from xml.dom import minidom
from django.core.urlresolvers import reverse
from django.conf import settings


def get_attributes(el):
    attrs = {}
    for i in el.attributes.items():
        if i[0][:2] != 'v:':
            attrs.update({i[0]: el.getAttribute(i[0])})
    return attrs


class Shape():
    def __init__(self, shape_type, attrs):
        self.type = shape_type
        self.attrs = attrs


class Host():
    def __init__(self, hostname, layer, transform, shape):
        self.hostname = hostname
        self.layer = layer
        self.shape = shape
        self.transform = transform


class Tag():
    def __init__(self, transform, shape):
        self.shape = shape
        self.transform = transform


class Link():
    def __init__(self, path_from, path_to, layer, transform, shape):
        self.url = reverse(
            'api:link',
            kwargs=(
                {'from_node': path_from, 'to_node': path_to}
            )
        )
        self.load_url = reverse(
            'api:load',
            kwargs=(
                {'from_node': path_from, 'to_node': path_to}
            )
        )
        self.layer = layer
        self.shape = shape
        self.transform = transform
        self.path_from = path_from
        self.path_to = path_to


def strip_vt4(string):
    return string.replace('VT4(', '')[:-1]


def parse_map(map_path='metromap'):
    map_path = '%s/images/%s.svg' % (settings.STATIC_ROOT, map_path)
    doc = minidom.parse(map_path)
    svg = doc.getElementsByTagName('svg')[0]
    viewbox = svg.getAttribute('viewBox')
    width = svg.getAttribute('width')
    css_class = svg.getAttribute('class')
    height = svg.getAttribute('height')
    style = doc.getElementsByTagName('style')[0].toxml().replace('<![CDATA[', '').replace(']]>', '')
    root = doc.getElementsByTagName('g')[0]
    title = root.getElementsByTagName('title')[0].childNodes[0].data

    hosts = []
    links = []
    layers = {}
    labels = []
    svg_tags = []

    # create layer dict
    for l in root.getElementsByTagName('v:layer'):
        layers.update({l.getAttribute('v:index'): l.getAttribute('v:name')})

    # parse elements
    for g in root.getElementsByTagName('g'):
        hidden = False
        try:
            layer = layers[g.getAttribute('v:layerMember')]
        except:
            layer = layers['1']
        is_host = False
        if g.getElementsByTagName('v:custProps'):
            try:
                cprops = g.getElementsByTagName('v:custProps')[0].getElementsByTagName('v:cp')
            except:
                continue
            for custom_property in cprops:
                if custom_property.getAttribute('v:lbl').lower() == 'hidden':
                    hidden = True
                    break
                if custom_property.getAttribute('v:lbl').lower() == 'from':
                    path_from = strip_vt4(custom_property.getAttribute('v:val'))
                elif custom_property.getAttribute('v:lbl').lower() == 'to':
                    path_to = strip_vt4(custom_property.getAttribute('v:val'))
                else:
                    hostname = strip_vt4(custom_property.getAttribute('v:val'))
                    if hostname and g.getElementsByTagName('ellipse'):
                        is_host = True
                        shape = Shape('ellipse', get_attributes(g.getElementsByTagName('ellipse')[0]))
                        hosts.append(Host(hostname, layer, g.getAttribute('transform'), shape))
            if not is_host and not hidden:
                # we have a link here
                shape = Shape('path', get_attributes(g.getElementsByTagName('path')[0]))
                links.append(Link(path_from, path_to, layer, g.getAttribute('transform'), shape))
        elif g.getAttribute('id') == u'shape44-28':
            shape = Shape('path', get_attributes(g.getElementsByTagName('path')[0]))
            svg_tags.append(Tag(g.getAttribute('transform'), shape))
        elif g.getElementsByTagName('desc'):
            pass
        elif g.getElementsByTagName('text'):
            labels.append({
                'x': g.getElementsByTagName('text')[0].getAttribute('x'),
                'transform': g.getAttribute('transform'),
                'y': g.getElementsByTagName('text')[0].getAttribute('y'),
                'title': g.getElementsByTagName('text')[0].lastChild.toxml()
            })

    response = {
        'svg': {
            'style': style,
            'attrs': {
                'viewbox': viewbox,
                'width': width,
                'height': height
            },
            'title': title,
            'css_class': css_class,
        },
        'hosts': {},
        'links': [],
        'labels': labels,
        'svg_tags': [],
    }

    for host in hosts:
        response['hosts'].update({
            host.hostname: {
                'shape': host.shape.type,
                'shape_attrs': host.shape.attrs,
                'layer': host.layer,
                'transform': host.transform
            }
        })
    for link in links:
        response['links'].append({
            'shape': link.shape.type,
            'shape_attrs': link.shape.attrs,
            'layer': link.layer,
            'transform': link.transform,
            'url': link.url,
            'load_url': link.load_url,
            'from': link.path_from,
            'to': link.path_to,
        })
    for tag in svg_tags:
        response['svg_tags'].append({
            'shape': tag.shape.type,
            'shape_attrs': tag.shape.attrs,
            'transform': tag.transform,
        })
    return response
