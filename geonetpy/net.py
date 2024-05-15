import json
import logging
import numpy as np
from .geojson import point_to_geojson
from .balltree import BallTree

class Net:
    def __init__(self, points=None, edges=[]):
        self.max_spot_distance = 75
        self.last_id = 0
        self.edges = edges
        self.meta = {}
        if points is not None:
            self.balltree = BallTree(points)
            logging.debug('created net from existing data, max spot distance: %i', self.max_spot_distance)
        else:
            self.balltree = None
            logging.debug('created empty net, max spot distance: %i', self.max_spot_distance)

    def stat(self):
        return f'height of ball tree is: {self.balltree.get_height()}'

    def get_points(self):
        if self.balltree is None:
            return []

        return self.balltree.get_points()

    def get_edges(self):
        return self.edges

    def get_id(self):
        result = self.last_id
        self.last_id += 1
        return result

    def store_point(self, point):
        point_id = self.get_id()
        point = np.array([point[0], point[1], point_id])
        logging.debug('storing point: %s', point)

        if self.balltree is None:
            self.balltree = BallTree(np.array([point]))
        else:
            self.balltree.add_point(point)

        self.meta[point_id] = {
            'quantity': 1
        }

        return point

    def store_edge(self, edge):
        self.edges.append(edge)

    def add_point(self, point, last_point=None):
        logging.debug('add point: %s, last_point: %s', point, last_point[2] if last_point is not None else "-")

        # ball tree needs to be created with first point and no further processing is needed
        if self.balltree is None:
            return self.store_point(point)

        final_point = None

        # find nearest neighbor it returns array of tuples (distance, point, node index)
        # there must be always at least one item in result since tree is not empty
        nearest = self.balltree.query(point, k=1)
        logging.debug('nearest points: %s', nearest)
        assert len(nearest) > 0

        if nearest[0][0] < self.max_spot_distance:

            final_point = nearest[0][1]

            logging.debug('reusing existing point, which is %f m far, limit is %f m', nearest[0][0], self.max_spot_distance)
            # NOTE: possibility to store meta information somewhere - we have
            # an id of the ball tree point in nearest[0][1][2] place

            self.meta[final_point[2]]['quantity'] += 1

        else:
            #  no existing point was close enough -> create new one

            logging.debug('adding point as new: %s', point)
            final_point = self.store_point(point)

        # --------------------  edge processing
        if last_point is not None:
            last_point_id = int(last_point[2])
            final_point_id = int(final_point[2])

            # ignore self edges
            if last_point_id != final_point_id:
                # create edge with sorted point ids to avoid duplicates (reverse direction of track movement)
                edge = (last_point_id, final_point_id) if last_point_id < final_point_id else (final_point_id, last_point_id)
                # edge_id = f'{edge[0]}-{edge[1]}'
                if edge in self.edges:
                    logging.debug('reusing existing edge: %s', edge)
                    # self.meta[edge_id]['quantity'] += 1
                else:
                    logging.debug('adding edge: %s', edge)
                    self.store_edge(edge)
                    # self.meta[edge_id] = {'quantity': 1}

        return final_point

    def to_geojson(self):
        geos = []

        points = self.balltree.get_points()

        # render points and build dict of points for searching

        index = {}

        for point in points:

            pnt = {
                'type': 'Feature',
                'properties': {
                    'spot': int(point[2])
                },
                'geometry': {
                    'coordinates': point_to_geojson(point),
                    'type': 'Point'
                }
            }
            geos.append(pnt)

            index[int(point[2])] = point

        # render edges
        # build dict of points for searching
        for edge in self.edges:
            p1 = index[edge[0]]
            p2 = index[edge[1]]

            line = {
                'type': 'Feature',
                'properties': {
                    'edge': f'{edge}'
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
