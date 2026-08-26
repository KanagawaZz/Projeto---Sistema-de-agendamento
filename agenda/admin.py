from django.contrib import admin

from .models import BusinessPage


@admin.register(BusinessPage)
class BusinessPageAdmin(admin.ModelAdmin):
	list_display = ('business', 'is_published', 'theme', 'updated_at')
from django.contrib import admin

# Register your models here.
