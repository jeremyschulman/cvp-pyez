from operator import itemgetter


NODE_USER_TAGS = ('datacenter', 'pod', 'rack')
NODE_TAGS = ('pod', 'rack')


def is_tagged(data):
    return (any(data.get(tag) for tag in NODE_TAGS) or
            all(data['userTags'].get(tag) for tag in NODE_TAGS))


def get_topology_edges(cvp):
    res = cvp.get('$n/topology/edges')
    edges = cvp.extracto_notifications(res.json(), extract='key')

    edge_map = dict()
    for edge in edges.values():
        edge_map[edge['from']] = edge['to']
        edge_map[edge['to']] = edge['from']

    return edge_map


def get_topology_nodes(cvp):
    res = cvp.get('$n/topology/nodes')
    return cvp.extracto_notifications(res.json())


def get_topology_node_tags(cvp):
    res = cvp.get('$n/topology/tags/nodes')
    return cvp.extracto_notifications(res.json())
