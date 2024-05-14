from .rect import Rect

class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def from_point(cls, p):
        v = cls(p[0], p[1])
        return v

    def hadamard(self, other):
        return self.x * other.x + self.y * other.y

    def scalar(self, scalar):
        return Vector(self.x * scalar, self.y * scalar)


Hull4BoundVectors = [
    Vector(1, 0),
    Vector(-1, 0),
    Vector(0, 1),
    Vector(0, -1)
]


class Hull4:
    def __init__(self, hullid):
        self.id = hullid
        self.bounds = [0.0] * 4

    @classmethod
    def from_vector(cls, v, hullid):
        h = cls(hullid)
        for i in range(4):
            h.bounds[i] = v.hadamard(Hull4BoundVectors[i])
        return h

    def copy(self):
        h = Hull4(self.id)
        h.bounds = self.bounds.copy()
        return h

    def size(self):
        v = [vector.scalar(self.bounds[i]) for i, vector in enumerate(Hull4BoundVectors)]
        return v[0].x - v[1].x + v[2].y - v[3].y

    def estimate_size(self, h2):
        bounds = [0.0] * 4
        for i in range(4):
            bounds[i] = max(self.bounds[i], h2.bounds[i])
        v = [vector.scalar(bounds[i]) for i, vector in enumerate(Hull4BoundVectors)]
        return v[0].x - v[1].x + v[2].y - v[3].y

    def add(self, h2):
        for i in range(4):
            self.bounds[i] = max(self.bounds[i], h2.bounds[i])
        return self

    def bounding_rect(self):
        v = [vector.scalar(self.bounds[i]) for i, vector in enumerate(Hull4BoundVectors)]
        return Rect([v[0].x, v[2].y], [v[1].x, v[3].y])

    def equals(self, h2):
        for i in range(4):
            if self.bounds[i] != h2.bounds[i]:
                return False
        return True
