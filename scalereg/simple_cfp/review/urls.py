from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'scalereg.simple_cfp.review.views.index'),
)
