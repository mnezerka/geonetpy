
import math

# Radius of the Earth in meters
EARTH_RADIUS = 6371.0 * 1000

def haversine_distance(point1, point2):

    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(point1[0])
    lon1_rad = math.radians(point1[1])
    lat2_rad = math.radians(point2[0])
    lon2_rad = math.radians(point2[1])

    # Calculate the differences between latitudes and longitudes
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate the distance
    distance = EARTH_RADIUS * c

    return distance
