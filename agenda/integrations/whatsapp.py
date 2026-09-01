import json
import os
from urllib import error, request

from django.conf import settings
from django.utils import timezone

from ..models import AppointmentReminder, WhatsAppIntegration
from ..services import normalize_phone


class WhatsAppProviderError(Exception):
	def __init__(self, message, *, retryable=False):
		super().__init__(message)
		self.retryable = retryable


def _api_key(integration):
	env_var = integration.api_key_env_var or 'EVOLUTION_API_KEY'
	return os.environ.get(env_var, '')


def _evolution_request(method, path, integration, payload=None):
	api_key = _api_key(integration)
	if not api_key or not integration.instance_name:
		raise WhatsAppProviderError('Configure a API key e o nome da instância Evolution.')

	base_url = settings.EVOLUTION_API_URL.rstrip('/')
	api_request = request.Request(
		f'{base_url}{path}',
		data=json.dumps(payload).encode('utf-8') if payload is not None else None,
		headers={
			'apikey': api_key,
			'Content-Type': 'application/json',
		},
		method=method,
	)
	try:
		with request.urlopen(api_request, timeout=settings.WHATSAPP_HTTP_TIMEOUT) as response:
			return json.loads(response.read().decode('utf-8'))
	except error.HTTPError as exc:
		retryable = exc.code == 408 or exc.code == 429 or exc.code >= 500
		raise WhatsAppProviderError(f'Evolution API HTTP {exc.code}.', retryable=retryable) from exc
	except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
		raise WhatsAppProviderError('Não foi possível conectar à Evolution API.', retryable=True) from exc


def validate_whatsapp_connection(integration: WhatsAppIntegration):
	data = _evolution_request(
		'GET',
		f'/instance/connectionState/{integration.instance_name}',
		integration,
	)
	state = (data.get('instance') or {}).get('state') or data.get('state')
	if state != 'open':
		raise WhatsAppProviderError(f'A instância Evolution não está conectada (estado: {state or "desconhecido"}).')
	return data


def get_whatsapp_connection_data(integration: WhatsAppIntegration):
	return _evolution_request(
		'GET',
		f'/instance/connect/{integration.instance_name}',
		integration,
	)


def _recipient_phone(phone):
	normalized = normalize_phone(phone)
	if len(normalized) in (10, 11):
		normalized = f'55{normalized}'
	if not 10 <= len(normalized) <= 15:
		raise WhatsAppProviderError('Telefone do cliente inválido.')
	return normalized


def send_text_message(integration: WhatsAppIntegration, phone, text):
	payload = {
		'number': _recipient_phone(phone),
		'text': text,
	}
	data = _evolution_request(
		'POST',
		f'/message/sendText/{integration.instance_name}',
		integration,
		payload,
	)
	message_id = (data.get('key') or {}).get('id') or data.get('id')
	if not message_id:
		raise WhatsAppProviderError('A Evolution API não retornou o ID da mensagem.')
	return message_id


def send_appointment_reminder(reminder: AppointmentReminder):
	appointment = reminder.appointment
	integration = getattr(appointment.business, 'whatsapp_integration', None)
	if integration is None or integration.status != WhatsAppIntegration.Status.CONNECTED:
		raise WhatsAppProviderError('A integração do WhatsApp não está conectada.')

	local_start = timezone.localtime(appointment.start_datetime)
	message = appointment.business.whatsapp_reminder_message.format(
		cliente=appointment.client_name,
		servico=appointment.service.name,
		data=local_start.strftime('%d/%m/%Y'),
		hora=local_start.strftime('%H:%M'),
		negocio=appointment.business.name,
	)
	return send_text_message(
		integration,
		appointment.client_phone,
		message,
	)
