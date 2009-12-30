from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scalereg.simple_cfp.review.views.index'),
    (r'^(?P<id>[0-9]+)/$', 'scalereg.simple_cfp.review.views.ReviewPresentation'),
    (r'^audience/$', 'scalereg.simple_cfp.review.views.AudienceIndex'),
    (r'^audience/(?P<id>[0-9]+)/$', 'scalereg.simple_cfp.review.views.Audience'),
    (r'^category/$', 'scalereg.simple_cfp.review.views.CategoryIndex'),
    (r'^category/(?P<id>[0-9]+)/$', 'scalereg.simple_cfp.review.views.Category'),
    (r'^speaker/$', 'scalereg.simple_cfp.review.views.SpeakerIndex'),
    (r'^speaker/(?P<id>[0-9]+)/$', 'scalereg.simple_cfp.review.views.Speaker'),
    (r'^status/$', 'scalereg.simple_cfp.review.views.StatusIndex'),
    (r'^status/(?P<status>[A-Za-z]+)/$', 'scalereg.simple_cfp.review.views.Status'),
)
