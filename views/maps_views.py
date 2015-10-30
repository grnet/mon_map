from django.shortcuts import render
from django.core.urlresolvers import reverse


def metro_map(request):
    map_type = request.GET.get('type')
    # if raw=true then we just display the svgs.
    if request.GET.get('raw', False):
        if map_type == 'network':
            return render(request, 'maps/metro_map.html', {'url': False, 'svg': 'networkmap'})
        else:
            return render(request, 'maps/metro_map.html', {'url': False, 'svg': 'metromap'})

    url = reverse('api:metro-map')
    if map_type == 'network':
        url += '?path=networkmap'
    return render(request, 'maps/metro_map.html', {'url': url})
