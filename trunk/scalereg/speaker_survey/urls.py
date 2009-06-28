from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scale.speaker_survey.views.SurveyLookup'),
    (r'^(?P<hash>[0-9a-f]{10})/$', 'scale.speaker_survey.views.Survey'),
    (r'^(?P<hash>[0-9a-f]{10})/(?P<id>\d{1,4})/$', 'scale.speaker_survey.views.Survey'),
    (r'^mass_add/$', 'scale.speaker_survey.views.MassAdd'),
    (r'^url_dump/$', 'scale.speaker_survey.views.UrlDump'),
    (r'^scores/$', 'scale.speaker_survey.views.Scores'),
    (r'^scores/(?P<id>\d{1,4})/$', 'scale.speaker_survey.views.Scores'),
)
