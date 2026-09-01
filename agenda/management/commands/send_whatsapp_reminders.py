from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from agenda.integrations.whatsapp import WhatsAppProviderError, send_appointment_reminder
from agenda.models import Appointment, AppointmentReminder


class Command(BaseCommand):
	help = 'Envia lembretes de agendamento pelo WhatsApp.'

	def add_arguments(self, parser):
		parser.add_argument('--batch-size', type=int, default=50)
		parser.add_argument('--dry-run', action='store_true')

	def handle(self, *args, **options):
		now = timezone.now()
		batch_size = max(1, options['batch_size'])
		self._release_stale_claims(now)
		counters = {'sent': 0, 'skipped': 0, 'failed': 0, 'retried': 0}
		reminders = AppointmentReminder.objects.select_related(
			'appointment__business__whatsapp_integration',
			'appointment__service',
		).filter(
			status=AppointmentReminder.Status.PENDING,
		).filter(
			Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now),
		).order_by('created_at')[:batch_size]

		for reminder in reminders:
			appointment = reminder.appointment
			reminder_at = appointment.start_datetime - timedelta(
				minutes=appointment.business.whatsapp_reminder_lead_time_minutes,
			)
			if appointment.status != Appointment.Status.CONFIRMED:
				self._cancel(reminder.pk, 'Agendamento não está confirmado.', now)
				counters['skipped'] += 1
				continue
			if not appointment.business.whatsapp_reminders_enabled:
				self._cancel(reminder.pk, 'Lembretes automáticos estão desativados.', now)
				counters['skipped'] += 1
				continue
			if not appointment.whatsapp_reminder_opt_in:
				self._cancel(reminder.pk, 'Cliente não autorizou o lembrete.', now)
				counters['skipped'] += 1
				continue
			if now < reminder_at:
				counters['skipped'] += 1
				continue
			if now >= appointment.start_datetime:
				self._cancel(reminder.pk, 'O horário do agendamento já começou.', now)
				counters['skipped'] += 1
				continue
			if options['dry_run']:
				counters['would_send'] = counters.get('would_send', 0) + 1
				continue
			if not self._claim(reminder.pk, now):
				continue
			current_reminder = AppointmentReminder.objects.select_related(
				'appointment__business__whatsapp_integration',
				'appointment__service',
			).get(pk=reminder.pk)
			current_appointment = current_reminder.appointment
			if (
				current_appointment.status != Appointment.Status.CONFIRMED
				or not current_appointment.business.whatsapp_reminders_enabled
				or not current_appointment.whatsapp_reminder_opt_in
				or now >= current_appointment.start_datetime
			):
				self._cancel(reminder.pk, 'O agendamento não está mais elegível para lembrete.', now)
				counters['skipped'] += 1
				continue
			try:
				message_id = send_appointment_reminder(
					current_reminder,
				)
			except WhatsAppProviderError as exc:
				self._record_failure(reminder.pk, str(exc), exc.retryable, now)
				counters['retried' if exc.retryable else 'failed'] += 1
			else:
				AppointmentReminder.objects.filter(pk=reminder.pk).update(
					status=AppointmentReminder.Status.SENT,
					provider_message_id=message_id,
					sent_at=now,
					claimed_at=None,
					updated_at=now,
				)
				counters['sent'] += 1

		self.stdout.write(
			f"Enviados: {counters['sent']} | Ignorados: {counters['skipped']} | "
			f"Repetir: {counters['retried']} | Falhas: {counters['failed']}"
			+ (f" | Seriam enviados: {counters.get('would_send', 0)} (dry-run)" if options['dry_run'] else '')
		)

	@staticmethod
	def _release_stale_claims(now):
		cutoff = now - timedelta(minutes=10)
		AppointmentReminder.objects.filter(
			status=AppointmentReminder.Status.PROCESSING,
			claimed_at__lt=cutoff,
		).update(
			status=AppointmentReminder.Status.FAILED,
			claimed_at=None,
			last_error='Resultado do envio desconhecido; revisar antes de reenviar.',
			updated_at=now,
		)

	@staticmethod
	def _claim(reminder_id, now):
		return AppointmentReminder.objects.filter(
			pk=reminder_id,
			status=AppointmentReminder.Status.PENDING,
		).update(status=AppointmentReminder.Status.PROCESSING, claimed_at=now, updated_at=now) == 1

	@staticmethod
	def _cancel(reminder_id, reason, now):
		AppointmentReminder.objects.filter(pk=reminder_id).update(
			status=AppointmentReminder.Status.CANCELLED,
			claimed_at=None,
			last_error=reason,
			updated_at=now,
		)

	@staticmethod
	def _record_failure(reminder_id, message, retryable, now):
		reminder = AppointmentReminder.objects.get(pk=reminder_id)
		attempt_count = reminder.attempt_count + 1
		max_attempts = 3
		if retryable and attempt_count < max_attempts:
			status = AppointmentReminder.Status.PENDING
			next_attempt_at = now + timedelta(minutes=2 ** attempt_count)
		else:
			status = AppointmentReminder.Status.FAILED
			next_attempt_at = None
		AppointmentReminder.objects.filter(pk=reminder_id).update(
			status=status,
			attempt_count=attempt_count,
			next_attempt_at=next_attempt_at,
			claimed_at=None,
			last_error=message[:255],
			updated_at=now,
		)