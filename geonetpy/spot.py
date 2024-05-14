from .geoutils import haversine_distance

class Spot:
    def __init__(self, spot_id, center):
        self.id = spot_id
        self.center = center

    def copy(self):
        return Spot(self.id, self.center.copy())

    def distance(self, other):
        return haversine_distance(self.center, other)

    def add(self, point):
        self.center = get_centroid([self.center, point])
        return point

def get_centroid(points):
    total_x = 0
    total_y = 0
    num_points = len(points)

    # Sum up all x and y coordinates
    for point in points:
        total_x += point[0]
        total_y += point[1]

    # Compute average x and y coordinates
    centroid_x = total_x / num_points
    centroid_y = total_y / num_points

    return [centroid_x, centroid_y]
