import json
import logging
from .geojson import point_to_geojson
from .balltree import BallTree

def num2id(val):
    return str(int(val))

class NetMem:
    def __init__(self, points=None, edges=[]):
        self.max_spot_distance = 75
        self.last_id = 0
        self.edges = edges

        # meta information
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

    def generate_id(self):
        result = self.last_id
        self.last_id += 1
        return result

    def store_point(self, point):
        point_id = self.generate_id()
        point = [point[0], point[1], point_id]
        logging.debug('storing point: %s', point)

        if self.balltree is None:
            self.balltree = BallTree([point])
        else:
            self.balltree.add_point(point)

        self.meta[num2id(point_id)] = {
            'q': 1
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

            self.meta[num2id(final_point[2])]['q'] += 1

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
                edge_id = f'{edge[0]}-{edge[1]}'
                if edge in self.edges:
                    logging.debug('reusing existing edge: %s', edge)
                    self.meta[edge_id]['q'] += 1
                else:
                    logging.debug('adding edge: %s', edge)
                    self.store_edge(edge)
                    self.meta[edge_id] = {'q': 1}

        return final_point

    def save(self, filepath):
        content = {
            'points': [[p[0], p[1], int(p[2])] for p in self.get_points()],
            'edges': self.edges,
            'meta': self.meta
        }

        with open(filepath, 'w') as json_file:
            json.dump(content, json_file)

    def load(self, filepath):

        with open(filepath) as json_file:
            data = json.load(json_file)
            self.meta = data['meta']
            self.edges = data['edges']
            # set last_id to max of ids in points
            self.balltree = BallTree(data['points'])

    def to_geojson(self, show_points=True, show_edges=True):
        geos = []

        points = self.balltree.get_points()

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

            for edge in self.edges:
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
