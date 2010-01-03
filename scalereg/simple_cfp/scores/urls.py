from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scalereg.simple_cfp.scores.views.index'),
    (r'^(?P<id>[0-9]+)/$', 'scalereg.simple_cfp.scores.views.ReviewPresentation'),
    (r'^audience/$', 'scalereg.simple_cfp.scores.views.AudienceIndex'),
    (r'^audience/(?P<id>[0-9]+)/$', 'scalereg.simple_cfp.scores.views.Audience'),
    (r'^category/$', 'scalereg.simple_cfp.scores.views.CategoryIndex'),
    (r'^category/(?P<id>[0-9]+)/$', 'scalereg.simple_cfp.scores.views.Category'),
    (r'^speaker/$', 'scalereg.simple_cfp.scores.views.SpeakerIndex'),
    (r'^speaker/(?P<id>[0-9]+)/$', 'scalereg.simple_cfp.scores.views.Speaker'),
    (r'^status/$', 'scalereg.simple_cfp.scores.views.StatusIndex'),
    (r'^status/(?P<status>[A-Za-z]+)/$', 'scalereg.simple_cfp.scores.views.Status'),
)
