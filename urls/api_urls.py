# -*- coding: utf-8 -*- vim:encoding=utf-8:
from django.conf.urls import patterns, url
from mon_map.views import api

urlpatterns = patterns(
    '',
    url(r'^$', api.metro_map_json, name='metro-map'),
    url(r'^(?P<fake>f?)?links/(?P<from_node>[\w\d\-\.]+)/to/(?P<to_node>[\w\d\-\.]+)/$', api.link, name='link'),
    url(r'^links/(?P<from_node>[\w\d\-\.]+)/to/(?P<to_node>[\w\d\-\.]+)/separate/$', api.link, {'separate': True}, name='link-separate'),
    url(r'^load/(?P<from_node>[\w\d\-\.]+)/to/(?P<to_node>[\w\d\-\.]+)/$', api.link_load, name='load'),
    url(r'^load/$', api.load, name='load-total'),
    url(r'^bandwidth/$', api.bandwidth, name='bandwidth-total'),
)
