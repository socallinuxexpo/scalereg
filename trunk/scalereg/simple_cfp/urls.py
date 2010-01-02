from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scalereg.simple_cfp.views.index'),
    (r'^accepted_presentations/$', 'scalereg.simple_cfp.views.AcceptedPresentations'),
    (r'^accepted_speakers/$', 'scalereg.simple_cfp.views.AcceptedSpeakers'),
    (r'^logout/$', 'scalereg.simple_cfp.views.Logout'),
    (r'^recover_validation/$', 'scalereg.simple_cfp.views.RecoverValidation'),
    (r'^speaker_registration/$', 'scalereg.simple_cfp.views.RegisterSpeaker'),
    (r'^submission_status/$', 'scalereg.simple_cfp.views.SubmissionStatus'),
    (r'^submit_presentation/$', 'scalereg.simple_cfp.views.SubmitPresentation'),
    (r'^review/', include('scalereg.simple_cfp.review.urls')),
)
