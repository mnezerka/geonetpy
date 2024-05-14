
class Rect:
    def __init__(self, point1, point2):
        self.point1 = point1
        self.point2 = point2

    def get_center(self):
        return [
            self.point1[0] + (self.point2[0] - self.point1[0]) / 2,
            self.point1[1] + (self.point2[1] - self.point1[1]) / 2
        ]

    def get_corner_points(self):
        return [
            self.point1,
            [self.point2[0], self.point1[1]],
            self.point2,
            [self.point1[0], self.point2[1]],
            self.point1,
        ]
