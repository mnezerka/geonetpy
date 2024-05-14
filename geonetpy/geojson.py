"""
Geojson tools
"""

import json

def point_to_geojson(point):
    """https://macwright.com/lonlat/"""
    return [point[1], point[0]]


def points_to_geojson(points, line=False):
    geos = []

    for point in points:

        pt = {
            'type': 'Feature',
            'properties': {
                'track': 0
            },
            'geometry': {
                'coordinates': [point[1], point[0]],
                'type': 'Point'
            },
        }
        geos.append(pt)

    if line:
        poly = {
            'type': 'Feature',
            'properties': {
                'track': 0
            },
            'geometry': {
                'coordinates': [[p[1], p[0]] for p in points],
                'type': 'LineString'
            },
        }
        geos.append(poly)

    geometries = {
        'type': 'FeatureCollection',
        'features': geos,
    }

    return json.dumps(geometries, indent=4)
