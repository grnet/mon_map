# -*- coding: utf-8 -*- vim:encoding=utf-8:
from django.conf.urls import patterns, url

from mon_map.views import maps_views

urlpatterns = patterns(
    '',
    url(r'^$', maps_views.metro_map, name='metro-map'),
)
