import json

class Net:
    def __init__(self, points=None, edges=[]):
        self.max_spot_distance = 75
        self.last_id = 0
        self.edges = edges

        # meta information
        self.meta = {}

        self.add_points(points)

    def stat(self):
        return ''

    def get_points(self):
        return []

    def get_edges(self):
        return []

    def generate_id(self):
        result = self.last_id
        self.last_id += 1
        return result

    def add_points(self, points):
        pass

    def add_point(self, point, last_point=None):
        return None

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
