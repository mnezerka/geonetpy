import unittest
from geonetpy.netmem import NetMem

# sample points
POINTS = [
    [52.5200, 13.4050, 0],      # berlin
    [48.8566, 2.3522, 1],       # paris
    [40.7128, -74.0060, 2],     # new york
    [34.0522, -118.2437, 3]     # los angeles
]


class TestNetMem(unittest.TestCase):

    def test_create(self):

        NetMem()

        NetMem(POINTS)
