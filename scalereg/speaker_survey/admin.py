from django.contrib import admin
from models import Speaker
from models import Survey7X


class Survey7XOptions(admin.ModelAdmin):
  save_on_top = True


class SpeakerOptions(admin.ModelAdmin):
  save_on_top = True


admin.site.register(Survey7X, Survey7XOptions)
admin.site.register(Speaker, SpeakerOptions)
