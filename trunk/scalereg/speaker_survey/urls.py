from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scalereg.speaker_survey.views.SurveyLookup'),
    (r'^(?P<hash>[0-9a-f]{10})/$', 'scalereg.speaker_survey.views.Survey'),
    (r'^(?P<hash>[0-9a-f]{10})/(?P<id>\d{1,4})/$', 'scalereg.speaker_survey.views.Survey'),
    (r'^mass_add/$', 'scalereg.speaker_survey.views.MassAdd'),
    (r'^url_dump/$', 'scalereg.speaker_survey.views.UrlDump'),
    (r'^scores/$', 'scalereg.speaker_survey.views.Scores'),
    (r'^scores/(?P<id>\d{1,4})/$', 'scalereg.speaker_survey.views.Scores'),
)
