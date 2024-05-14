import logging
import numpy as np
from .geoutils import haversine_distance

BALANCING_FACTOR = 150

class BallTreeNode:
    def __init__(self, point, index):
        self.point = point
        self.index = index
        self.left = None
        self.right = None

class BallTree:
    def __init__(self, points):
        self.root = self.build_tree(points)

    def build_tree(self, points):
        if len(points) == 0:
            return None

        # find the median index and point based on latitude

        # sort by first coordinate
        points = points[points[:, 0].argsort()]

        median_index = len(points) // 2
        median_point = points[median_index]

        # create node for median point
        node = BallTreeNode(median_point, median_index)

        # recursively build left and right subtrees
        node.left = self.build_tree(points[:median_index])
        node.right = self.build_tree(points[median_index + 1:])

        return node

    def query(self, query_point, k=1):
        return self._query(self.root, query_point, k, [])

    def _query(self, node, query_point, k, nearest):
        if not node:
            return nearest

        distance = haversine_distance(node.point, query_point)
        nearest.append((distance, node.point, node.index))

        if len(nearest) > k:
            nearest.sort(key=lambda x: x[0])
            nearest = nearest[:k]

        axis = 0  # Split on latitude
        if query_point[axis] < node.point[axis]:
            nearest = self._query(node.left, query_point, k, nearest)
            if query_point[axis] + nearest[-1][0] >= node.point[axis]:
                nearest = self._query(node.right, query_point, k, nearest)
        else:
            nearest = self._query(node.right, query_point, k, nearest)
            if query_point[axis] - nearest[-1][0] <= node.point[axis]:
                nearest = self._query(node.left, query_point, k, nearest)

        return nearest

    def add_point(self, point):
        self._add_point(self.root, point)

    def _add_point(self, node, point):
        if not node:
            return BallTreeNode(point, 0)

        axis = 0  # Split on latitude
        if point[axis] < node.point[axis]:
            node.left = self._add_point(node.left, point)
        else:
            node.right = self._add_point(node.right, point)

        # Rebuild the tree if it is unbalanced
        if self._is_unbalanced(node):
            logging.info('balancing ball tree node, height: %d', self._height(node))
            points = self._collect_points(node)
            node = self.build_tree(points)
            logging.info('node balancing done, height: %d', self._height(node))

        return node

    def _is_unbalanced(self, node):
        return abs(self._height(node.left) - self._height(node.right)) > BALANCING_FACTOR

    def get_height(self):
        return self._height(self.root)

    def _height(self, node):
        if not node:
            return 0
        return max(self._height(node.left), self._height(node.right)) + 1

    def _collect_points(self, node):
        points = []
        self._collect_points_recursively(node, points)
        return np.array(points)

    def _collect_points_recursively(self, node, points):
        if not node:
            return
        self._collect_points_recursively(node.left, points)
        points.append(node.point)
        self._collect_points_recursively(node.right, points)

    # TODO: remove duplicates
    def get_points(self):
        points = []
        self._get_points(self.root, points)
        return points

    # TODO: remove duplicates
    def _get_points(self, node, points):
        if node:
            self._get_points(node.left, points)
            points.append(node.point)
            self._get_points(node.right, points)
