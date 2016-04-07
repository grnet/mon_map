import rrdtool
import time
import os

from django.core.urlresolvers import reverse
from django.conf import settings

from network.models import Ifce
from rg.models import Graph
import gevent


def last_x_rec(x):
    return range(2, x + 1)


def get_load(ifce, start, end):
    if not start:
        start = str(int(time.time()) - 10000)
    if not end:
        end = str(int(time.time()) - 1000)
    datasources = ifce.get('datasources')
    if datasources:
        rrdfile = datasources
        for i in last_x_rec(3):
            # rrdtool hates unicode
            try:
                latest = rrdtool.fetch(
                    rrdfile,
                    'AVERAGE',
                    '-s %s' % start.encode('ascii', 'ignore'),
                    '-e %s' % end.encode('ascii', 'ignore')
                )[2][-i]
            except IndexError:
                # no rrds found
                return (0, 0, start, end)
            if latest[0] is None or latest[1] is None:
                loadin = 0
                loadout = 0
                continue
            else:
                loadin = latest[0]
                loadout = latest[1]
                break
        # Making sure our tuple does not contain Nones
        if ifce.get('bandwidth') == 0:
            ifce_in = '0'
            ifce_out = '0'
        else:
            ifce_in = '%s' % round(loadin * 800 / ifce.get('bandwidth'), 2)
            ifce_out = '%s' % round(loadout * 800 / ifce.get('bandwidth'), 2)
    else:
        ifce_in = '0'
        ifce_out = '0'
    return (ifce_in, ifce_out, start, end)


def get_load_for_interfaces(ifces, key, start=None, end=None):
    traffic_in = 0
    traffic_out = 0
    bandwidth = 0
    response = {}
    if ifces:
        for ifce in ifces:
            bandwidth += ifce.get('bandwidth')
            ifce_in, ifce_out, start, end = get_load(ifce, start, end)
            traffic_in += float(ifce_in)
            traffic_out += float(ifce_out)
        if ifces:
            traffic_in = traffic_in / len(ifces)
            traffic_out = traffic_out / len(ifces)
        response = {
            '%s' % key: {
                'bandwidth': bandwidth,
                'load': {
                    'in': traffic_in,
                    'out': traffic_out
                },
                'start': start,
                'end': end
            }
        }
    return response


def get_load_for_links(ifces, start=None, end=None):
    response = {}
    threads = []
    for key, val in ifces.iteritems():
        # response.update(get_load_for_interfaces(val, key, start, end))
        threads.append(gevent.spawn(get_load_for_interfaces, val, key, start, end))
    gevent.joinall(threads)
    for thread in threads:
        if thread.value:
            response.update(thread.value)
    return response


def graph_for_each_interface(graph, datasources, start='-1d', end='-300'):

    response = {'Total': graph.get_draw_url()}

    for i in range(0, len(datasources) / 2):
        dss = datasources[i * 2:i * 2 + 2]
        if dss:
            ifce = Ifce.objects.get(pk=dss[0].object_id)
            try:
                png = dss[0].graph_set.filter(type='traffic')[0].get_draw_url()
                mon = dss[0].graph_set.filter(type='traffic')[0].get_absolute_url()
            except IndexError:
                continue
            response.update({
                ifce.name: {
                    'png': png,
                    'link_to_mon': mon,
                }
            })
    return response


def create_graph_for_interfaces(datasources, start=None, end=None, **kwargs):
    if 'dryrun' in kwargs:
        dryrun = kwargs['dryrun']
    else:
        dryrun = False

    if not start:
        start = '-1d'
    if not end:
        end = '-100'
    if datasources:
        name = os.path.basename(datasources[0].rrdfile.path).split('.')
        if name[0]:
            name = name[0]
        else:
            name = name[1]
        title = '%s to %s' % (name.split('-')[0], name.split('-')[1])
        arguments = ['%s/%s%s%s.png' % (settings.RG_STATICPATH, name, start, end)]

        if hasattr(settings, 'RG_RRDCACHED'):
            arguments.append('--daemon=%s' % str(settings.RG_RRDCACHED))
        arguments.append('-s %s' % start)
        arguments.append('-e %s' % end)
        arguments.append('-t %s' % title)
        arguments.append('--slope-mode')
        arguments.append('-l 0')
        aggregate_dict = {'ds0': [], 'ds1': []}
        interfaces_dict = {
            'ds0': {
                'label': 'In ',
                'color': '#0000ff',
                'graph_type': 'AREA'
            },
            'ds1': {
                'label': 'Out',
                'color': '#00ff00',
                'graph_type': 'LINE'
            }
        }
        legend = []
        used_ds = []
        for d in datasources:
            if d.pk not in used_ds:
                arguments.append('DEF:d%s=%s:%s:AVERAGE' % (d.pk, d.rrdfile.path, d.name))
                arguments.append('DEF:%smax=%s:%s:MAX' % (d.pk, d.rrdfile.path, d.name))
                aggregate_dict[d.name].append(d.pk)
                arguments.append('CDEF:d%sdispAVG=d%s,8,*' % (d.pk, d.pk))
                used_ds.append(d.pk)
        arguments.append('COMMENT:\t\tMin\g')
        arguments.append('COMMENT:\tMax\g')
        arguments.append('COMMENT:\tAverage\g')
        arguments.append('COMMENT:\tCurrent\\n')
        for key, val in aggregate_dict.iteritems():
            arguments.append('CDEF:aggr%s=' % (key))
            legend.append('%s:aggr%s%s:%s' % (
                interfaces_dict.get(key).get('graph_type'), key, interfaces_dict.get(key).get('color'), interfaces_dict.get(key).get('label'))
            )
            for rrd in val:
                arguments[-1] += 'd%sdispAVG,' % rrd
                if rrd != val[0]:
                    arguments[-1] += 'ADDNAN,'
            legend.append('%s:aggr%s:%s:%s' % ('GPRINT', key, 'MIN', '\t%4.2lf%s\g'))
            legend.append('%s:aggr%s:%s:%s' % ('GPRINT', key, 'MAX', '\t%4.2lf%s\g'))
            legend.append('%s:aggr%s:%s:%s' % ('GPRINT', key, 'AVERAGE', '\t%4.2lf%s\g'))
            legend.append('%s:aggr%s:%s:%s' % ('GPRINT', key, 'LAST', '\t%4.2lf%s\\n'))
        arguments.extend(legend)
        args = [str(val) for val in arguments]

        if dryrun == True:
            import re
            for ri in range(len(args)):
                if args[ri].find('-') == 0 and \
                        len(args[ri].split()) > 2:
                    larg = args[ri].split()
                    larg[1] = "'" + larg[1]
                    larg[-1] = larg[-1] + "'"
                    args[ri] = ' '.join(larg)
                elif bool(re.search(r'^([CV]?DEF|AREA|GPRINT|COMMENT|HRULE):',
                                    args[ri])):
                    args[ri] = "'%s'" % args[ri]
            return ' \n'.join('rrdtool graph'.split() + args)
        else:
            rrdtool.graphv(*args)

        url = reverse(
            'get-png-data',
            kwargs={
                'path': '%s%s%s.png' % (name, start, end)
            }
        )
        return url
    return False


def create_links_dict(links):
    ifces = {}
    for link in links:
        try:
            if ifces.get(
                '%s_%s' % (
                    link.local_ifce.node.name, link.remote_ifce.node.name
                )
            ):
                name = '%s_%s' % (link.local_ifce.node.name, link.remote_ifce.node.name)
                prev = ifces.get(name)
                prev.append(link.local_ifce.as_dict())
                ifces.update({
                    '%s_%s' % (
                        link.local_ifce.node.name, link.remote_ifce.node.name
                    ): prev
                })
            else:
                ifces.update({
                    '%s_%s' % (
                        link.local_ifce.node.name, link.remote_ifce.node.name
                    ): [link.local_ifce.as_dict()]
                })
        except:
            continue
    return ifces


def get_graph_for_node_link(local, remote, separate=False):

    response = []

    try:
        graph = Graph.objects.get(
            type='n2ntraffic',
            description__contains='%s - %s' % (local, remote)
        )
    except:
        graph = None

    if graph:
        if separate:
            # '-1d', '-300' now need to be fixed values as we are not creating
            # the graphs, only getting the ones that rg creates with those
            # default values
            response = graph_for_each_interface(
                graph, graph.datasources.all(), '-1d', '-300')
        else:
            response = {
                'graph': graph.get_draw_url(),
                'links': [{"from_descr": graph.description}]
            }

    else:
        response = {'graph': False, 'links': []}
    return response
