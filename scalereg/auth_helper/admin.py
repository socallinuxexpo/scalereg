from django.contrib import admin
from models import Service


class ServiceOptions(admin.ModelAdmin):
  list_display = ('name', 'active', 'url')


admin.site.register(Service, ServiceOptions)
