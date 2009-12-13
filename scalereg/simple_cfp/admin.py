from django.contrib import admin
from models import Audience
from models import Category
from models import Presentation
from models import Speaker


class SpeakerOptions(admin.ModelAdmin):
  fieldsets = (
    ('Contact Info', {'fields': ('contact_name', 'contact_email')}),
    ('Speaker Info', {'fields': ('salutation', 'first_name', 'last_name',
                                 'title', 'org')}),
    ('Contact Info', {'fields': ('email', 'zip', 'phone')}),
    ('Other Info', {'fields': ('url', 'bio')}),
    ('Validation Info', {'fields': ('valid', 'validation_code')}),
  )
  list_display = ('id', 'first_name', 'last_name', 'title', 'org',
                  'contact_email', 'email', 'valid', 'validation_code')
  list_filter = ('valid',)
  save_on_top = True


class PresentationOptions(admin.ModelAdmin):
  fieldsets = (
    (None, {'fields': ('speaker', 'valid', 'submission_code')}),
    ('Categories', {'fields': ('categories', 'audiences')}),
    ('Presentation', {'fields': ('title', 'description', 'short_abstract',
                                 'long_abstract', 'file', 'msg')}),
    ('Private Data', {'fields': ('status', 'score', 'notes')}),
  )
  list_display = ('id', 'submission_code', 'speaker', 'title', 'valid',
                  'status', 'score')
  list_filter = ('categories', 'audiences', 'valid', 'status')
  save_on_top = True


admin.site.register(Audience)
admin.site.register(Category)
admin.site.register(Presentation, PresentationOptions)
admin.site.register(Speaker, SpeakerOptions)
