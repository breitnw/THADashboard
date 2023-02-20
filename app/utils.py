
# West: 7600 Victoria drive, Victoria MN 55386
# East: 1835 North Penn Avenue, Minneapolis MN 55411
# HUB_LOCATION_COORDS = {"LODGE": (44.867340, -93.674630), "NORTH POINT": (44.998190, -93.308270), "WIS": (44.956050,-93.135910)}

# The hub names that appear in the "Route/Driver" column in MembershipWorks. Used to filter out individual drivers from hubs.
ROUTE_DRIVER_HUBS = ["West", "East"]


def safe_incr(redis_client, key):
    value = None
    while value is None or value == '':
        value = redis_client.incr(key)
    return value
