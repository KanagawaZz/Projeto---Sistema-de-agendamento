import datetime
import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .services import AppointmentUnavailableError, build_whatsapp_link, create_confirmed_appointment, get_available_start_times, normalize_phone
from .models import Appointment, AppointmentReminder, Business, BusinessNotification, BusinessPage, Customer, Service, WhatsAppIntegration, WorkingDay, WorkingHours

User = get_user_model()


class AuthenticationTests(TestCase):
	def test_build_whatsapp_link_normalizes_brazilian_phone_and_encodes_message(self):
		link = build_whatsapp_link('(11) 99999-9999', 'Olá, horário confirmado!')

		self.assertEqual(
			link,
			'https://wa.me/5511999999999?text=Ol%C3%A1%2C%20hor%C3%A1rio%20confirmado%21',
		)

	def test_signup_creates_and_logs_in_user(self):
		response = self.client.post(
			'/signup/',
			{
				'username': 'joao',
				'password1': 'Senha-forte-123',
				'password2': 'Senha-forte-123',
			},
		)

		self.assertRedirects(response, '/business/')
		self.assertTrue(response.wsgi_request.user.is_authenticated)
		self.assertTrue(User.objects.filter(username='joao').exists())

	def test_invalid_signup_does_not_create_user(self):
		response = self.client.post(
			'/signup/',
			{
				'username': 'joao',
				'password1': 'Senha-forte-123',
				'password2': 'outra-senha',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertFalse(User.objects.filter(username='joao').exists())

	def test_anonymous_user_is_redirected_from_dashboard(self):
		response = self.client.get('/')

		self.assertRedirects(response, '/login/?next=/')

	def test_login_and_logout(self):
		user = User.objects.create_user(username='joao', password='Senha-forte-123')
		Business.objects.create(owner=user, name='Barbearia do João')

		login_response = self.client.post(
			'/login/',
			{'username': 'joao', 'password': 'Senha-forte-123'},
		)
		self.assertRedirects(login_response, '/')

		logout_response = self.client.post('/logout/')
		self.assertRedirects(logout_response, '/login/')

	def test_login_without_business_redirects_to_business_form(self):
		User.objects.create_user(username='joao', password='Senha-forte-123')

		response = self.client.post(
			'/login/',
			{'username': 'joao', 'password': 'Senha-forte-123'},
		)

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], '/')
		dashboard_response = self.client.get('/')
		self.assertRedirects(dashboard_response, '/business/')

	def test_dashboard_displays_only_current_business_notifications(self):
		user = User.objects.create_user(username='owner-notification', password='Senha-forte-123')
		business = Business.objects.create(owner=user, name='Meu negócio')
		other_user = User.objects.create_user(username='other-notification', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Outro negócio')
		BusinessNotification.objects.create(
			business=business,
			event_type=BusinessNotification.EventType.APPOINTMENT_CREATED,
			title='Novo agendamento',
			message='Cliente do meu negócio marcou um horário.',
		)
		BusinessNotification.objects.create(
			business=other_business,
			event_type=BusinessNotification.EventType.APPOINTMENT_CREATED,
			title='Novo agendamento',
			message='Mensagem de outro negócio.',
		)
		self.client.force_login(user)

		response = self.client.get('/')

		self.assertContains(response, 'Cliente do meu negócio')
		self.assertNotContains(response, 'Mensagem de outro negócio')

	def test_dashboard_displays_top_customers_and_services_from_completed_appointments(self):
		user = User.objects.create_user(username='owner-insights', password='Senha-forte-123')
		business = Business.objects.create(owner=user, name='Meu negócio')
		service = Service.objects.create(
			business=business,
			name='Corte clássico',
			price='45.00',
			duration_minutes=30,
		)
		customer = Customer.objects.create(
			business=business,
			name='Cliente recorrente',
			phone='11999999999',
			normalized_phone='11999999999',
		)
		for day in (1, 2):
			appointment = Appointment.objects.create(
				business=business,
				service=service,
				customer=customer,
				start_datetime=timezone.make_aware(datetime.datetime(2026, 8, day, 10, 0)),
				client_name='Cliente recorrente',
				client_phone='11999999999',
				status=Appointment.Status.COMPLETED,
			)
		self.client.force_login(user)

		response = self.client.get('/')

		self.assertContains(response, 'Clientes mais frequentes')
		self.assertContains(response, 'Cliente recorrente')
		self.assertContains(response, 'Serviços mais realizados')
		self.assertContains(response, 'Corte clássico')
		self.assertContains(response, '2')

	def test_business_form_creates_business_with_unique_slug(self):
		user = User.objects.create_user(username='joao', password='Senha-forte-123')
		self.client.force_login(user)

		response = self.client.post(
			'/business/',
			{'name': 'Barbearia do João', 'description': 'Cortes masculinos'},
		)

		self.assertRedirects(response, '/')
		business = Business.objects.get(owner=user)
		self.assertEqual(business.slug, 'barbearia-do-joao')

		other_user = User.objects.create_user(username='maria', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Barbearia do João')
		self.assertEqual(other_business.slug, 'barbearia-do-joao-2')

	def test_business_form_edits_existing_business(self):
		user = User.objects.create_user(username='joao', password='Senha-forte-123')
		Business.objects.create(owner=user, name='Barbearia do João')
		self.client.force_login(user)

		response = self.client.post(
			'/business/',
			{'name': 'Barbearia Central', 'description': 'Novo texto'},
		)

		self.assertRedirects(response, '/')
		business = Business.objects.get(owner=user)
		self.assertEqual(business.name, 'Barbearia Central')
		self.assertEqual(business.description, 'Novo texto')
		self.assertEqual(business.slug, 'barbearia-do-joao')

	def test_business_form_saves_custom_whatsapp_reminder_message(self):
		user = User.objects.create_user(username='message-owner', password='Senha-forte-123')
		Business.objects.create(owner=user, name='Barbearia Central')
		self.client.force_login(user)

		response = self.client.post(
			'/business/',
			{
				'name': 'Barbearia Central',
				'description': '',
				'whatsapp_phone': '',
				'whatsapp_reminders_enabled': '',
				'whatsapp_reminder_lead_time_minutes': '30',
				'whatsapp_reminder_message': 'Oi {cliente}, seu {servico} será em {data} às {hora}.',
			},
		)

		self.assertRedirects(response, '/')
		business = Business.objects.get(owner=user)
		self.assertEqual(business.whatsapp_reminder_lead_time_minutes, 30)
		self.assertEqual(business.whatsapp_reminder_message, 'Oi {cliente}, seu {servico} será em {data} às {hora}.')

	def test_business_form_rejects_unknown_whatsapp_placeholder(self):
		user = User.objects.create_user(username='invalid-message-owner', password='Senha-forte-123')
		Business.objects.create(owner=user, name='Barbearia Central')
		self.client.force_login(user)

		response = self.client.post(
			'/business/',
			{
				'name': 'Barbearia Central',
				'whatsapp_reminder_message': 'Olá {cliente}, código {codigo}.',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Use somente: {cliente}, {servico}, {data}, {hora} e {negocio}.')

	def test_whatsapp_settings_save_connection_metadata_without_token(self):
		user = User.objects.create_user(username='whatsapp-owner', password='Senha-forte-123')
		business = Business.objects.create(owner=user, name='Barbearia Central')
		self.client.force_login(user)

		response = self.client.post(
			'/business/whatsapp/',
			{
				'instance_name': 'agenda-facil-central',
			},
		)

		self.assertRedirects(response, '/business/whatsapp/')
		integration = WhatsAppIntegration.objects.get(business=business)
		self.assertEqual(integration.instance_name, 'agenda-facil-central')
		self.assertEqual(integration.api_key_env_var, 'EVOLUTION_API_KEY')
		self.assertEqual(integration.status, WhatsAppIntegration.Status.DISCONNECTED)

	def test_whatsapp_validation_marks_connection_as_connected(self):
		user = User.objects.create_user(username='whatsapp-validation', password='Senha-forte-123')
		business = Business.objects.create(owner=user, name='Barbearia Central')
		integration = WhatsAppIntegration.objects.create(
			business=business,
			instance_name='agenda-facil-central',
			api_key_env_var='EVOLUTION_API_KEY',
		)
		self.client.force_login(user)
		response_mock = MagicMock()
		response_mock.__enter__.return_value.read.return_value = b'{"instance": {"state": "open"}}'

		with patch.dict('os.environ', {integration.api_key_env_var: 'token-value'}), patch(
			'agenda.integrations.whatsapp.request.urlopen', return_value=response_mock,
		) as urlopen:
			response = self.client.post('/business/whatsapp/validate/')

		self.assertRedirects(response, '/business/whatsapp/')
		integration.refresh_from_db()
		self.assertEqual(integration.status, WhatsAppIntegration.Status.CONNECTED)
		self.assertEqual(integration.last_error, '')
		urlopen.assert_called_once()
		api_request = urlopen.call_args.args[0]
		self.assertEqual(api_request.method, 'GET')
		self.assertEqual(api_request.full_url, 'http://localhost:8080/instance/connectionState/agenda-facil-central')
		self.assertEqual(api_request.get_header('Apikey'), 'token-value')

	def test_whatsapp_validation_records_missing_token_without_external_call(self):
		user = User.objects.create_user(username='whatsapp-missing-token', password='Senha-forte-123')
		business = Business.objects.create(owner=user, name='Barbearia Central')
		integration = WhatsAppIntegration.objects.create(
			business=business,
			instance_name='agenda-facil-central',
			api_key_env_var='EVOLUTION_API_KEY',
		)
		self.client.force_login(user)

		with patch.dict('os.environ', {}, clear=True), patch('agenda.integrations.whatsapp.request.urlopen') as urlopen:
			response = self.client.post('/business/whatsapp/validate/')

		self.assertRedirects(response, '/business/whatsapp/')
		integration.refresh_from_db()
		self.assertEqual(integration.status, WhatsAppIntegration.Status.ERROR)
		self.assertIn('api key', integration.last_error.lower())
		urlopen.assert_not_called()

	def test_whatsapp_connect_displays_qr_code_without_persisting_it(self):
		user = User.objects.create_user(username='whatsapp-connect', password='Senha-forte-123')
		business = Business.objects.create(owner=user, name='Barbearia Central')
		integration = WhatsAppIntegration.objects.create(
			business=business,
			instance_name='agenda-facil',
			api_key_env_var='EVOLUTION_API_KEY',
		)
		self.client.force_login(user)
		response_mock = MagicMock()
		response_mock.__enter__.return_value.read.return_value = b'{"base64":"data:image/png;base64,qr-code","pairingCode":null}'

		with patch.dict('os.environ', {'EVOLUTION_API_KEY': 'token-value'}), patch(
			'agenda.integrations.whatsapp.request.urlopen', return_value=response_mock,
		) as urlopen:
			response = self.client.post('/business/whatsapp/connect/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'data:image/png;base64,qr-code')
		integration.refresh_from_db()
		self.assertEqual(integration.status, WhatsAppIntegration.Status.DISCONNECTED)
		api_request = urlopen.call_args.args[0]
		self.assertEqual(api_request.full_url, 'http://localhost:8080/instance/connect/agenda-facil')
		self.assertEqual(api_request.get_header('Apikey'), 'token-value')

	def test_business_page_uses_business_data_as_fallback(self):
		user = User.objects.create_user(username='joao', password='Senha-forte-123')
		business = Business.objects.create(
			owner=user,
			name='Barbearia Central',
			description='Cortes e cuidados masculinos',
		)
		page = BusinessPage.objects.create(business=business)

		self.assertEqual(page.display_title, business.name)
		self.assertEqual(page.display_description, business.description)

	def test_business_page_keeps_controlled_customization(self):
		user = User.objects.create_user(username='maria', password='Senha-forte-123')
		business = Business.objects.create(owner=user, name='Studio Maria')
		page = BusinessPage.objects.create(
			business=business,
			public_title='Studio Maria Beauty',
			public_description='Atendimento com hora marcada.',
			cta_label='Escolher horário',
			theme=BusinessPage.Theme.FOREST,
			is_published=False,
		)

		page.refresh_from_db()
		self.assertEqual(page.display_title, 'Studio Maria Beauty')
		self.assertEqual(page.display_description, 'Atendimento com hora marcada.')
		self.assertEqual(page.cta_label, 'Escolher horário')
		self.assertEqual(page.theme, BusinessPage.Theme.FOREST)
		self.assertFalse(page.is_published)


class LandingPageTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='joao', password='Senha-forte-123')
		self.business = Business.objects.create(
			owner=self.user,
			name='Barbearia Central',
			description='Cortes com hora marcada.',
		)
		self.active_service = Service.objects.create(
			business=self.business,
			name='Corte clássico',
			price='45.00',
			duration_minutes=30,
		)
		self.inactive_service = Service.objects.create(
			business=self.business,
			name='Serviço pausado',
			price='30.00',
			duration_minutes=20,
			is_active=False,
		)

	def test_public_landing_falls_back_to_business_data(self):
		response = self.client.get(f'/book/{self.business.slug}/')

		self.assertContains(response, self.business.name)
		self.assertContains(response, self.business.description)
		self.assertContains(response, self.active_service.name)
		self.assertNotContains(response, self.inactive_service.name)
		self.assertContains(response, 'Agendar agora')

	def test_published_page_uses_custom_data(self):
		BusinessPage.objects.create(
			business=self.business,
			public_title='Central Barber Club',
			public_description='Seu novo visual começa aqui.',
			cta_label='Reservar horário',
		)

		response = self.client.get(f'/book/{self.business.slug}/')

		self.assertContains(response, 'Central Barber Club')
		self.assertContains(response, 'Seu novo visual começa aqui.')
		self.assertContains(response, 'Reservar horário')

	def test_published_page_applies_custom_brand_colors(self):
		BusinessPage.objects.create(
			business=self.business,
			public_title='Central Barber Club',
			primary_color='#123456',
			secondary_color='#abcdef',
			is_published=True,
		)

		response = self.client.get(f'/book/{self.business.slug}/')

		self.assertContains(response, '--brand-primary: #123456')
		self.assertContains(response, '--brand-secondary: #abcdef')

	def test_unpublished_page_falls_back_to_business_data(self):
		BusinessPage.objects.create(
			business=self.business,
			public_title='Página em revisão',
			is_published=False,
		)

		response = self.client.get(f'/book/{self.business.slug}/')

		self.assertContains(response, self.business.name)
		self.assertNotContains(response, 'Página em revisão')

	def test_owner_can_update_page_and_anonymous_user_is_redirected(self):
		anonymous_response = self.client.get('/business/page/')
		self.assertRedirects(anonymous_response, '/login/?next=/business/page/')

		self.client.force_login(self.user)
		response = self.client.post(
			'/business/page/',
			{
				'public_title': 'Central Barber Club',
				'public_description': 'Descrição atualizada.',
				'cta_label': 'Agendar visita',
				'theme': BusinessPage.Theme.FOREST,
				'is_published': 'on',
			},
		)

		self.assertRedirects(response, '/business/page/')
		page = BusinessPage.objects.get(business=self.business)
		self.assertEqual(page.public_title, 'Central Barber Club')
		self.assertEqual(page.theme, BusinessPage.Theme.FOREST)

	def test_page_settings_are_isolated_between_businesses(self):
		other_user = User.objects.create_user(username='maria-page', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Studio Maria')
		other_page = BusinessPage.objects.create(business=other_business, public_title='Página Maria')
		self.client.force_login(self.user)

		self.client.post(
			'/business/page/',
			{
				'public_title': 'Minha página',
				'public_description': '',
				'cta_label': 'Agendar agora',
				'theme': BusinessPage.Theme.OCEAN,
				'is_published': 'on',
			},
		)

		other_page.refresh_from_db()
		self.assertEqual(other_page.public_title, 'Página Maria')


class AdminAppointmentCreationTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='joao-admin', password='Senha-forte-123')
		self.business = Business.objects.create(owner=self.user, name='Barbearia Central')
		self.service = Service.objects.create(
			business=self.business,
			name='Corte clássico',
			price='45.00',
			duration_minutes=30,
		)
		self.booking_date = timezone.localdate() + datetime.timedelta(days=7)
		working_day = WorkingDay.objects.create(
			business=self.business,
			day_of_week=self.booking_date.weekday(),
		)
		WorkingHours.objects.create(working_day=working_day, start_time='09:00', end_time='12:00')

	def test_anonymous_user_is_redirected(self):
		response = self.client.get('/appointments/new/')

		self.assertRedirects(response, '/login/?next=/appointments/new/')

	def test_owner_can_create_manual_appointment(self):
		self.client.force_login(self.user)
		date_value = self.booking_date.isoformat()

		form_response = self.client.get(
			f'/appointments/new/?service={self.service.id}&date={date_value}',
		)
		self.assertContains(form_response, '09:00')

		response = self.client.post(
			'/appointments/new/',
			{
				'service': self.service.id,
				'date': date_value,
				'start_datetime': f'{date_value}T09:00',
				'client_name': 'Maria Silva',
				'client_phone': '11999999999',
			},
		)

		self.assertRedirects(response, '/appointments/')
		appointment = Appointment.objects.get()
		self.assertEqual(appointment.business, self.business)
		self.assertEqual(appointment.service, self.service)
		self.assertEqual(appointment.client_name, 'Maria Silva')

	def test_manual_flow_rejects_service_from_another_business(self):
		other_user = User.objects.create_user(username='maria-admin', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Studio Maria')
		other_service = Service.objects.create(
			business=other_business,
			name='Manicure',
			price='30.00',
			duration_minutes=30,
		)
		self.client.force_login(self.user)

		response = self.client.post(
			'/appointments/new/',
			{
				'service': other_service.id,
				'date': self.booking_date.isoformat(),
				'start_datetime': f'{self.booking_date.isoformat()}T09:00',
				'client_name': 'Maria Silva',
				'client_phone': '11999999999',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(Appointment.objects.count(), 0)

	def test_manual_flow_revalidates_occupied_time(self):
		Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.make_aware(datetime.datetime.combine(self.booking_date, datetime.time(9, 0))),
			client_name='Cliente existente',
			client_phone='11888888888',
		)
		self.client.force_login(self.user)

		response = self.client.post(
			'/appointments/new/',
			{
				'service': self.service.id,
				'date': self.booking_date.isoformat(),
				'start_datetime': f'{self.booking_date.isoformat()}T09:00',
				'client_name': 'Maria Silva',
				'client_phone': '11999999999',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'não está mais disponível')
		self.assertEqual(Appointment.objects.count(), 1)


class CustomerHistoryTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='joao-customer', password='Senha-forte-123')
		self.business = Business.objects.create(owner=self.user, name='Barbearia Central')
		self.service = Service.objects.create(
			business=self.business,
			name='Corte clássico',
			price='45.00',
			duration_minutes=30,
		)
		self.booking_date = timezone.localdate() + datetime.timedelta(days=7)
		working_day = WorkingDay.objects.create(
			business=self.business,
			day_of_week=self.booking_date.weekday(),
		)
		WorkingHours.objects.create(working_day=working_day, start_time='09:00', end_time='12:00')

	def test_normalize_phone_keeps_only_digits(self):
		self.assertEqual(normalize_phone('(11) 99999-9999'), '11999999999')

	def test_new_appointments_share_customer_by_normalized_phone(self):
		first_start = timezone.make_aware(datetime.datetime.combine(self.booking_date, datetime.time(9, 0)))
		second_date = self.booking_date + datetime.timedelta(days=1)
		second_day = WorkingDay.objects.create(business=self.business, day_of_week=second_date.weekday())
		WorkingHours.objects.create(working_day=second_day, start_time='09:00', end_time='12:00')
		second_start = timezone.make_aware(datetime.datetime.combine(second_date, datetime.time(9, 0)))

		first = create_confirmed_appointment(
			self.business, self.service, first_start, 'Maria Silva', '(11) 99999-9999',
		)
		second = create_confirmed_appointment(
			self.business, self.service, second_start, 'Maria S.', '11999999999',
		)

		self.assertEqual(first.customer_id, second.customer_id)
		customer = Customer.objects.get()
		self.assertEqual(customer.name, 'Maria S.')
		self.assertEqual(customer.completed_count, 0)
		self.assertEqual(BusinessNotification.objects.filter(business=self.business).count(), 2)
		self.assertTrue(BusinessNotification.objects.filter(
			business=self.business,
			event_type=BusinessNotification.EventType.APPOINTMENT_CREATED,
		).exists())

	def test_customer_history_counts_completed_appointments_and_last_service(self):
		start = timezone.make_aware(datetime.datetime.combine(self.booking_date, datetime.time(9, 0)))
		appointment = create_confirmed_appointment(
			self.business, self.service, start, 'Maria Silva', '11999999999',
		)
		appointment.status = Appointment.Status.COMPLETED
		appointment.save(update_fields=['status', 'updated_at'])

		customer = appointment.customer
		self.assertEqual(customer.completed_count, 1)
		self.assertEqual(customer.last_completed_service, 'Corte clássico')

		self.client.force_login(self.user)
		response = self.client.get(f'/appointments/?date={self.booking_date.isoformat()}')
		self.assertContains(response, '1 atendimento concluído')
		self.assertContains(response, 'último: Corte clássico')


class ServiceTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='joao', password='Senha-forte-123')
		self.business = Business.objects.create(owner=self.user, name='Barbearia do João')
		self.client.force_login(self.user)

	def test_creates_service_and_calculates_operational_time(self):
		response = self.client.post(
			'/services/new/',
			{
				'name': 'Corte masculino',
				'description': 'Corte tradicional',
				'price': '45.00',
				'duration_minutes': 30,
				'buffer_minutes': 10,
				'is_active': 'on',
			},
		)

		self.assertRedirects(response, '/services/')
		service = Service.objects.get(business=self.business)
		self.assertEqual(service.name, 'Corte masculino')
		self.assertEqual(service.operational_minutes, 40)
		self.assertTrue(service.is_active)

	def test_edits_service_and_recalculates_operational_time(self):
		service = Service.objects.create(
			business=self.business,
			name='Corte masculino',
			price='45.00',
			duration_minutes=30,
			buffer_minutes=10,
		)

		response = self.client.post(
			f'/services/{service.id}/edit/',
			{
				'name': 'Corte premium',
				'description': 'Inclui acabamento',
				'price': '60.00',
				'duration_minutes': 45,
				'buffer_minutes': 15,
				'is_active': 'on',
			},
		)

		self.assertRedirects(response, '/services/')
		service.refresh_from_db()
		self.assertEqual(service.name, 'Corte premium')
		self.assertEqual(service.operational_minutes, 60)

	def test_service_isolation_between_businesses(self):
		service = Service.objects.create(
			business=self.business,
			name='Corte masculino',
			price='45.00',
			duration_minutes=30,
		)
		other_user = User.objects.create_user(username='maria', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Studio Maria')
		other_service = Service.objects.create(
			business=other_business,
			name='Manicure',
			price='30.00',
			duration_minutes=20,
		)

		list_response = self.client.get('/services/')
		self.assertContains(list_response, service.name)
		self.assertNotContains(list_response, other_service.name)

		edit_response = self.client.get(f'/services/{other_service.id}/edit/')
		self.assertEqual(edit_response.status_code, 404)

		toggle_response = self.client.post(f'/services/{other_service.id}/toggle/')
		self.assertEqual(toggle_response.status_code, 404)
		other_service.refresh_from_db()
		self.assertTrue(other_service.is_active)

	def test_service_can_be_activated_and_deactivated(self):
		service = Service.objects.create(
			business=self.business,
			name='Corte masculino',
			price='45.00',
			duration_minutes=30,
		)

		deactivate_response = self.client.post(f'/services/{service.id}/toggle/')
		self.assertRedirects(deactivate_response, '/services/')
		service.refresh_from_db()
		self.assertFalse(service.is_active)

		activate_response = self.client.post(f'/services/{service.id}/toggle/')
		self.assertRedirects(activate_response, '/services/')
		service.refresh_from_db()
		self.assertTrue(service.is_active)


class AppointmentTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='joao', password='Senha-forte-123')
		self.business = Business.objects.create(owner=self.user, name='Barbearia do João')
		self.service = Service.objects.create(
			business=self.business,
			name='Corte masculino',
			price='45.00',
			duration_minutes=30,
		)
		self.start_datetime = timezone.make_aware(datetime.datetime(2026, 8, 24, 10, 0))

	def test_new_appointment_is_confirmed_and_has_cancellation_token(self):
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=self.start_datetime,
			client_name='Maria Silva',
			client_phone='11999999999',
		)

		self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)
		self.assertIsNotNone(appointment.cancellation_token)
		self.assertIsNotNone(appointment.created_at)

	def test_service_from_another_business_is_rejected(self):
		other_user = User.objects.create_user(username='maria', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Studio Maria')
		other_service = Service.objects.create(
			business=other_business,
			name='Manicure',
			price='30.00',
			duration_minutes=30,
		)
		appointment = Appointment(
			business=self.business,
			service=other_service,
			start_datetime=self.start_datetime,
			client_name='Maria Silva',
			client_phone='11999999999',
		)

		with self.assertRaisesMessage(ValidationError, 'O serviço deve pertencer ao negócio do agendamento.'):
			appointment.full_clean()

	def test_naive_start_datetime_is_rejected(self):
		appointment = Appointment(
			business=self.business,
			service=self.service,
			start_datetime=datetime.datetime(2026, 8, 24, 10, 0),
			client_name='Maria Silva',
			client_phone='11999999999',
		)

		with self.assertRaisesMessage(ValidationError, 'O horário do agendamento deve conter timezone.'):
			appointment.full_clean()

	def test_customer_from_another_business_is_rejected(self):
		other_user = User.objects.create_user(username='cliente-outro-owner', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Studio Maria')
		other_customer = Customer.objects.create(
			business=other_business,
			name='Maria Silva',
			phone='11999999999',
			normalized_phone='11999999999',
		)
		appointment = Appointment(
			business=self.business,
			service=self.service,
			customer=other_customer,
			start_datetime=self.start_datetime,
			client_name='Maria Silva',
			client_phone='11999999999',
		)

		with self.assertRaisesMessage(ValidationError, 'O cliente deve pertencer ao negócio do agendamento.'):
			appointment.full_clean()

	def test_public_flow_creates_confirmed_appointment(self):
		monday = WorkingDay.objects.create(business=self.business, day_of_week=0)
		WorkingHours.objects.create(working_day=monday, start_time='09:00', end_time='12:00')
		booking_date = '2026-08-31'

		services_response = self.client.get(f'/book/{self.business.slug}/')
		self.assertContains(services_response, self.service.name)

		booking_response = self.client.get(
			f'/book/{self.business.slug}/service/{self.service.id}/?date={booking_date}',
		)
		self.assertContains(booking_response, '09:00')

		response = self.client.post(
			f'/book/{self.business.slug}/service/{self.service.id}/',
			{
				'date': booking_date,
				'start_datetime': f'{booking_date}T09:00',
				'client_name': 'Maria Silva',
				'client_phone': '11999999999',
			},
		)

		self.assertEqual(response.status_code, 200)
		appointment = Appointment.objects.get()
		self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)
		self.assertContains(response, str(appointment.cancellation_token))

	def test_public_confirmation_includes_whatsapp_link_when_business_has_phone(self):
		self.business.whatsapp_phone = '(11) 98888-7777'
		self.business.save(update_fields=['whatsapp_phone'])
		monday = WorkingDay.objects.create(business=self.business, day_of_week=0)
		WorkingHours.objects.create(working_day=monday, start_time='09:00', end_time='12:00')
		booking_date = '2026-08-31'

		response = self.client.post(
			f'/book/{self.business.slug}/service/{self.service.id}/',
			{
				'date': booking_date,
				'start_datetime': f'{booking_date}T09:00',
				'client_name': 'Maria Silva',
				'client_phone': '11999999999',
			},
		)

		self.assertContains(response, 'https://wa.me/5511988887777?text=')
		self.assertContains(response, 'Falar pelo WhatsApp')

	def test_public_confirmation_omits_whatsapp_link_when_business_has_no_phone(self):
		monday = WorkingDay.objects.create(business=self.business, day_of_week=0)
		WorkingHours.objects.create(working_day=monday, start_time='09:00', end_time='12:00')
		booking_date = '2026-08-31'

		response = self.client.post(
			f'/book/{self.business.slug}/service/{self.service.id}/',
			{
				'date': booking_date,
				'start_datetime': f'{booking_date}T09:00',
				'client_name': 'Maria Silva',
				'client_phone': '11999999999',
			},
		)

		self.assertNotContains(response, 'Falar pelo WhatsApp')

	def test_public_flow_rejects_occupied_start(self):
		monday = WorkingDay.objects.create(business=self.business, day_of_week=0)
		WorkingHours.objects.create(working_day=monday, start_time='09:00', end_time='12:00')
		booking_date = '2026-08-31'
		Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.make_aware(datetime.datetime(2026, 8, 31, 9, 0)),
			client_name='Maria Silva',
			client_phone='11999999999',
		)

		response = self.client.post(
			f'/book/{self.business.slug}/service/{self.service.id}/',
			{
				'date': booking_date,
				'start_datetime': f'{booking_date}T09:00',
				'client_name': 'Joana Lima',
				'client_phone': '11888888888',
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'não está mais disponível')
		self.assertEqual(Appointment.objects.count(), 1)

	def test_transactional_creation_rejects_second_confirmation_for_same_interval(self):
		monday = WorkingDay.objects.create(business=self.business, day_of_week=0)
		WorkingHours.objects.create(working_day=monday, start_time='09:00', end_time='12:00')
		start_datetime = timezone.make_aware(datetime.datetime(2026, 8, 31, 9, 0))

		create_confirmed_appointment(
			self.business,
			self.service,
			start_datetime,
			'Maria Silva',
			'11999999999',
		)

		with self.assertRaises(AppointmentUnavailableError):
			create_confirmed_appointment(
				self.business,
				self.service,
				start_datetime,
				'Joana Lima',
				'11888888888',
			)

		self.assertEqual(Appointment.objects.count(), 1)

	def test_public_cancel_by_token_changes_status(self):
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.make_aware(datetime.datetime(2026, 8, 31, 10, 0)),
			client_name='Maria Silva',
			client_phone='11999999999',
		)

		response = self.client.post(f'/appointments/cancel/{appointment.cancellation_token}/')

		self.assertEqual(response.status_code, 200)
		appointment.refresh_from_db()
		self.assertEqual(appointment.status, Appointment.Status.CANCELLED)
		self.assertTrue(BusinessNotification.objects.filter(
			appointment=appointment,
			event_type=BusinessNotification.EventType.APPOINTMENT_CANCELLED,
		).exists())

	def test_public_cancel_after_start_is_rejected(self):
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.now() - datetime.timedelta(minutes=1),
			client_name='Maria Silva',
			client_phone='11999999999',
		)

		response = self.client.post(f'/appointments/cancel/{appointment.cancellation_token}/')

		self.assertContains(response, 'já começou')
		appointment.refresh_from_db()
		self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)

	def test_owner_can_list_and_cancel_future_appointment(self):
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.now() + datetime.timedelta(days=1),
			client_name='Maria Silva',
			client_phone='11999999999',
		)
		self.client.force_login(self.user)
		selected_date = timezone.localtime(appointment.start_datetime).date().isoformat()

		list_response = self.client.get(f'/appointments/?date={selected_date}')
		self.assertContains(list_response, appointment.client_name)
		self.assertContains(list_response, 'Cancelar')
		self.assertContains(list_response, 'WhatsApp')
		self.assertContains(list_response, 'https://wa.me/5511999999999?text=')

		cancel_response = self.client.post(f'/appointments/{appointment.id}/cancel/')

		self.assertRedirects(cancel_response, '/appointments/')
		appointment.refresh_from_db()
		self.assertEqual(appointment.status, Appointment.Status.CANCELLED)

	def test_administrative_list_filters_appointments_by_selected_date(self):
		selected_date = timezone.localdate() + datetime.timedelta(days=2)
		other_date = selected_date + datetime.timedelta(days=1)
		first_appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.make_aware(datetime.datetime.combine(selected_date, datetime.time(9, 0))),
			client_name='Cliente do dia',
			client_phone='11999999999',
		)
		second_appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.make_aware(datetime.datetime.combine(other_date, datetime.time(9, 0))),
			client_name='Cliente de outro dia',
			client_phone='11888888888',
		)
		self.client.force_login(self.user)

		response = self.client.get(f'/appointments/?date={selected_date.isoformat()}')

		self.assertContains(response, first_appointment.client_name)
		self.assertNotContains(response, second_appointment.client_name)

	def test_administrative_list_is_isolated_between_businesses(self):
		other_user = User.objects.create_user(username='outro-owner', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Studio Maria')
		other_service = Service.objects.create(
			business=other_business,
			name='Manicure',
			price='30.00',
			duration_minutes=30,
		)
		other_appointment = Appointment.objects.create(
			business=other_business,
			service=other_service,
			start_datetime=timezone.now() + datetime.timedelta(days=1),
			client_name='Cliente de outro negócio',
			client_phone='11888888888',
		)
		self.client.force_login(self.user)

		response = self.client.get('/appointments/')

		self.assertNotContains(response, other_appointment.client_name)

		cancel_response = self.client.post(f'/appointments/{other_appointment.id}/cancel/')
		self.assertEqual(cancel_response.status_code, 404)
		other_appointment.refresh_from_db()
		self.assertEqual(other_appointment.status, Appointment.Status.CONFIRMED)

	def test_administrative_cancel_does_not_cancel_started_appointment(self):
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.now() - datetime.timedelta(minutes=1),
			client_name='Maria Silva',
			client_phone='11999999999',
		)
		self.client.force_login(self.user)

		response = self.client.post(f'/appointments/{appointment.id}/cancel/')

		self.assertRedirects(response, '/appointments/')
		appointment.refresh_from_db()
		self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)

	def test_owner_can_mark_started_appointment_as_completed(self):
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.now() - datetime.timedelta(minutes=1),
			client_name='Maria Silva',
			client_phone='11999999999',
		)
		self.client.force_login(self.user)

		response = self.client.post(f'/appointments/{appointment.id}/status/completed/')

		self.assertRedirects(response, f'/appointments/?date={appointment.start_datetime.date().isoformat()}')
		appointment.refresh_from_db()
		self.assertEqual(appointment.status, Appointment.Status.COMPLETED)

	def test_owner_can_mark_started_appointment_as_no_show(self):
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.now() - datetime.timedelta(minutes=1),
			client_name='Maria Silva',
			client_phone='11999999999',
		)
		self.client.force_login(self.user)

		response = self.client.post(f'/appointments/{appointment.id}/status/no_show/')

		self.assertRedirects(response, f'/appointments/?date={appointment.start_datetime.date().isoformat()}')
		appointment.refresh_from_db()
		self.assertEqual(appointment.status, Appointment.Status.NO_SHOW)

	def test_future_appointment_cannot_be_marked_as_attended(self):
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.now() + datetime.timedelta(days=1),
			client_name='Maria Silva',
			client_phone='11999999999',
		)
		self.client.force_login(self.user)

		self.client.post(f'/appointments/{appointment.id}/status/completed/')

		appointment.refresh_from_db()
		self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)

	def test_administrative_cancel_requires_post_and_login(self):
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.now() + datetime.timedelta(days=1),
			client_name='Maria Silva',
			client_phone='11999999999',
		)

		get_response = self.client.get(f'/appointments/{appointment.id}/cancel/')
		self.assertRedirects(get_response, f'/login/?next=/appointments/{appointment.id}/cancel/')

		self.client.force_login(self.user)
		self.assertRedirects(
			self.client.get(f'/appointments/{appointment.id}/cancel/'),
			'/appointments/',
		)
		appointment.refresh_from_db()
		self.assertEqual(appointment.status, Appointment.Status.CONFIRMED)


class WorkingHoursTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='joao', password='Senha-forte-123')
		self.business = Business.objects.create(owner=self.user, name='Barbearia do João')
		self.client.force_login(self.user)

	def schedule_payload(self, intervals_by_day=None, closed_days=None):
		intervals_by_day = intervals_by_day or {}
		closed_days = closed_days or set()
		payload = {}
		for day in range(7):
			prefix = f'hours-{day}'
			intervals = intervals_by_day.get(day, [])
			payload[f'day-{day}-is_closed'] = 'on' if day in closed_days else ''
			payload[f'{prefix}-TOTAL_FORMS'] = str(len(intervals))
			payload[f'{prefix}-INITIAL_FORMS'] = '0'
			payload[f'{prefix}-MIN_NUM_FORMS'] = '0'
			payload[f'{prefix}-MAX_NUM_FORMS'] = '1000'
			for index, (start, end) in enumerate(intervals):
				payload[f'{prefix}-{index}-start_time'] = start
				payload[f'{prefix}-{index}-end_time'] = end
		return payload

	def test_closed_day_has_no_intervals(self):
		response = self.client.post(
			'/working-hours/',
			self.schedule_payload(closed_days={0}),
		)

		self.assertRedirects(response, '/working-hours/')
		monday = WorkingDay.objects.get(business=self.business, day_of_week=0)
		self.assertTrue(monday.is_closed)
		self.assertFalse(monday.hours.exists())

	def test_day_accepts_multiple_intervals(self):
		response = self.client.post(
			'/working-hours/',
			self.schedule_payload({0: [('08:00', '12:00'), ('14:00', '18:00')]}),
		)

		self.assertRedirects(response, '/working-hours/')
		monday = WorkingDay.objects.get(business=self.business, day_of_week=0)
		self.assertEqual(monday.hours.count(), 2)
		self.assertEqual(
			list(monday.hours.values_list('start_time', 'end_time')),
			[(datetime.time(8, 0), datetime.time(12, 0)), (datetime.time(14, 0), datetime.time(18, 0))],
		)

	def test_overlapping_new_intervals_are_rejected_by_formset(self):
		response = self.client.post(
			'/working-hours/',
			self.schedule_payload({0: [('08:00', '12:00'), ('11:00', '14:00')]}),
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Os intervalos de horário não podem se sobrepor.')
		self.assertFalse(WorkingHours.objects.exists())

	def test_overlapping_intervals_are_rejected_by_model_validation(self):
		monday = WorkingDay.objects.create(business=self.business, day_of_week=0)
		WorkingHours.objects.create(
			working_day=monday,
			start_time='08:00',
			end_time='12:00',
		)
		overlapping_interval = WorkingHours(
			working_day=monday,
			start_time='11:00',
			end_time='14:00',
		)

		with self.assertRaisesMessage(ValidationError, 'Os intervalos de horário não podem se sobrepor.'):
			overlapping_interval.full_clean()

	def test_adjacent_intervals_are_allowed_by_model_validation(self):
		monday = WorkingDay.objects.create(business=self.business, day_of_week=0)
		WorkingHours.objects.create(
			working_day=monday,
			start_time='08:00',
			end_time='12:00',
		)
		adjacent_interval = WorkingHours(
			working_day=monday,
			start_time='12:00',
			end_time='14:00',
		)

		adjacent_interval.full_clean()

	def test_invalid_interval_is_rejected(self):
		response = self.client.post(
			'/working-hours/',
			self.schedule_payload({0: [('18:00', '08:00')]}),
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'O início deve ser anterior ao fim do intervalo.')
		self.assertFalse(WorkingHours.objects.exists())

	def test_closed_day_with_interval_is_rejected(self):
		response = self.client.post(
			'/working-hours/',
			self.schedule_payload({0: [('08:00', '12:00')]}, closed_days={0}),
		)

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Um dia fechado não pode ter intervalos de horário.')
		self.assertFalse(WorkingHours.objects.exists())

	def test_working_hours_are_isolated_between_businesses(self):
		other_user = User.objects.create_user(username='maria', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Studio Maria')
		other_monday = WorkingDay.objects.create(business=other_business, day_of_week=0)
		WorkingHours.objects.create(working_day=other_monday, start_time='09:00', end_time='17:00')

		response = self.client.get('/working-hours/')
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, self.business.name)
		self.assertNotContains(response, other_business.name)

		self.client.post('/working-hours/', self.schedule_payload({0: [('10:00', '16:00')]}))
		other_monday.refresh_from_db()
		self.assertEqual(other_monday.hours.first().start_time, datetime.time(9, 0))


class WhatsAppReminderTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='reminder-owner', password='Senha-forte-123')
		self.business = Business.objects.create(
			owner=self.user,
			name='Barbearia Central',
			whatsapp_reminders_enabled=True,
			whatsapp_reminder_lead_time_minutes=20,
		)
		self.service = Service.objects.create(
			business=self.business,
			name='Corte clássico',
			price='45.00',
			duration_minutes=30,
		)

	def make_reminder(self, **appointment_values):
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.now() + datetime.timedelta(minutes=10),
			client_name='Maria Silva',
			client_phone='11999999999',
			whatsapp_reminder_opt_in=True,
			**appointment_values,
		)
		return AppointmentReminder.objects.create(appointment=appointment)

	def test_booking_service_creates_reminder_intent_only_with_opt_in_and_enabled_business(self):
		booking_date = timezone.localdate() + datetime.timedelta(days=2)
		start = timezone.make_aware(datetime.datetime.combine(booking_date, datetime.time(9, 0)))
		working_day = WorkingDay.objects.create(business=self.business, day_of_week=booking_date.weekday())
		WorkingHours.objects.create(working_day=working_day, start_time='00:00', end_time='23:59')

		appointment = create_confirmed_appointment(
			self.business, self.service, start, 'Maria Silva', '11999999999',
			whatsapp_reminder_opt_in=True,
			whatsapp_opt_in_source='public_booking',
		)

		self.assertTrue(AppointmentReminder.objects.filter(appointment=appointment).exists())
		self.assertEqual(appointment.whatsapp_opt_in_source, 'public_booking')

	def test_command_sends_due_reminder_once(self):
		from django.core.management import call_command

		reminder = self.make_reminder()
		WhatsAppIntegration.objects.create(
			business=self.business,
			instance_name='agenda-facil-central',
			api_key_env_var='EVOLUTION_API_KEY',
			status=WhatsAppIntegration.Status.CONNECTED,
		)
		with patch('agenda.management.commands.send_whatsapp_reminders.send_appointment_reminder', return_value='wamid.test') as send:
			call_command('send_whatsapp_reminders')
			call_command('send_whatsapp_reminders')

		reminder.refresh_from_db()
		self.assertEqual(reminder.status, AppointmentReminder.Status.SENT)
		self.assertEqual(reminder.provider_message_id, 'wamid.test')
		send.assert_called_once()

	def test_command_skips_cancelled_reminder(self):
		from django.core.management import call_command

		reminder = self.make_reminder(status=Appointment.Status.CANCELLED)
		with patch('agenda.management.commands.send_whatsapp_reminders.send_appointment_reminder') as send:
			call_command('send_whatsapp_reminders')

		reminder.refresh_from_db()
		self.assertEqual(reminder.status, AppointmentReminder.Status.CANCELLED)
		self.assertIn('confirmado', reminder.last_error)
		send.assert_not_called()

	def test_command_cancels_reminder_without_customer_consent(self):
		from django.core.management import call_command

		reminder = self.make_reminder()
		reminder.appointment.whatsapp_reminder_opt_in = False
		reminder.appointment.save(update_fields=['whatsapp_reminder_opt_in'])
		with patch('agenda.management.commands.send_whatsapp_reminders.send_appointment_reminder') as send:
			call_command('send_whatsapp_reminders')

		reminder.refresh_from_db()
		self.assertEqual(reminder.status, AppointmentReminder.Status.CANCELLED)
		self.assertIn('autorizou', reminder.last_error)
		send.assert_not_called()

	def test_reminder_history_is_isolated_by_business(self):
		from django.utils import timezone

		own_reminder = self.make_reminder()
		other_user = User.objects.create_user(username='other-reminder-owner', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Outro negócio')
		other_service = Service.objects.create(
			business=other_business,
			name='Outro serviço',
			price='30.00',
			duration_minutes=30,
		)
		other_appointment = Appointment.objects.create(
			business=other_business,
			service=other_service,
			start_datetime=timezone.now() + datetime.timedelta(minutes=30),
			client_name='Cliente de outro negócio',
			client_phone='5511888888888',
		)
		AppointmentReminder.objects.create(appointment=other_appointment)
		self.client.force_login(self.user)

		response = self.client.get('/business/whatsapp/reminders/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, own_reminder.appointment.client_name)
		self.assertNotContains(response, 'Cliente de outro negócio')

	def test_reminder_history_requires_login(self):
		response = self.client.get('/business/whatsapp/reminders/')

		self.assertRedirects(response, '/login/?next=/business/whatsapp/reminders/')

	def test_evolution_client_sends_text_to_instance(self):
		from agenda.integrations.whatsapp import send_appointment_reminder

		reminder = self.make_reminder()
		integration = WhatsAppIntegration.objects.create(
			business=self.business,
			instance_name='agenda-facil-central',
			api_key_env_var='EVOLUTION_API_KEY',
			status=WhatsAppIntegration.Status.CONNECTED,
		)
		response_mock = MagicMock()
		response_mock.__enter__.return_value.read.return_value = b'{"key": {"id": "evolution-message-id"}}'

		with patch.dict('os.environ', {'EVOLUTION_API_KEY': 'test-api-key'}), patch(
			'agenda.integrations.whatsapp.request.urlopen', return_value=response_mock,
		) as urlopen:
			message_id = send_appointment_reminder(reminder)

		self.assertEqual(message_id, 'evolution-message-id')
		api_request = urlopen.call_args.args[0]
		self.assertEqual(api_request.full_url, 'http://localhost:8080/message/sendText/agenda-facil-central')
		self.assertEqual(api_request.get_header('Apikey'), 'test-api-key')
		self.assertEqual(
			json.loads(api_request.data.decode('utf-8')),
			{
				'number': '5511999999999',
				'text': 'Olá, Maria Silva! Lembrete: seu atendimento de Corte clássico está marcado para '
				f'{timezone.localtime(reminder.appointment.start_datetime):%d/%m/%Y às %H:%M}.',
			},
		)

	def test_reminder_uses_business_message_template(self):
		from agenda.integrations.whatsapp import send_appointment_reminder

		self.business.whatsapp_reminder_message = 'Oi {cliente}, {servico} em {data} às {hora} - {negocio}.'
		self.business.save(update_fields=['whatsapp_reminder_message'])
		reminder = self.make_reminder()
		integration = WhatsAppIntegration.objects.create(
			business=self.business,
			instance_name='agenda-facil-central',
			api_key_env_var='EVOLUTION_API_KEY',
			status=WhatsAppIntegration.Status.CONNECTED,
		)
		response_mock = MagicMock()
		response_mock.__enter__.return_value.read.return_value = b'{"key": {"id": "message-template-test"}}'

		with patch.dict('os.environ', {'EVOLUTION_API_KEY': 'test-api-key'}), patch(
			'agenda.integrations.whatsapp.request.urlopen', return_value=response_mock,
		) as urlopen:
			send_appointment_reminder(reminder)

		payload = json.loads(urlopen.call_args.args[0].data.decode('utf-8'))
		local_start = timezone.localtime(reminder.appointment.start_datetime)
		self.assertEqual(payload['text'], f'Oi Maria Silva, Corte clássico em {local_start:%d/%m/%Y} às {local_start:%H:%M} - Barbearia Central.')

class AvailabilityTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='joao', password='Senha-forte-123')
		self.business = Business.objects.create(owner=self.user, name='Barbearia do João')
		self.service = Service.objects.create(
			business=self.business,
			name='Corte masculino',
			price='45.00',
			duration_minutes=60,
			buffer_minutes=15,
		)
		self.monday = WorkingDay.objects.create(business=self.business, day_of_week=0)

	def add_interval(self, start, end):
		return WorkingHours.objects.create(
			working_day=self.monday,
			start_time=start,
			end_time=end,
		)

	def test_returns_empty_for_closed_or_unconfigured_day(self):
		self.monday.is_closed = True
		self.monday.save()

		closed_day = get_available_start_times(self.business, self.service, datetime.date(2026, 8, 24))
		unconfigured_day = get_available_start_times(self.business, self.service, datetime.date(2026, 8, 25))

		self.assertEqual(closed_day, [])
		self.assertEqual(unconfigured_day, [])

	def test_uses_granularity_and_keeps_intervals_separate(self):
		self.business.slot_granularity_minutes = 30
		self.business.save()
		self.add_interval('08:00', '10:00')
		self.add_interval('14:00', '16:00')

		result = get_available_start_times(
			self.business,
			self.service,
			datetime.date(2026, 8, 24),
			now=timezone.make_aware(datetime.datetime(2026, 8, 23, 12, 0)),
		)

		self.assertEqual(
			result,
			[
				timezone.make_aware(datetime.datetime(2026, 8, 24, 8, 0)),
				timezone.make_aware(datetime.datetime(2026, 8, 24, 8, 30)),
				timezone.make_aware(datetime.datetime(2026, 8, 24, 14, 0)),
				timezone.make_aware(datetime.datetime(2026, 8, 24, 14, 30)),
			],
		)

	def test_requires_operational_time_to_fit_inside_one_interval(self):
		self.add_interval('08:00', '09:00')

		result = get_available_start_times(
			self.business,
			self.service,
			datetime.date(2026, 8, 24),
			now=timezone.make_aware(datetime.datetime(2026, 8, 23, 12, 0)),
		)

		self.assertEqual(result, [])

	def test_excludes_past_starts_using_local_now(self):
		self.add_interval('08:00', '12:00')
		self.service.duration_minutes = 30
		self.service.buffer_minutes = 0
		self.service.save()

		result = get_available_start_times(
			self.business,
			self.service,
			datetime.date(2026, 8, 24),
			now=timezone.make_aware(datetime.datetime(2026, 8, 24, 9, 15)),
		)

		self.assertEqual(result[0], timezone.make_aware(datetime.datetime(2026, 8, 24, 9, 30)))
		self.assertNotIn(timezone.make_aware(datetime.datetime(2026, 8, 24, 9, 0)), result)

	def test_margin_after_service_can_remove_last_candidate(self):
		self.add_interval('08:00', '09:45')
		self.service.duration_minutes = 90
		self.service.buffer_minutes = 15
		self.service.save()

		result = get_available_start_times(
			self.business,
			self.service,
			datetime.date(2026, 8, 24),
			now=timezone.make_aware(datetime.datetime(2026, 8, 23, 12, 0)),
		)

		self.assertEqual(result, [timezone.make_aware(datetime.datetime(2026, 8, 24, 8, 0))])

	def test_inactive_or_foreign_service_is_not_available(self):
		self.add_interval('08:00', '12:00')
		self.service.is_active = False
		self.service.save()

		self.assertEqual(
			get_available_start_times(
				self.business,
				self.service,
				datetime.date(2026, 8, 24),
				now=timezone.make_aware(datetime.datetime(2026, 8, 23, 12, 0)),
			),
			[],
		)

	def test_confirmed_appointment_blocks_overlapping_starts(self):
		self.service.duration_minutes = 60
		self.service.save()
		self.business.slot_granularity_minutes = 30
		self.business.save()
		self.add_interval('08:00', '12:00')
		Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.make_aware(datetime.datetime(2026, 8, 24, 9, 0)),
			client_name='Maria Silva',
			client_phone='11999999999',
		)

		result = get_available_start_times(
			self.business,
			self.service,
			datetime.date(2026, 8, 24),
			now=timezone.make_aware(datetime.datetime(2026, 8, 23, 12, 0)),
		)

		self.assertEqual(
			result,
			[
				timezone.make_aware(datetime.datetime(2026, 8, 24, 10, 30)),
			],
		)

	def test_cancelled_appointment_does_not_block_and_other_business_is_ignored(self):
		self.add_interval('08:00', '10:00')
		appointment = Appointment.objects.create(
			business=self.business,
			service=self.service,
			start_datetime=timezone.make_aware(datetime.datetime(2026, 8, 24, 8, 0)),
			client_name='Maria Silva',
			client_phone='11999999999',
			status=Appointment.Status.CANCELLED,
		)

		other_user = User.objects.create_user(username='maria', password='Senha-forte-123')
		other_business = Business.objects.create(owner=other_user, name='Studio Maria')
		other_service = Service.objects.create(
			business=other_business,
			name='Manicure',
			price='30.00',
			duration_minutes=30,
		)
		Appointment.objects.create(
			business=other_business,
			service=other_service,
			start_datetime=appointment.start_datetime,
			client_name='Joana',
			client_phone='11888888888',
		)

		result = get_available_start_times(
			self.business,
			self.service,
			datetime.date(2026, 8, 24),
			now=timezone.make_aware(datetime.datetime(2026, 8, 23, 12, 0)),
		)

		self.assertEqual(
			result,
			[
				timezone.make_aware(datetime.datetime(2026, 8, 24, 8, 0)),
				timezone.make_aware(datetime.datetime(2026, 8, 24, 8, 15)),
				timezone.make_aware(datetime.datetime(2026, 8, 24, 8, 30)),
				timezone.make_aware(datetime.datetime(2026, 8, 24, 8, 45)),
			],
		)
