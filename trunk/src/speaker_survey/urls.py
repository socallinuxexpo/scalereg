from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scale.speaker_survey.views.SurveyLookup'),
    (r'^mass_add/$', 'scale.speaker_survey.views.MassAdd'),
    (r'^url_dump/$', 'scale.speaker_survey.views.UrlDump'),
    (r'^scores/$', 'scale.speaker_survey.views.Scores'),
    (r'^scores/(?P<id>\d{1,4})/$', 'scale.speaker_survey.views.Scores'),
)
