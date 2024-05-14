import unittest
from geonetpy.balltree import BallTree

class TestBallTree(unittest.TestCase):

    def test_distance(self):

        # sample points
        points = [
            [52.5200, 13.4050, 'berlin'],
            [48.8566, 2.3522, 'paris'],
            [40.7128, -74.0060, 'new york'],
            [34.0522, -118.2437, 'los angeles']
        ]

        # build  a Ball Tree
        tree = BallTree(points)

        # query for nearest neighbors
        query_point = [34.0522, -118.2437]  # Example query point (Los Angeles)
        nearest = tree.query(query_point, k=2)
        print('create', nearest)

        # self.assertEqual([1, 1], c)

    def test_adding(self):

        # sample points
        points = [[52.5200, 13.4050, 'berlin']]
        # build  a Ball Tree
        tree = BallTree(points)

        tree.add_point([48.8566, 2.3522, 'paris'])
        tree.add_point([34.0522, -118.2437, 'los angeles'])
        tree.add_point([40.7128, -74.0060, 'new york'])

        # query for nearest neighbors
        query_point = [34.0522, -118.2437]  # Example query point (Los Angeles)
        nearest = tree.query(query_point, k=2)
        print('adding', nearest)

    def test_dump(self):

        # sample points
        points = [
            [52.5200, 13.4050, 'berlin'],
            [48.8566, 2.3522, 'paris'],
            [40.7128, -74.0060, 'new york'],
            [34.0522, -118.2437, 'los angeles']
        ]

        # build  a Ball Tree
        tree = BallTree(points)

        print('dump', tree.get_points())
