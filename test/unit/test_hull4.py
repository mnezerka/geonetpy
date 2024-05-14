import unittest
from geonetpy.hull4 import Hull4, Vector
from geonetpy.rect import Rect

class TestHull4(unittest.TestCase):
    def test_fun(self):
        h = Hull4.from_vector(Vector(2, 7), 1)
        self.assertEqual([2, -2, 7, -7], h.bounds)

    def test_add(self):
        h1 = Hull4.from_vector(Vector(2, 7), 1)
        h2 = Hull4.from_vector(Vector(5, 4), 1)

        h = h1.add(h2)
        self.assertEqual([5, -2, 7, -4], h.bounds)

    def test_size(self):

        h1 = Hull4.from_vector(Vector(2, 1), 1)
        h2 = Hull4.from_vector(Vector(4, 6), 1)

        h = h1.add(h2)

        self.assertEqual(7., h.size())

    def test_bounding_rect(self):
        h1 = Hull4.from_vector(Vector(2, 1), 1)
        h2 = Hull4.from_vector(Vector(4, 6), 1)

        h = h1.add(h2)

        self.assertEqual([4, 6], h.bounding_rect().point1, "should add correctly")
        self.assertEqual([2, 1], h.bounding_rect().point2, "should add correctly")


if __name__ == '__main__':
    unittest.main()
