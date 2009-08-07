from django.contrib import admin
from simple_cfp.models import Speaker


class SpeakerOptions(admin.ModelAdmin):
  fieldsets = (
    ('Speaker Info', {'fields': ('salutation', 'first_name', 'last_name',
                                 'title', 'org')}),
    ('Contact Info', {'fields': ('email', 'zip', 'phone')}),
    ('Other Info', {'fields': ('url', 'bio')}),
    ('Validation Info', {'fields': ('valid', 'validation_code')}),
  )
  list_display = ('id', 'first_name', 'last_name', 'title', 'org', 'email',
                  'valid', 'validation_code')
  save_on_top = True


admin.site.register(Speaker, SpeakerOptions)
