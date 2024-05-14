import unittest
import numpy as np
from geonetpy.balltree import BallTree

# sample points
POINTS = [
    [52.5200, 13.4050, 0],      # berlin
    [48.8566, 2.3522, 1],       # paris
    [40.7128, -74.0060, 2],     # new york
    [34.0522, -118.2437, 3]     # los angeles
]


class TestBallTree(unittest.TestCase):

    def test_distance(self):

        # build  a Ball Tree
        tree = BallTree(np.array(POINTS))

        # query for nearest neighbors
        query_point = [34.0522, -118.2437]  # Example query point (Los Angeles)
        nearest = tree.query(query_point, k=2)

        self.assertEqual(2, len(nearest))
        self.assertEqual(3, nearest[0][1][2])  # lose angeles is nearest since it is point itself
        self.assertEqual(0, nearest[0][0])     # distance to lose angeles is 0
        self.assertEqual(2, nearest[1][1][2])  # new york is nearest from other cities
        self.assertAlmostEqual(3935746.254, nearest[1][0], places=2)     # distance to new york

    def test_adding(self):

        # sample points
        points = [[52.5200, 13.4050, 0]]   # berlin

        # build  a Ball Tree
        tree = BallTree(np.array(points))

        tree.add_point([48.8566, 2.3522, 1])     # paris
        tree.add_point([34.0522, -118.2437, 3])  # los angeles
        tree.add_point([40.7128, -74.0060, 2])   # new york

        # query for nearest neighbors
        query_point = [34.0522, -118.2437]       # example query point (Los Angeles)
        nearest = tree.query(query_point, k=2)

        self.assertEqual(2, len(nearest))
        self.assertEqual(2, nearest[1][1][2])                         # new york is nearest from other cities
        self.assertAlmostEqual(3935746.254, nearest[1][0], places=2)  # distance to new york

    def test_dump(self):

        tree = BallTree(np.array(POINTS))

        dump = tree.get_points()
        self.assertEqual(4, len(dump))
