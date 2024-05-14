import json
import logging
from .geojson import point_to_geojson
from .spot import Spot
from .geoutils import haversine_distance

class Net:
    def __init__(self):
        self.spots = {}
        self.max_spot_distance = 15
        self.last_id = 0
        self.edges = []
        logging.debug(f'created empty net, max spot distance: {self.max_spot_distance}')

    def get_id(self):
        result = self.last_id
        self.last_id += 1
        return result

    def store_spot(self, spot):
        self.spots[spot.id] = spot

    def store_edge(self, edge):
        self.edges.append(edge)

    def add_point(self, point, last_spot=None):
        logging.debug(f'add point: {point}, last_spot: {last_spot.id if last_spot else "-"}')

        # find nearest neighbor
        final_spot = None
        for _, s in self.spots.items():

            if s.distance(point) < self.max_spot_distance:

                logging.debug(f'adding to existing spot {s.id}')
                s.add(point)
                final_spot = s
                break

        #  no existing spot was close enough -> create new one
        if final_spot is None:
            final_spot = Spot(self.get_id(), point)
            logging.debug(f'registering new spot {final_spot.id}')
            self.store_spot(final_spot)

        # --------------------  edge processing
        if last_spot is not None:
            # ignore edges between spot itself
            if last_spot.id != final_spot.id:
                edge = (last_spot.id, final_spot.id)
                edge_reverse = (final_spot.id, last_spot.id)
                if edge not in self.edges and edge_reverse not in self.edges:
                    logging.debug(f'adding edge {last_spot.id} - {final_spot.id}')
                    self.store_edge(edge)

        return final_spot

    def to_geojson(self):
        geos = []

        # render hulls
        for _, s in self.spots.items():

            pnt = {
                'type': 'Feature',
                'properties': {
                    'spot': s.id
                },
                'geometry': {
                    'coordinates': point_to_geojson(s.center),
                    'type': 'Point'
                }
            }
            geos.append(pnt)

        # render edges
        for edge in self.edges:
            s1 = self.spots[edge[0]]
            s2 = self.spots[edge[1]]

            line = {
                'type': 'Feature',
                'properties': {
                    'edge': f'{s1.id}-{s2.id}'
                },
                'geometry': {
                    'coordinates': [point_to_geojson(s1.center), point_to_geojson(s2.center)],
                    'type': 'LineString'
                }
            }
            geos.append(line)

        geometries = {
            'type': 'FeatureCollection',
            'features': geos,
        }

        return json.dumps(geometries, indent=4)
