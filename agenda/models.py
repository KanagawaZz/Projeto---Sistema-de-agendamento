from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify
import uuid


User = get_user_model()


class Business(models.Model):
	owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business')
	name = models.CharField(max_length=150)
	slug = models.SlugField(max_length=170, unique=True, blank=True)
	description = models.TextField(blank=True)
	whatsapp_phone = models.CharField(max_length=30, blank=True)
	slot_granularity_minutes = models.PositiveIntegerField(default=15, validators=[MinValueValidator(1)])

	def save(self, *args, **kwargs):
		if not self.slug:
			base_slug = slugify(self.name)
			candidate = base_slug
			counter = 2
			while type(self).objects.filter(slug=candidate).exclude(pk=self.pk).exists():
				candidate = f'{base_slug}-{counter}'
				counter += 1
			self.slug = candidate
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class BusinessPage(models.Model):
	class Theme(models.TextChoices):
		OCEAN = 'ocean', 'Azul oceano'
		FOREST = 'forest', 'Verde floresta'
		SUNSET = 'sunset', 'Pôr do sol'

	business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='page')
	public_title = models.CharField(max_length=120, blank=True)
	public_description = models.TextField(max_length=500, blank=True)
	cta_label = models.CharField(max_length=40, default='Agendar agora')
	theme = models.CharField(max_length=20, choices=Theme.choices, default=Theme.OCEAN)
	is_published = models.BooleanField(default=True)
	updated_at = models.DateTimeField(auto_now=True)

	@property
	def display_title(self):
		return self.public_title or self.business.name

	@property
	def display_description(self):
		return self.public_description or self.business.description

	def __str__(self):
		return f'Página de {self.business.name}'


class Service(models.Model):
	business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='services')
	name = models.CharField(max_length=150)
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
	duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
	buffer_minutes = models.PositiveIntegerField(default=0)
	is_active = models.BooleanField(default=True)

	@property
	def operational_minutes(self):
		return self.duration_minutes + self.buffer_minutes

	def __str__(self):
		return self.name


class Customer(models.Model):
	business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='customers')
	name = models.CharField(max_length=150)
	phone = models.CharField(max_length=30)
	normalized_phone = models.CharField(max_length=30)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=('business', 'normalized_phone'),
				name='unique_customer_phone_per_business',
			),
		]

	@property
	def completed_count(self):
		return self.appointments.filter(status=Appointment.Status.COMPLETED).count()

	@property
	def last_completed_service(self):
		last_appointment = self.appointments.filter(
			status=Appointment.Status.COMPLETED,
		).select_related('service').order_by('-start_datetime').first()
		return last_appointment.service.name if last_appointment else ''

	def __str__(self):
		return f'{self.name} - {self.phone}'


class Appointment(models.Model):
	class Status(models.TextChoices):
		CONFIRMED = 'confirmed', 'Confirmado'
		CANCELLED = 'cancelled', 'Cancelado'
		COMPLETED = 'completed', 'Concluído'
		NO_SHOW = 'no_show', 'Não compareceu'

	business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='appointments')
	service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='appointments')
	customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
	start_datetime = models.DateTimeField()
	client_name = models.CharField(max_length=150)
	client_phone = models.CharField(max_length=30)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.CONFIRMED)
	cancellation_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def clean(self):
		if self.service_id and self.business_id and self.service.business_id != self.business_id:
			raise ValidationError('O serviço deve pertencer ao negócio do agendamento.')
		if self.customer_id and self.business_id and self.customer.business_id != self.business_id:
			raise ValidationError('O cliente deve pertencer ao negócio do agendamento.')
		if self.start_datetime and not timezone.is_aware(self.start_datetime):
			raise ValidationError({'start_datetime': 'O horário do agendamento deve conter timezone.'})

	def __str__(self):
		return f'{self.client_name} - {self.start_datetime}'


class BusinessNotification(models.Model):
	class EventType(models.TextChoices):
		APPOINTMENT_CREATED = 'appointment_created', 'Novo agendamento'
		APPOINTMENT_CANCELLED = 'appointment_cancelled', 'Agendamento cancelado'

	business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='notifications')
	appointment = models.ForeignKey(
		Appointment,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='notifications',
	)
	event_type = models.CharField(max_length=40, choices=EventType.choices)
	title = models.CharField(max_length=120)
	message = models.CharField(max_length=255)
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ('-created_at',)

	def __str__(self):
		return self.title


class WorkingDay(models.Model):
	business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='working_days')
	day_of_week = models.PositiveSmallIntegerField()
	is_closed = models.BooleanField(default=False)

	class Meta:
		constraints = [
			models.UniqueConstraint(
				fields=('business', 'day_of_week'),
				name='unique_working_day_per_business',
			),
		]

	def clean(self):
		if not 0 <= self.day_of_week <= 6:
			raise ValidationError({'day_of_week': 'O dia da semana deve estar entre 0 e 6.'})
		if self.is_closed and self.pk and self.hours.exists():
			raise ValidationError('Um dia fechado não pode ter intervalos de horário.')

	def __str__(self):
		return f'{self.business.name} - {self.day_of_week}'


class WorkingHours(models.Model):
	working_day = models.ForeignKey(WorkingDay, on_delete=models.CASCADE, related_name='hours')
	start_time = models.TimeField()
	end_time = models.TimeField()

	def clean(self):
		if self.start_time >= self.end_time:
			raise ValidationError('O início deve ser anterior ao fim do intervalo.')
		if self.working_day_id and self.working_day.is_closed:
			raise ValidationError('Um dia fechado não pode ter intervalos de horário.')
		if self.working_day_id and self.working_day.hours.filter(
			start_time__lt=self.end_time,
			end_time__gt=self.start_time,
		).exclude(pk=self.pk).exists():
			raise ValidationError('Os intervalos de horário não podem se sobrepor.')

	def __str__(self):
		return f'{self.start_time} - {self.end_time}'
