from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from datetime import datetime

from django.utils import timezone

from .models import Appointment, Business, BusinessPage, Service, WhatsAppIntegration, WorkingDay, WorkingHours
from .services import get_available_start_times


class BusinessForm(forms.ModelForm):
	class Meta:
		model = Business
		fields = ('name', 'description', 'whatsapp_phone', 'whatsapp_reminders_enabled', 'whatsapp_reminder_lead_time_minutes')
		labels = {
			'name': 'Nome do negócio',
			'description': 'Descrição',
			'whatsapp_phone': 'WhatsApp do negócio',
			'whatsapp_reminders_enabled': 'Ativar lembretes automáticos',
			'whatsapp_reminder_lead_time_minutes': 'Enviar lembrete com antecedência (minutos)',
		}
		widgets = {
			'description': forms.Textarea(attrs={'rows': 4}),
			'whatsapp_phone': forms.TextInput(attrs={'placeholder': '(11) 99999-9999'}),
			'whatsapp_reminder_lead_time_minutes': forms.NumberInput(attrs={'min': 5, 'max': 1440}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['whatsapp_reminder_lead_time_minutes'].required = False

	def clean_whatsapp_reminder_lead_time_minutes(self):
		return self.cleaned_data.get('whatsapp_reminder_lead_time_minutes') or 20


class ServiceForm(forms.ModelForm):
	class Meta:
		model = Service
		fields = (
			'name',
			'description',
			'price',
			'duration_minutes',
			'buffer_minutes',
			'is_active',
		)
		labels = {
			'name': 'Nome do serviço',
			'description': 'Descrição',
			'price': 'Preço',
			'duration_minutes': 'Duração média (minutos)',
			'buffer_minutes': 'Margem de segurança (minutos)',
			'is_active': 'Serviço ativo',
		}


class AppointmentForm(forms.ModelForm):
	whatsapp_reminder_opt_in = forms.BooleanField(
		label='Aceito receber lembretes deste agendamento pelo WhatsApp',
		required=False,
	)

	class Meta:
		model = Appointment
		fields = ('client_name', 'client_phone')
		labels = {
			'client_name': 'Nome',
			'client_phone': 'Telefone',
		}


class AdminAppointmentForm(AppointmentForm):
	service = forms.ModelChoiceField(queryset=Service.objects.none(), label='Serviço')
	date = forms.DateField(label='Data', widget=forms.DateInput(attrs={'type': 'date'}))
	start_datetime = forms.ChoiceField(label='Horário', choices=())

	def __init__(self, *args, business, **kwargs):
		super().__init__(*args, **kwargs)
		self.business = business
		self.fields['service'].queryset = business.services.filter(is_active=True).order_by('name')
		service_value = self.data.get('service') if self.is_bound else self.initial.get('service')
		date_value = self.data.get('date') if self.is_bound else self.initial.get('date')
		self.available_times = []
		try:
			service = self.fields['service'].queryset.get(pk=service_value)
			target_date = date_value if hasattr(date_value, 'weekday') else datetime.strptime(date_value, '%Y-%m-%d').date()
		except (Service.DoesNotExist, TypeError, ValueError):
			return

		self.available_times = get_available_start_times(business, service, target_date)
		self.fields['start_datetime'].choices = [
			(time_value.strftime('%Y-%m-%dT%H:%M'), time_value.strftime('%H:%M'))
			for time_value in self.available_times
		]
		if self.is_bound:
			start_value = self.data.get('start_datetime')
			if start_value and not any(value == start_value for value, _ in self.fields['start_datetime'].choices):
				try:
					start_datetime = datetime.fromisoformat(start_value)
				except ValueError:
					pass
				else:
					if start_datetime.date() == target_date:
						self.fields['start_datetime'].choices.append((start_value, start_datetime.strftime('%H:%M')))

	def clean_start_datetime(self):
		value = self.cleaned_data['start_datetime']
		return timezone.make_aware(datetime.fromisoformat(value))


class BusinessPageForm(forms.ModelForm):
	class Meta:
		model = BusinessPage
		fields = ('public_title', 'public_description', 'cta_label', 'theme', 'primary_color', 'secondary_color', 'is_published')
		labels = {
			'public_title': 'Título público',
			'public_description': 'Descrição pública',
			'cta_label': 'Texto do botão de agendamento',
			'theme': 'Tema visual',
			'primary_color': 'Cor principal',
			'secondary_color': 'Cor de destaque',
			'is_published': 'Publicar página',
		}
		widgets = {
			'public_description': forms.Textarea(attrs={'rows': 5}),
			'primary_color': forms.TextInput(attrs={'type': 'color'}),
			'secondary_color': forms.TextInput(attrs={'type': 'color'}),
		}

	def clean_primary_color(self):
		value = self.cleaned_data.get('primary_color', '').strip()
		if value and not value.startswith('#'):
			raise forms.ValidationError('Use uma cor no formato hexadecimal, como #087f82.')
		return value or '#087f82'

	def clean_secondary_color(self):
		value = self.cleaned_data.get('secondary_color', '').strip()
		if value and not value.startswith('#'):
			raise forms.ValidationError('Use uma cor no formato hexadecimal, como #d88d4d.')
		return value or '#d88d4d'


class WhatsAppIntegrationForm(forms.ModelForm):
	class Meta:
		model = WhatsAppIntegration
		fields = ('phone_number_id',)
		labels = {
			'phone_number_id': 'ID do número na Meta',
		}
		widgets = {
			'phone_number_id': forms.TextInput(attrs={'placeholder': 'Ex.: 123456789012345'}),
		}


class WorkingDayForm(forms.ModelForm):
	class Meta:
		model = WorkingDay
		fields = ('is_closed',)
		labels = {'is_closed': 'Fechado'}


class WorkingHoursForm(forms.ModelForm):
	class Meta:
		model = WorkingHours
		fields = ('start_time', 'end_time')
		widgets = {
			'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
			'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
		}


class BaseWorkingHoursFormSet(BaseInlineFormSet):
	def clean(self):
		super().clean()
		if any(self.errors):
			return

		active_forms = [form for form in self.forms if form.cleaned_data and not form.cleaned_data.get('DELETE')]
		if self.instance.is_closed and active_forms:
			raise forms.ValidationError('Um dia fechado não pode ter intervalos de horário.')

		for index, form in enumerate(active_forms):
			start_time = form.cleaned_data['start_time']
			end_time = form.cleaned_data['end_time']
			for other_form in active_forms[index + 1:]:
				if (
					start_time < other_form.cleaned_data['end_time']
					and other_form.cleaned_data['start_time'] < end_time
				):
					raise forms.ValidationError('Os intervalos de horário não podem se sobrepor.')


WorkingHoursFormSet = inlineformset_factory(
	WorkingDay,
	WorkingHours,
	form=WorkingHoursForm,
	formset=BaseWorkingHoursFormSet,
	extra=1,
	can_delete=True,
)