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


def validate_whatsapp_connection(integration: WhatsAppIntegration):
	env_var = f'WHATSAPP_TOKEN_BUSINESS_{integration.business_id}'
	token = os.environ.get(env_var, '')
	if not token or not integration.phone_number_id:
		raise WhatsAppProviderError('Informe o ID do número e configure o token do negócio no servidor.')

	api_version = settings.WHATSAPP_GRAPH_API_VERSION
	url = f'https://graph.facebook.com/{api_version}/{integration.phone_number_id}'
	api_request = request.Request(
		url,
		headers={'Authorization': f'Bearer {token}'},
		method='GET',
	)
	try:
		with request.urlopen(api_request, timeout=settings.WHATSAPP_HTTP_TIMEOUT) as response:
			data = json.loads(response.read().decode('utf-8'))
	except error.HTTPError as exc:
		retryable = exc.code == 408 or exc.code == 429 or exc.code >= 500
		raise WhatsAppProviderError(f'Não foi possível validar a conexão (HTTP {exc.code}).', retryable=retryable) from exc
	except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
		raise WhatsAppProviderError('Não foi possível conectar à API do WhatsApp.', retryable=True) from exc

	if not data.get('id'):
		raise WhatsAppProviderError('A Meta não confirmou o número informado.')
	return data


def _recipient_phone(phone):
	normalized = normalize_phone(phone)
	if len(normalized) in (10, 11):
		normalized = f'55{normalized}'
	if not 10 <= len(normalized) <= 15:
		raise WhatsAppProviderError('Telefone do cliente inválido.')
	return normalized


def send_appointment_reminder(reminder: AppointmentReminder):
	appointment = reminder.appointment
	integration = getattr(appointment.business, 'whatsapp_integration', None)
	if integration is None or integration.status != WhatsAppIntegration.Status.CONNECTED:
		raise WhatsAppProviderError('A integração do WhatsApp não está conectada.')

	env_var = f'WHATSAPP_TOKEN_BUSINESS_{appointment.business_id}'
	token = os.environ.get(env_var, '')
	if not token or not integration.phone_number_id:
		raise WhatsAppProviderError('A integração do WhatsApp está incompleta.')

	local_start = timezone.localtime(appointment.start_datetime)
	payload = {
		'messaging_product': 'whatsapp',
		'to': _recipient_phone(appointment.client_phone),
		'type': 'template',
		'template': {
			'name': settings.WHATSAPP_REMINDER_TEMPLATE_NAME,
			'language': {'code': settings.WHATSAPP_REMINDER_TEMPLATE_LANGUAGE},
			'components': [{
				'type': 'body',
				'parameters': [
					{'type': 'text', 'text': appointment.client_name},
					{'type': 'text', 'text': appointment.service.name},
					{'type': 'text', 'text': local_start.strftime('%d/%m/%Y às %H:%M')},
				],
			}],
		},
	}
	api_version = settings.WHATSAPP_GRAPH_API_VERSION
	url = f'https://graph.facebook.com/{api_version}/{integration.phone_number_id}/messages'
	api_request = request.Request(
		url,
		data=json.dumps(payload).encode('utf-8'),
		headers={
			'Authorization': f'Bearer {token}',
			'Content-Type': 'application/json',
		},
		method='POST',
	)
	try:
		with request.urlopen(api_request, timeout=settings.WHATSAPP_HTTP_TIMEOUT) as response:
			data = json.loads(response.read().decode('utf-8'))
	except error.HTTPError as exc:
		retryable = exc.code == 408 or exc.code == 429 or exc.code >= 500
		raise WhatsAppProviderError(f'WhatsApp API HTTP {exc.code}.', retryable=retryable) from exc
	except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
		raise WhatsAppProviderError('Não foi possível conectar à API do WhatsApp.', retryable=True) from exc

	message_id = (data.get('messages') or [{}])[0].get('id')
	if not message_id:
		raise WhatsAppProviderError('A API do WhatsApp não retornou o ID da mensagem.')
	return message_id