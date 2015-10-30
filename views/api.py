# -*- coding: utf-8 -*- vim:encoding=utf-8:
import json
from django.http import HttpResponse
from django.core.cache import cache
from network.models import Links
from utils import (
    create_graph_for_interfaces,
    graph_for_each_interface,
    get_load_for_links,
    create_links_dict
)
from svg_utils import parse_map


def metro_map_json(request):
    path = request.GET.get('path', 'metromap')
    response = json.dumps(parse_map(map_path=path))
    return HttpResponse(response, content_type='application/json')


def link_load(request, from_node, to_node):
    start = request.GET.get('start', None)
    end = request.GET.get('end', None)
    links = Links.objects.filter(
        local_ifce__node__name=from_node,
        remote_ifce__node__name=to_node
    )
    ifces = create_links_dict(links)
    if start and end:
        result = get_load_for_links(ifces, start, end)
    else:
        result = get_load_for_links(ifces)
    return HttpResponse(json.dumps(result), content_type='application/json')


def bandwidth(request):
    ifces = cache.get('bandwidth')
    if not ifces:
        links = Links.objects.exclude(remote_ifce_id=0).select_related(
            'local_ifce',
            'remote_ifce'
        )
        ifces = {}
        for link in links:
            try:
                if ifces.get(
                    '%s_%s' % (
                        link.local_ifce.node.name, link.remote_ifce.node.name
                    )
                ):
                    ifces.update({
                        '%s_%s' % (
                            link.local_ifce.node.name,
                            link.remote_ifce.node.name
                        ): ifces.get(
                            '%s_%s' % (
                                link.local_ifce.node.name, link.remote_ifce.node.name
                            )
                        ) + link.local_ifce.bandwidth
                    })
                else:
                    ifces.update({
                        '%s_%s' % (
                            link.local_ifce.node.name, link.remote_ifce.node.name
                        ): link.local_ifce.bandwidth
                    })
            except Exception:
                pass
        ifces = json.dumps(ifces)
        cache.set('bandwidth', ifces)
    return HttpResponse(ifces, content_type='application/json')


def load(request):
    start = request.GET.get('start', None)
    end = request.GET.get('end', None)
    result = cache.get('load_%s_%s' % (start, end))
    if not result:
        links = Links.objects.exclude(remote_ifce_id=0).select_related(
            'local_ifce',
            'remote_ifce',
            'remote_ifce__node',
            'local_ifce__node'
        )
        ifces = create_links_dict(links)
        if start and end:
            result = get_load_for_links(ifces, start, end)
        else:
            result = get_load_for_links(ifces)
        result = json.dumps(result)
        cache.set('load_%s_%s' % (start, end), result)
    return HttpResponse(result, content_type='application/json')


def link(request, from_node, to_node, separate=False):
    start = request.GET.get('start', None)
    end = request.GET.get('end', None)
    links = Links.objects.filter(
        local_ifce__node__name=from_node,
        remote_ifce__node__name=to_node
    )
    if links:
        response = []
        datasources = []
        for link in links:
            res = link.as_dict()
            response.append(res)
            # get the datasources in order to create the graphs
            ds = link.local_ifce.get_datasources(type='traffic')
            # try to get all available datasources
            if not ds:
                ds = link.remote_ifce.get_datasources(type='traffic')
            datasources.append(ds)
        datasources = [val for sublist in datasources for val in sublist]
        if not separate:
            if start and end:
                url = create_graph_for_interfaces(datasources, start, end) or False
            else:
                url = create_graph_for_interfaces(datasources) or False
            result = {'links': response, 'graph': url}
        else:
            if start and end:
                urls = graph_for_each_interface(datasources, start, end)
            else:
                urls = graph_for_each_interface(datasources)
            result = urls
    else:
        result = {'links': [], 'graph': False}
    return HttpResponse(json.dumps(result), content_type='application/json')
