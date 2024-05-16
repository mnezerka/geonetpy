import logging
from pymongo.mongo_client import MongoClient
import pymongo
from .net import Net

def mongo_loc_to_point(loc):

    c = loc['loc']['coordinates']
    return ([c[1], c[0], loc['index']])


class NetDb(Net):
    def __init__(self, uri):
        super().__init__()

        self.uri = uri
        self.client = MongoClient(self.uri)

        # send a ping to confirm a successful connection
        self.client.admin.command('ping')
        self.db = self.client.geonet

        # make collection empty
        self.db.places.drop()

        # create geospatial index
        self.db.places.create_index({'loc': pymongo.GEOSPHERE})

        print("Pinged your deployment. You successfully connected to MongoDB!")

    def stat(self):
        return 'netdb stat'

    def add_point(self, point, last_point=None):
        logging.debug('add point: %s, last_point: %s', point, last_point[2] if last_point is not None else "-")

        final_point = None

        # look for existing point to be reused
        nearest = self.db.places.find({
            'loc': {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [point[1], point[0]]  # Example query point (Los Angeles)
                    },
                    "$maxDistance": self.max_spot_distance}}})

        for loc in nearest:
            logging.debug('reusing point %s', point)

            self.meta[loc['index']]['q'] += 1

            final_point = mongo_loc_to_point(loc)
            break

        # if no near point exists, register new one
        if final_point is None:
            logging.debug('registring new point %s', point)
            point_geojson = {
                'loc': {
                    'type': 'Point',
                    'coordinates': [point[1], point[0]]
                },
                'index': self.generate_id()
            }
            self.db.places.insert_one(point_geojson)
            self.meta[point_geojson['index']] = {'q': 1}

            final_point = mongo_loc_to_point(point_geojson)

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
                    logging.debug('reusing existing edge: %s', edge_id)
                    self.meta[edge_id]['q'] += 1
                else:
                    logging.debug('adding edge: %s', edge_id)
                    self.edges.append(edge)
                    self.meta[edge_id] = {'q': 1}

        return final_point

    def get_points(self):
        all = self.db.places.find({})

        result = []
        for loc in all:
            result.append(mongo_loc_to_point(loc))

        return result
