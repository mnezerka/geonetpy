"""
Tools for matching (comparing) geographic tracks

Issue 1 - scipy KD tree uses euclidean distance
* https://stackoverflow.com/questions/49266244/kdtree-is-returning-points-outside-of-radius
* https://pysal.org/libpysal/ -> possibility to use Arc + radius for KDTree
* https://stackoverflow.com/questions/10549402/kdtree-for-longitude-latitude
* https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.BallTree.html#sklearn.neighbors.BallTree

Tip with ball tree (note: Note this returns distances assuming a sphere of
radius 1 - to get the distances on the earth multiply by radius = 6371km):
```python
from sklearn.neighbors import BallTree
import numpy as np
import pandas as pd

cities = pd.DataFrame(data={
    'name': [...],
    'lat': [...],
    'lon': [...]
})

query_lats = [...]
query_lons = [...]

bt = BallTree(np.deg2rad(cities[['lat', 'lon']].values), metric='haversine')
distances, indices = bt.query(np.deg2rad(np.c_[query_lats, query_lons]))

nearest_cities = cities['name'].iloc[indices]
```


"""

import json
import logging
import scipy.spatial
import scipy.cluster.hierarchy
import numpy as np
from geopy import distance


def match(a, b, tolerance):
    """ Matching two GPX-tracks"""

    points_a = np.vstack(np.asarray(a))
    points_b = np.vstack(np.asarray(b))

    all_tracks = [points_a, points_b]
    logging.debug('shape a: %d', points_a.shape)
    logging.debug('shape b: %d', points_b.shape)

    all_points = np.vstack([np.hstack([points, np.full((points.shape[0], 1), i)]) for i, points in enumerate(all_tracks)])

    # Generate array of indexes/indices
    indexes = np.arange(len(all_points))

    # Combine indices and all points array (add index as 4th dimension)
    all_points = np.column_stack((all_points, indexes))
    logging.debug(all_points)

    # all_points has following structure now:
    # [
    #    [x, y, track_id, index]
    #    ...
    # ]

    logging.debug('all_pts (ix: coordinates):')
    for i, v in enumerate(all_points):
        logging.debug('%d: %s', i, v)

    tree = scipy.spatial.KDTree(all_points[:, :2])
    # tree = pysal.cg.KDTree(all_points[:, :2], distance_metric='Arc', radius=pysal.cg.RADIUS_EARTH_MILES)

    # note: [:, :2] removes third coordinate (label/index)
    # find nearest points (circle is given by tolerance) around each of the points
    points_within_tolerance = tree.query_ball_point(all_points[:, :2], tolerance)

    logging.debug("points_within_tolerance (point ix -> ix of points in tolearance):")
    for i, v in enumerate(points_within_tolerance):
        logging.debug('%d: %s', i, v)

    # previous returns an array of the same length as the incoming points,
    # with each value in the array being a tuple of indexes of the found
    # points in the tree. Because you put in our original set there will
    # always be at least one match. However you can then build a simple
    # vectorisation function to test whether each item in the tree matches
    # a point from a different group.

    vfunc = np.vectorize(lambda a: np.any(all_points[a, 2] != all_points[a[0], 2]))

    matches = vfunc(points_within_tolerance)

    logging.debug('matches (true if given point matches point in another track):')
    for i, v in enumerate(matches):
        logging.debug('%d: %s', i, v)

    # reduce all_points array to those who are True in matches array,
    # so the matching_points contain only points which match points in
    # second group (labeling/index coordinate is stripped -> :2)
    matching_points = all_points[matches, :2]

    logging.debug('matchiing points: %s', matching_points)

    # if there are no points close to each other -> tracks are too far from each other
    if len(matching_points) > 0:

        # So now you have points on the GPS trails which cross, but you want to
        # group points into contiguous segments of track that overlap. For that you
        # can use the scipy hierarchical clustering methods to group the data into
        # groups which are linked by at most the TOLERANCE distance.

        clusters = scipy.cluster.hierarchy.fclusterdata(matching_points, tolerance, 'distance')
    else:
        clusters = []

    logging.debug('clusters: %s', clusters)

    # clusters is an array of the same length of your matched points containing
    # cluster indexes for each point. This means it's easy to get back a table
    # of x, y, original_trail, segment by stacking the output together.

    cluster_points = np.hstack([
        matching_points,
        np.vstack([
            all_points[matches, 2],    # track index
            all_points[matches, 3],    # point index
            clusters
        ]).T
    ])

    logging.debug('cluster_points:')
    logging.debug(cluster_points)

    cluster_point_indexes = cluster_points[:, 3]

    def get_point_with_cluster_info(p):
        # look for point in clusters
        cluster_ix = np.nonzero(cluster_point_indexes == p[3])[0]

        # if point is member of some cluster, use it
        if cluster_ix.shape[0] > 0:
            return cluster_points[cluster_ix[0]]

        # if point was not found, add information that it doesn't belong to any cluster (-1)
        return np.append(p, -1)

    result = np.vstack([get_point_with_cluster_info(p) for p in all_points])

    logging.debug('result:')
    # (x, y, track_id, index, cluster)
    logging.debug(result)

    return result

def get_track_ratios(matches):
    """Compute single track ratio"""

    for track_ix in range(2):
        # prepare filter (boolean vector) to filter out current truack points
        tracks_filter = [m[2] == track_ix for m in matches]
        track_points = matches[tracks_filter]

        dist_outside_cluster = 0    # distance outside of clusters
        dist_total = 0      # distance total
        last_point = None

        for p_ix, p in enumerate(track_points):
            if p_ix == 0:
                last_point = p
                continue

            # calculating Euclidean distance using linalg.norm()
            # d = np.linalg.norm(np.array((p[0], p[1])) - np.array((last_point[0], last_point[1])))
            d = distance.distance([p[0], p[1]], [last_point[0], last_point[1]]).m
            dist_total += d

            # if we are outside of cluster
            if p[4] == -1:
                dist_outside_cluster += d

            last_point = p

        print('track', track_ix)
        print(f'  points: {track_points.shape[0]}')
        print(f'  distance total: {format_distance_m(dist_total)}')
        print(f'  distance outside of clusters: {format_distance_m(dist_outside_cluster)}')
        print(f'  match ratio:: {round(((dist_total - dist_outside_cluster) / dist_total * 100), 1)}%')

def points_from_gpx(gpx):
    """point from gpx object"""
    points = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append([point.latitude, point.longitude])

    return np.array(points)

def matches_to_geojson(matches):
    geos = []

    # get unique track ids
    track_ids = set(matches[:, 2].astype(int))

    for track_ix in track_ids:
        # prepare filter (boolean vector) to filter out current truack points
        track_filter = [m[2] == track_ix for m in matches]
        track_points = matches[track_filter]

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
    cluster_ids = {int(p[4]) for p in matches if p[4] != -1}

    for cluster_ix in cluster_ids:
        # prepare filter (boolean vector) to filter out current cluster points
        cluster_filter = [m[4] == cluster_ix for m in matches]
        cluster_points = matches[cluster_filter]
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

    return json.dumps(geometries, indent=4)

def format_distance_m(d):
    """format distance specified in meters"""

    result = f'{round(d, 1)} m'

    if d > 1000:
        result = f'{round(d/1000, 1)} km'

    return result
