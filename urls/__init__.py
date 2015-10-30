# -*- coding: utf-8 -*- vim:encoding=utf-8:
from django.conf.urls.defaults import include, patterns
# from maps.urls import api_urls
from maps.urls import maps_urls

urlpatterns = patterns(
    'maps.views',
    (r'^', include(maps_urls, namespace='maps')),
)
