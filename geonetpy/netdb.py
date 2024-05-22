import json
import logging
from pymongo.mongo_client import MongoClient
import pymongo

def mongo_loc_to_point(loc):

    c = loc['loc']['coordinates']
    return ([c[1], c[0], loc['index']])

def remove_att_from_list(lst, att):
    return [{k: v for k, v in item.items() if k != att} for item in lst]

class NetDb:
    def __init__(self, uri):

        self.max_spot_distance = 75
        self.last_id = 0

        self.uri = uri
        self.client = MongoClient(self.uri)

        # send a ping to confirm a successful connection
        self.client.admin.command('ping')
        self.db = self.client.geonet

        # make collection empty
        self.db.tracks.drop()
        self.db.points.drop()
        self.db.edges.drop()

        # create geospatial index
        self.db.points.create_index({'loc': pymongo.GEOSPHERE})

        print("Pinged your deployment. You successfully connected to MongoDB!")

    def generate_id(self):
        result = self.last_id
        self.last_id += 1
        return result

    def get_meta(self):
        return {
            'tracks': remove_att_from_list(self.db.tracks.find({}), "_id")
        }

    def add_track(self, points, track_id, track_meta=None):

        if track_meta is None:
            track_meta = {}

        logging.debug('registring new track: %s, %s', track_id, track_meta)
        track_meta['id'] = track_id
        self.db.tracks.insert_one(track_meta)

        last_point_id = None
        for point in points:
            last_point_id = self.add_point(point, track_id, last_point_id)

    def add_point(self, point, track_id, last_point_id=None):
        logging.debug('add point: %s, track_id=%s, last_point_id: %s', point, track_id, last_point_id if last_point_id is not None else "-")

        final_point_id = None

        # look for existing point to be reused
        nearest = self.db.points.find({
            'loc': {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [point[1], point[0]]  # Example query point (Los Angeles)
                    },
                    "$maxDistance": self.max_spot_distance}}})

        for loc in nearest:
            logging.debug('reusing point %s (%s)', loc['index'], point)
            update = {
                'q': loc['q'] + 1
            }

            if track_id not in loc['tracks']:
                update['tracks'] = loc['tracks'].copy()
                update['tracks'].append(track_id)

            self.db.points.update_one({'_id': loc['_id']}, {'$set': update})

            final_point_id = loc['index']
            break

        # if no near point exists, register new one
        if final_point_id is None:
            final_point_id = self.generate_id()

            logging.debug('registring new point %s track_id=%s (%s)', final_point_id, track_id, point)
            loc = {
                'loc': {
                    'type': 'Point',
                    'coordinates': [point[1], point[0]]
                },
                'index': final_point_id,
                'tracks': [track_id],
                'q': 1
            }
            self.db.points.insert_one(loc)

        # --------------------  edge processing
        if last_point_id is not None:

            # ignore self edges
            if last_point_id != final_point_id:
                # create edge with sorted point ids to avoid duplicates (reverse direction of track movement)
                edge_points = (last_point_id, final_point_id) if last_point_id < final_point_id else (final_point_id, last_point_id)
                edge_id = f'{edge_points[0]}-{edge_points[1]}'
                edge = {
                    'index': edge_id,
                    'p1': edge_points[0],
                    'p2': edge_points[1],
                    'tracks': [track_id],
                    'q': 1
                }

                existing = self.db.edges.find_one({'index': edge_id})

                if existing is not None:
                    logging.debug('reusing existing edge: %s', existing['index'])

                    update = {
                        'q': loc['q'] + 1
                    }

                    if track_id not in existing['tracks']:
                        update['tracks'] = existing['tracks'].copy()
                        update['tracks'].append(track_id)

                    self.db.edges.update_one({'_id': existing['_id']}, {'$set': update})

                else:
                    logging.debug('registering new edge: %s', edge_id)
                    self.db.edges.insert_one(edge)

        return final_point_id

    def get_points(self):
        all_points = self.db.points.find({})

        result = []
        for loc in all_points:
            result.append(mongo_loc_to_point(loc))

        return result

    def save(self, filepath, output_format='gnt', show_points=True):

        logging.info("saving net content to %s (output_format: %s)", filepath, output_format)

        if output_format == 'js':
            content = {
                'geojson': self.to_geojson(show_points=show_points),
                'meta': {
                    'tracks': remove_att_from_list(self.db.tracks.find({}), "_id")
                }
            }

            with open(filepath, 'w', encoding='utf-8') as output_file:
                output_file.write('geonet=' + json.dumps(content, indent=4))

            logging.info("saved")

        else:
            content = {
                'points': remove_att_from_list(self.db.points.find({}), "_id"),
                'edges': remove_att_from_list(self.db.edges.find({}), "_id"),
                'tracks': remove_att_from_list(self.db.tracks.find({}), "_id")
            }

            with open(filepath, 'w', encoding='utf-8') as output_file:
                json.dump(content, output_file)

            logging.info("saved (points: %d, edges: %d, tracks: %d)", len(content['points']), len(content['edges']), len(content['tracks']))

    def load(self, filepath):

        with open(filepath, encoding='utf-8') as json_file:

            logging.info("loading net content from %s", filepath)

            data = json.load(json_file)

            # make collection empty
            self.db.tracks.drop()
            self.db.points.drop()
            self.db.edges.drop()

            # insert into collections
            self.db.points.insert_many(data['points'])
            self.db.edges.insert_many(data['edges'])
            self.db.tracks.insert_many(data['tracks'])

            # find last id
            max_point = self.db.points.find_one(sort=[('index', pymongo.DESCENDING)])
            if max_point is not None:
                self.last_id = max_point['index']
            else:
                self.last_id = 0

            logging.debug('last index set to %d', self.last_id)

    def simplify(self):

        # reset process flag for each edge
        self.db.edges.update({}, {'$set': {'proc': False}})

        # loop over not processed edges
        simplified = False
        while not simplified:
            pass

    def to_geojson(self, show_points=True, show_edges=True):
        geos = []

        index = {}

        # render points and build dict of points for searching when
        # rendering edges
        points = self.db.points.find({})
        for point in points:

            point_id = point['index']

            if show_points:

                pnt = {
                    'type': 'Feature',
                    'properties': {
                        'spot': point_id,
                        'q': point['q']
                    },
                    'geometry': {
                        'coordinates': point['loc']['coordinates'],
                        'type': 'Point'
                    }
                }
                geos.append(pnt)

            index[point_id] = point

        # render edges
        if show_edges:
            edges = self.db.edges.find({})

            for edge in edges:
                p1 = index[edge['p1']]    # p1 index -> p1 data
                p2 = index[edge['p2']]    # p2 index -> p2 data
                line = {
                    'type': 'Feature',
                    'properties': {
                        'edge': edge['index'],
                        'tracks': edge['tracks'],
                        'q': edge['q']
                    },
                    'geometry': {
                        'coordinates': [p1['loc']['coordinates'], p2['loc']['coordinates']],
                        'type': 'LineString'
                    }
                }
                geos.append(line)

        geometries = {
            'type': 'FeatureCollection',
            'features': geos,
        }

        # return json.dumps(geometries, indent=4)
        return geometries
