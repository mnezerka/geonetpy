import json
import logging
from .hull4 import Hull4, Vector
from .geojson import point_to_geojson

class Net:
    def __init__(self):
        self.hulls = {}
        self.sizeTreshold = 0.001
        self.last_id = 0
        self.edges = []
        logging.debug(f'created empty net, sizeTreshold={self.sizeTreshold}')

    def get_id(self):
        result = self.last_id
        self.last_id += 1
        return result

    def store_hull(self, hull):
        self.hulls[hull.id] = hull

    def store_edge(self, edge):
        self.edges.append(edge)

    def add_point(self, point, last_hull=None):
        logging.debug(f'add point: {point}, last_hull: {last_hull.id if last_hull else "-"}')

        new_hull = Hull4.from_vector(Vector.from_point(point), self.get_id())

        # look for existing hull which is close to the point
        final_hull = None
        for _, h in self.hulls.items():

            # try to join existing hull with the new point
            joined_size = h.estimate_size(new_hull)

            # if joined size is under threshold
            if joined_size < self.sizeTreshold:

                logging.debug(f'adding to existing hull {h.id}, size: {joined_size}')
                joined = h.copy()
                joined.add(new_hull)
                self.store_hull(joined)
                final_hull = joined
                break

        #  no existing hull was close enough -> store newly created one
        if final_hull is None:
            logging.debug(f'registering hull {new_hull.id}')
            self.store_hull(new_hull)
            final_hull = new_hull

        # --------------------  edge processing
        if last_hull is not None:
            # ignore edges between hull itself
            if last_hull.id != final_hull.id:
                edge = (last_hull.id, final_hull.id)
                if edge not in self.edges:
                    logging.debug(f'adding edge {last_hull.id} - {new_hull.id}')
                    self.store_edge(edge)

        return final_hull

    def to_geojson(self):
        geos = []

        # render hulls
        for _, h in self.hulls.items():

            r = h.bounding_rect()

            if h.size() == 0:

                rc = r.get_center()

                pnt = {
                    'type': 'Feature',
                    'properties': {
                        'hull': h.id
                    },
                    'geometry': {
                        'coordinates': point_to_geojson(rc),
                        'type': 'Point'
                    }
                }
                geos.append(pnt)

            else:

                poly = {
                    'type': 'Feature',
                    'properties': {
                        'hull': h.id
                    },
                    'geometry': {
                        'coordinates': [[point_to_geojson(p) for p in r.get_corner_points()]],
                        'type': 'Polygon'
                    }
                }
                geos.append(poly)

        # render edges
        for edge in self.edges:
            h1 = self.hulls[edge[0]]
            h2 = self.hulls[edge[1]]

            p1 = h1.bounding_rect().get_center()
            p2 = h2.bounding_rect().get_center()

            line = {
                'type': 'Feature',
                'properties': {
                    'edge': f'{h1.id}-{h2.id}'
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
