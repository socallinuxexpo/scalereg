from auth_helper.models import Service
from django.contrib import admin


class ServiceOptions(admin.ModelAdmin):
  list_display = ('name', 'active', 'url')


admin.site.register(Service, ServiceOptions)
