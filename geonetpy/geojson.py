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
