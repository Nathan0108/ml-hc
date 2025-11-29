import math


class Calculate:
    def __init__(self, focal_length_x, focal_length_y, baseline_distance, c_x, c_y):
        self.focal_length_x = focal_length_x  # pixels
        self.focal_length_y = focal_length_y
        self.baseline_distance = baseline_distance  # meters
        self.c_x = c_x  # pixels
        self.c_y = c_y  # pixels

    def getZDistanceFrom(self, p1, p2):
        disparity = abs(p2.x - p1.x)
        if disparity == 0:
            return float('inf')
        return (self.baseline_distance * self.focal_length_x) / disparity

    def getCoordinatesFrom(self, p1, p2):
        z = self.getZDistanceFrom(p1, p2)

        u_x = (p1.x + p2.x) / 2 - self.c_x
        u_y = (p1.y + p2.y) / 2 - self.c_y

        x = (u_x * z) / self.focal_length_x
        y = (u_y * z) / self.focal_length_y

        return Point3D(x, y, z)
    def getXYIntersection(self, p1, p2):
        if p2.z == p1.z:
            return Point2D(p1.x, p1.y)

        t = (-p1.z) / (p2.z - p1.z)
        x_int = p1.x + t * (p2.x - p1.x)
        y_int = p1.y + t * (p2.y - p1.y)
        return Point2D(x_int, y_int)

    def getMiddlePoint(self, p1, p2):
        return (p1 + p2) / 2

    def getEuclideanDistance(self, p1, p2):
        return p1.distance_to(p2)


class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point2D(x={self.x:.2f}, y={self.y:.2f})"

    def __add__(self, other):
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point2D(self.x - other.x, self.y - other.y)

    def __truediv__(self, scalar):
        return Point2D(self.x / scalar, self.y / scalar)

    def __mul__(self, scalar):
        return Point2D(self.x * scalar, self.y * scalar)

    def distance_to(self, other):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class Point3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"Point3D(x={self.x:.3f}, y={self.y:.3f}, z={self.z:.3f})"

    def __add__(self, other):
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Point3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar):
        return Point3D(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar):
        return Point3D(self.x / scalar, self.y / scalar, self.z / scalar)

    def distance_to(self, other):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2)
