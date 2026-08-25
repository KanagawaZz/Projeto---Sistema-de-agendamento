from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Count, Q
from datetime import date, datetime, timedelta

from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import AdminAppointmentForm, AppointmentForm, BusinessForm, BusinessPageForm
from .forms import ServiceForm
from .forms import WorkingDayForm, WorkingHoursFormSet
from .models import Appointment, Business, BusinessNotification, BusinessPage, Service, WorkingDay
from .services import AppointmentUnavailableError, build_whatsapp_link, create_business_notification, create_confirmed_appointment, get_available_start_times


def signup(request):
	if request.method == 'POST':
		form = UserCreationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			return redirect('business_form')
	else:
		form = UserCreationForm()

	return render(request, 'agenda/signup.html', {'form': form})


@login_required
def business_form(request):
	business = Business.objects.filter(owner=request.user).first()
	if request.method == 'POST':
		form = BusinessForm(request.POST, instance=business)
		if form.is_valid():
			business = form.save(commit=False)
			business.owner = request.user
			business.save()
			return redirect('dashboard')
	else:
		form = BusinessForm(instance=business)

	return render(request, 'agenda/business_form.html', {'form': form, 'business': business})


@login_required
def business_page_form(request):
	business = Business.objects.filter(owner=request.user).first()
	if business is None:
		return redirect('business_form')
	page, _ = BusinessPage.objects.get_or_create(business=business)
	if request.method == 'POST':
		form = BusinessPageForm(request.POST, instance=page)
		if form.is_valid():
			form.save()
			return redirect('business_page_form')
	else:
		form = BusinessPageForm(instance=page)
	return render(request, 'agenda/business_page_form.html', {'business': business, 'form': form, 'page': page})


@login_required
def dashboard(request):
	business = Business.objects.filter(owner=request.user).first()
	if business is None:
		return redirect('business_form')
	notifications = business.notifications.all()[:5]
	completed_filter = Q(appointments__status=Appointment.Status.COMPLETED)
	top_customers = business.customers.filter(
		completed_filter,
	).annotate(
		completed_total=Count('appointments', filter=completed_filter),
	).order_by('-completed_total', 'name')[:10]
	top_services = business.services.filter(
		appointments__status=Appointment.Status.COMPLETED,
	).annotate(
		completed_total=Count(
			'appointments',
			filter=Q(appointments__status=Appointment.Status.COMPLETED),
		),
	).order_by('-completed_total', 'name')[:10]
	return render(
		request,
		'agenda/dashboard.html',
		{
			'business': business,
			'notifications': notifications,
			'top_customers': top_customers,
			'top_services': top_services,
		},
	)


@login_required
def service_list(request):
	business = Business.objects.filter(owner=request.user).first()
	if business is None:
		return redirect('business_form')
	services = business.services.all()
	return render(request, 'agenda/service_list.html', {'business': business, 'services': services})


@login_required
def service_form(request, service_id=None):
	business = Business.objects.filter(owner=request.user).first()
	if business is None:
		return redirect('business_form')
	service = None
	if service_id is not None:
		service = get_object_or_404(Service, pk=service_id, business=business)

	if request.method == 'POST':
		form = ServiceForm(request.POST, instance=service)
		if form.is_valid():
			service = form.save(commit=False)
			service.business = business
			service.save()
			return redirect('service_list')
	else:
		form = ServiceForm(instance=service)

	return render(request, 'agenda/service_form.html', {'form': form, 'service': service})


@login_required
def service_toggle(request, service_id):
	if request.method != 'POST':
		return redirect('service_list')
	business = Business.objects.filter(owner=request.user).first()
	if business is None:
		return redirect('business_form')
	service = get_object_or_404(Service, pk=service_id, business=business)
	service.is_active = not service.is_active
	service.save(update_fields=['is_active'])
	return redirect('service_list')


DAY_NAMES = (
	'Segunda-feira',
	'Terça-feira',
	'Quarta-feira',
	'Quinta-feira',
	'Sexta-feira',
	'Sábado',
	'Domingo',
)


@login_required
def working_hours(request):
	business = Business.objects.filter(owner=request.user).first()
	if business is None:
		return redirect('business_form')

	days = [
		WorkingDay.objects.get_or_create(business=business, day_of_week=day)[0]
		for day in range(7)
	]
	forms_data = []
	for index, day in enumerate(days):
		day_form = WorkingDayForm(
			request.POST or None,
			instance=day,
			prefix=f'day-{index}',
		)
		hours_formset = WorkingHoursFormSet(
			request.POST or None,
			instance=day,
			prefix=f'hours-{index}',
		)
		forms_data.append((day, DAY_NAMES[index], day_form, hours_formset))

	if request.method == 'POST' and all(
		day_form.is_valid() and hours_formset.is_valid()
		for _, _, day_form, hours_formset in forms_data
	):
		with transaction.atomic():
			for day, _, day_form, hours_formset in forms_data:
				day = day_form.save(commit=False)
				day.business = business
				day.save()
				hours_formset.instance = day
				hours_formset.save()
		return redirect('working_hours')

	return render(
		request,
		'agenda/working_hours.html',
		{'business': business, 'forms_data': forms_data},
	)


def public_booking(request, slug, service_id=None):
	business = get_object_or_404(Business, slug=slug)
	services = business.services.filter(is_active=True)
	if service_id is None:
		page = BusinessPage.objects.filter(business=business, is_published=True).first()
		if page is None:
			page = BusinessPage(business=business)
		return render(request, 'agenda/public_services.html', {'business': business, 'page': page, 'services': services})

	service = get_object_or_404(services, pk=service_id)
	selected_date = request.POST.get('date') or request.GET.get('date')
	available_times = []
	if selected_date:
		try:
			target_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
		except ValueError:
			target_date = None
			selected_date = ''
		if target_date:
			available_times = get_available_start_times(business, service, target_date)

	if request.method == 'POST':
		form = AppointmentForm(request.POST)
		start_value = request.POST.get('start_datetime', '')
		try:
			start_datetime = timezone.make_aware(datetime.fromisoformat(start_value))
		except ValueError:
			start_datetime = None
		if not start_datetime or start_datetime not in available_times:
			form.add_error(None, 'O horário selecionado não está mais disponível.')
		elif form.is_valid():
			try:
				appointment = create_confirmed_appointment(
					business,
					service,
					start_datetime,
					form.cleaned_data['client_name'],
					form.cleaned_data['client_phone'],
				)
			except AppointmentUnavailableError:
				form.add_error(None, 'O horário selecionado não está mais disponível.')
			else:
				whatsapp_link = ''
				if appointment.business.whatsapp_phone:
					whatsapp_link = build_whatsapp_link(
						appointment.business.whatsapp_phone,
						f'Olá! Acabei de agendar {appointment.service.name} para {timezone.localtime(appointment.start_datetime):%d/%m às %H:%M}.',
					)
				return render(request, 'agenda/booking_confirmation.html', {'appointment': appointment, 'whatsapp_link': whatsapp_link})
	else:
		form = AppointmentForm()

	return render(
		request,
		'agenda/booking.html',
		{
			'business': business,
			'service': service,
			'form': form,
			'selected_date': selected_date or '',
			'available_times': available_times,
		},
	)


def cancel_appointment(request, token):
	appointment = get_object_or_404(Appointment, cancellation_token=token)
	if request.method == 'POST':
		if appointment.start_datetime <= timezone.now():
			return render(request, 'agenda/booking_cancel.html', {'appointment': appointment, 'error': 'O agendamento já começou e não pode ser cancelado.'})
		appointment.status = Appointment.Status.CANCELLED
		appointment.save(update_fields=['status', 'updated_at'])
		create_business_notification(
			appointment.business,
			appointment,
			BusinessNotification.EventType.APPOINTMENT_CANCELLED,
			'Agendamento cancelado',
			f'{appointment.client_name} cancelou {appointment.service.name}.',
		)
	return render(request, 'agenda/booking_cancel.html', {'appointment': appointment})


@login_required
def appointment_list(request):
	business = Business.objects.filter(owner=request.user).first()
	if business is None:
		return redirect('business_form')
	selected_date_value = request.GET.get('date', '')
	try:
		selected_date = date.fromisoformat(selected_date_value)
	except ValueError:
		selected_date = timezone.localdate()
	selected_date_value = selected_date.isoformat()
	appointments = business.appointments.select_related('service', 'customer').filter(
		start_datetime__date=selected_date,
	).order_by('start_datetime')
	for appointment in appointments:
		appointment.customer_whatsapp_link = build_whatsapp_link(
			appointment.client_phone,
			f'Olá, {appointment.client_name}! Aqui é da {business.name}. '
			f'Estou entrando em contato sobre seu agendamento de {appointment.service.name} '
			f'para {timezone.localtime(appointment.start_datetime):%d/%m às %H:%M}.',
		)
	return render(
		request,
		'agenda/appointment_list.html',
		{
			'business': business,
			'appointments': appointments,
			'now': timezone.now(),
			'selected_date': selected_date,
			'selected_date_value': selected_date_value,
			'previous_date': selected_date - timedelta(days=1),
			'next_date': selected_date + timedelta(days=1),
		},
	)


@login_required
def appointment_create(request):
	business = Business.objects.filter(owner=request.user).first()
	if business is None:
		return redirect('business_form')

	if request.method == 'POST':
		form = AdminAppointmentForm(request.POST, business=business)
	else:
		form = AdminAppointmentForm(
			business=business,
			initial={
				'service': request.GET.get('service'),
				'date': request.GET.get('date'),
			},
		)

	if request.method == 'POST' and form.is_valid():
		try:
			create_confirmed_appointment(
				business,
				form.cleaned_data['service'],
				form.cleaned_data['start_datetime'],
				form.cleaned_data['client_name'],
				form.cleaned_data['client_phone'],
			)
		except AppointmentUnavailableError:
			form.add_error(None, 'O horário selecionado não está mais disponível.')
		else:
			return redirect('appointment_list')

	return render(
		request,
		'agenda/appointment_form.html',
		{
			'business': business,
			'form': form,
			'selected_service': request.POST.get('service') or request.GET.get('service', ''),
			'selected_date': request.POST.get('date') or request.GET.get('date', ''),
		},
	)


@login_required
def appointment_cancel(request, appointment_id):
	business = Business.objects.filter(owner=request.user).first()
	if business is None:
		return redirect('business_form')
	appointment = get_object_or_404(Appointment, pk=appointment_id, business=business)
	if request.method == 'POST' and appointment.status == Appointment.Status.CONFIRMED:
		if appointment.start_datetime > timezone.now():
			appointment.status = Appointment.Status.CANCELLED
			appointment.save(update_fields=['status', 'updated_at'])
			create_business_notification(
				business,
				appointment,
				BusinessNotification.EventType.APPOINTMENT_CANCELLED,
				'Agendamento cancelado',
				f'{appointment.client_name} cancelou {appointment.service.name}.',
			)
	return redirect('appointment_list')


@login_required
def appointment_update_status(request, appointment_id, status):
	business = Business.objects.filter(owner=request.user).first()
	if business is None:
		return redirect('business_form')
	appointment = get_object_or_404(Appointment, pk=appointment_id, business=business)
	valid_statuses = {Appointment.Status.COMPLETED, Appointment.Status.NO_SHOW}
	if (
		request.method == 'POST'
		and status in valid_statuses
		and appointment.status == Appointment.Status.CONFIRMED
		and appointment.start_datetime <= timezone.now()
	):
		appointment.status = status
		appointment.save(update_fields=['status', 'updated_at'])
	return redirect(
		f'{reverse("appointment_list")}?date={appointment.start_datetime.date().isoformat()}'
	)
