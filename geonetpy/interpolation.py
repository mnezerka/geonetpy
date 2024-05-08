"""
Tools for adding points to existing geographic tracks
"""

import math
from geopy import distance
import numpy as np

# Constants
earth_radius_meters = 6378160
one_degree = (2 * math.pi * earth_radius_meters) / 360  # 111.319 km

# Bearing calculation
def bearing(point1, point2):
    lat1r = math.radians(point1[0])
    lat2r = math.radians(point2[0])
    dlon = math.radians(point2[1] - point1[1])

    y = math.sin(dlon) * math.cos(lat2r)
    x = math.cos(lat1r) * math.sin(lat2r) - math.sin(lat1r) * math.cos(lat2r) * math.cos(dlon)

    return math.degrees(math.atan2(y, x))

# Interpolating points
def interpolate_distance(points, dist):
    result = []

    if len(points) == 0:
        return result

    d = 0
    i = 0
    p1 = p2 = points[0]

    while i < len(points):
        if i == 0:
            result.append(points[0])
            i += 1
            continue

        if d == 0:
            p1 = result[-1]
        else:
            p1 = points[i-1]

        p2 = points[i]

        d += distance.distance(p1, p2).m

        if d >= dist:
            b = bearing(p1, p2)
            p2_copy = move_by_angle_and_distance2(p2, b, -(d - dist))
            result.append(p2_copy)
            d = 0
        else:
            i += 1

    result.append(points[-1])

    return np.array(result)

# Moving by angle and distance
def move_by_angle_and_distance2(p, angle, dist):
    angle_rad = math.radians(angle)
    dx = dist * math.sin(angle_rad)
    dy = dist * math.cos(angle_rad)

    delta_longitude = dx / (one_degree * math.cos(math.radians(p[0])))
    delta_latitude = dy / one_degree

    result = [p[0] + delta_latitude, p[1] + delta_longitude]

    return result