from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scalereg.simple_cfp.review.views.index'),
    (r'^(?P<id>[0-9]+)/$', 'scalereg.simple_cfp.review.views.ReviewPresentation'),
    (r'^audience/$', 'scalereg.simple_cfp.review.views.AudienceIndex'),
    (r'^category/$', 'scalereg.simple_cfp.review.views.CategoryIndex'),
    (r'^speaker/$', 'scalereg.simple_cfp.review.views.SpeakerIndex'),
    (r'^status/$', 'scalereg.simple_cfp.review.views.StatusIndex'),
)
