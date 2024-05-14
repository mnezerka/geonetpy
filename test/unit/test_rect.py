import unittest
from geonetpy.rect import Rect

class TestRect(unittest.TestCase):

    def test_create(self):
        Rect([0, 0], [1, 1])

    def test_get_center(self):
        r = Rect([1, 2], [11, 11])
        self.assertEqual([6, 6.5], r.get_center())

    def test_get_corner_points(self):
        pass

if __name__ == '__main__':
    unittest.main()
