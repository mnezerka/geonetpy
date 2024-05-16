"""
Geojson tools
"""

import json

def point_to_geojson(point):
    """https://macwright.com/lonlat/"""
    return [point[1], point[0]]


def tracks_to_geojson(tracks, lines=False):
    geos = []

    for track_ix, points in enumerate(tracks):

        for point in points:

            pt = {
                'type': 'Feature',
                'properties': {
                    'track': track_ix
                },
                'geometry': {
                    'coordinates': point_to_geojson(point),
                    'type': 'Point'
                },
            }
            geos.append(pt)

        if lines:
            line = {
                'type': 'Feature',
                'properties': {
                    'track': track_ix
                },
                'geometry': {
                    'coordinates': [point_to_geojson(p) for p in points],
                    'type': 'LineString'
                },
            }
            geos.append(line)

    geometries = {
        'type': 'FeatureCollection',
        'features': geos,
    }

    return json.dumps(geometries, indent=4)

def net_to_geojson(self, net, show_points=True, show_edges=True):
    geos = []

    points = net.get_points()

    index = {}

    # render edges and build dict of points for searching
    for point in points:

        if show_points:
            point_id = num2id(point[2])
            point_meta = self.meta[point_id]

            pnt = {
                'type': 'Feature',
                'properties': {
                    'spot': point_id,
                    'q': point_meta['q']
                },
                'geometry': {
                    'coordinates': point_to_geojson(point),
                    'type': 'Point'
                }
            }
            geos.append(pnt)

        index[int(point[2])] = point

    # render edges
    if show_edges:

        for edge in net.get_edges():
            p1 = index[edge[0]]
            p2 = index[edge[1]]
            edge_id = f'{edge[0]}-{edge[1]}'
            line = {
                'type': 'Feature',
                'properties': {
                    'edge': edge_id,
                    'q': self.meta[edge_id]['q']
                },
                'geometry': {
                    'coordinates': [point_to_geojson(p1), point_to_geojson(p2)],
                    'type': 'LineString'
                }
            }
            geos.append(line)

    geometries = {
        'type': 'FeatureCollection',
        'features': geos,
    }

    return json.dumps(geometries, indent=4)
