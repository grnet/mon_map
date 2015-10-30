# -*- coding: utf-8 -*- vim:encoding=utf-8:
from django.conf.urls.defaults import include, patterns
# from maps.urls import api_urls
from mon_map.urls import maps_urls

urlpatterns = patterns(
    'mon_map.views',
    (r'^', include(maps_urls, namespace='maps')),
)
