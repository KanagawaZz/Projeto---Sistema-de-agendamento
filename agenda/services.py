from datetime import date, datetime, timedelta
from urllib.parse import quote

from django.db import OperationalError, transaction
from django.utils import timezone

from .models import Appointment, AppointmentReminder, Business, BusinessNotification, Customer, Service


class AppointmentUnavailableError(Exception):
	pass


def normalize_phone(phone: str) -> str:
	return ''.join(character for character in phone if character.isdigit())


def build_whatsapp_link(phone: str, message: str) -> str:
	normalized_phone = normalize_phone(phone)
	if len(normalized_phone) in (10, 11):
		normalized_phone = f'55{normalized_phone}'
	return f'https://wa.me/{normalized_phone}?text={quote(message)}'


def create_business_notification(business, appointment, event_type, title, message):
	return BusinessNotification.objects.create(
		business=business,
		appointment=appointment,
		event_type=event_type,
		title=title,
		message=message,
	)


def get_available_start_times(
	business: Business,
	service: Service,
	target_date: date,
	*,
	now: datetime | None = None,
) -> list[datetime]:
	if service.business_id != business.id or not service.is_active:
		return []

	local_now = timezone.localtime(now or timezone.now())
	if target_date < local_now.date():
		return []

	day = business.working_days.filter(
		day_of_week=target_date.weekday(),
	).first()
	if not day or day.is_closed:
		return []

	available_times = []
	operational_duration = timedelta(minutes=service.operational_minutes)
	step = timedelta(minutes=business.slot_granularity_minutes)
	confirmed_appointments = business.appointments.filter(
		status=Appointment.Status.CONFIRMED,
		start_datetime__date=target_date,
	).select_related('service')

	for interval in day.hours.order_by('start_time'):
		interval_start = datetime.combine(target_date, interval.start_time)
		interval_end = datetime.combine(target_date, interval.end_time)
		candidate = interval_start

		while candidate + operational_duration <= interval_end:
			candidate_aware = timezone.make_aware(candidate)
			candidate_end = candidate_aware + operational_duration
			is_occupied = any(
				appointment.start_datetime < candidate_end
				and candidate_aware < appointment.start_datetime + timedelta(
					minutes=appointment.service.operational_minutes,
				)
				for appointment in confirmed_appointments
			)
			if (
				(target_date != local_now.date() or candidate_aware > local_now)
				and not is_occupied
			):
				available_times.append(candidate_aware)
			candidate += step

	return available_times


def create_confirmed_appointment(
	business: Business,
	service: Service,
	start_datetime: datetime,
	client_name: str,
	client_phone: str,
	*,
	whatsapp_reminder_opt_in: bool = False,
	whatsapp_opt_in_source: str = '',
) -> Appointment:
	try:
		with transaction.atomic():
			locked_business = Business.objects.select_for_update().get(pk=business.pk)
			locked_service = Service.objects.get(pk=service.pk)
			if locked_service.business_id != locked_business.id or not locked_service.is_active:
				raise AppointmentUnavailableError
			if not timezone.is_aware(start_datetime):
				raise AppointmentUnavailableError

			available_times = get_available_start_times(
				locked_business,
				locked_service,
				start_datetime.astimezone(timezone.get_current_timezone()).date(),
			)
			if start_datetime not in available_times:
				raise AppointmentUnavailableError

			normalized_phone = normalize_phone(client_phone)
			customer, created = Customer.objects.get_or_create(
				business=locked_business,
				normalized_phone=normalized_phone,
				defaults={'name': client_name, 'phone': client_phone},
			)
			if not created and (customer.name != client_name or customer.phone != client_phone):
				customer.name = client_name
				customer.phone = client_phone
				customer.save(update_fields=['name', 'phone', 'updated_at'])

			appointment = Appointment(
				business=locked_business,
				service=locked_service,
				customer=customer,
				start_datetime=start_datetime,
				client_name=client_name,
				client_phone=client_phone,
				whatsapp_reminder_opt_in=whatsapp_reminder_opt_in,
				whatsapp_opt_in_at=timezone.now() if whatsapp_reminder_opt_in else None,
				whatsapp_opt_in_source=whatsapp_opt_in_source,
			)
			appointment.full_clean()
			appointment.save()
			if locked_business.whatsapp_reminders_enabled and whatsapp_reminder_opt_in:
				AppointmentReminder.objects.create(appointment=appointment)
			local_start = timezone.localtime(appointment.start_datetime)
			create_business_notification(
				locked_business,
				appointment,
				BusinessNotification.EventType.APPOINTMENT_CREATED,
				'Novo agendamento',
				f'{appointment.client_name} marcou {appointment.service.name} para {local_start:%d/%m às %H:%M}.',
			)
			return appointment
	except OperationalError as error:
		if 'locked' in str(error).lower():
			raise AppointmentUnavailableError from error
		raise