from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scale.speaker_survey.views.SurveyLookup'),
    (r'^mass_add/$', 'scale.speaker_survey.views.MassAdd'),
)
