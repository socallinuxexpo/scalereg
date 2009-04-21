from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scale.speaker_survey.views.SurveyLookup'),
)
