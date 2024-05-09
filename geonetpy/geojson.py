"""
Geojson tools
"""

import json

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

    return(json.dumps(geometries, indent=4))


def matches_to_geojson(matches):
    geos = []

    # get unique track ids
    track_ids = set(matches[:, 2].astype(int))

    for track_ix in track_ids:
        # prepare filter (boolean vector) to filter out current truack points
        filter = [m[2] == track_ix for m in matches]
        track_points = matches[filter]

        poly = {
            'type': 'Feature',
            'properties': {
                'track': int(track_ix)
            },
            'geometry': {
                'coordinates': [[p[1], p[0]] for p in track_points],
                'type': 'LineString'
            },
        }
        geos.append(poly)

        for track_pt in track_points:

            pt = {
                'type': 'Feature',
                'properties': {
                    'track': int(track_ix)
                },
                'geometry': {
                    'coordinates': [track_pt[1], track_pt[0]],
                    'type': 'Point'
                },
            }
            geos.append(pt)

    # get unique cluster ids
    cluster_ids = set([int(p[4]) for p in matches if p[4] != -1])

    for cluster_ix in cluster_ids:
        # prepare filter (boolean vector) to filter out current cluster points
        filter = [m[4] == cluster_ix for m in matches]
        cluster_points = matches[filter]
        for cluster_pt in cluster_points:

            pt = {
                'type': 'Feature',
                'properties': {
                    'cluster': int(cluster_ix)
                },
                'geometry': {
                    'coordinates': [cluster_pt[1], cluster_pt[0]],
                    'type': 'Point'
                },
            }
            geos.append(pt)

    geometries = {
        'type': 'FeatureCollection',
        'features': geos,
    }

    return(json.dumps(geometries, indent=4))
