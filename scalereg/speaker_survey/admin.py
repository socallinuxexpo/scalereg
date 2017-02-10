from django.contrib import admin
from models import Speaker
from models import Survey7X


class Survey7XAdmin(admin.ModelAdmin):
  save_on_top = True


class SpeakerAdmin(admin.ModelAdmin):
  save_on_top = True


admin.site.register(Survey7X, Survey7XAdmin)
admin.site.register(Speaker, SpeakerAdmin)
