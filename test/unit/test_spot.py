import unittest
from geonetpy.spot import Spot, get_centroid

class TestSpot(unittest.TestCase):

    def test_centoid(self):
        c = get_centroid([[1, 1]])
        self.assertEqual([1, 1], c)

        c = get_centroid([[1, 1], [3, 3]])
        self.assertEqual([2, 2], c)

        c = get_centroid([[0, 0], [6, 0], [6, 3], [0, 3]])
        self.assertEqual([3, 1.5], c)

    def test_create(self):
        Spot(2, [1, 1])

    def test_distance(self):
        s = Spot(2, [1, 1])

        self.assertAlmostEqual(222355.978, s.distance([1, 3]), places=1)
        self.assertAlmostEqual(4336602.139, s.distance([40, 1]), places=1)

    def test_add(self):
        s = Spot(2, [1, 1])

        s.add([3, 3])

        self.assertEqual([1, 1], s.center)
