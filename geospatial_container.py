class GeospatialContainer:
    def __init__(self, lat_min, lat_max, lon_min, lon_max, depth, global_container=False):
        self.subcontainers = []
        self.global_container = global_container
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.data = set()
        if depth > 1:
            self.subcontainers.append(
                GeospatialContainer(lat_min, (lat_min + lat_max) / 2, lon_min, (lon_min + lon_max) / 2, depth - 1))
            self.subcontainers.append(
                GeospatialContainer(lat_min, (lat_min + lat_max) / 2, (lon_min + lon_max) / 2, lon_max, depth - 1))
            self.subcontainers.append(
                GeospatialContainer((lat_min + lat_max) / 2, lat_max, lon_min, (lon_min + lon_max) / 2, depth - 1))
            self.subcontainers.append(
                GeospatialContainer((lat_min + lat_max) / 2, lat_max, (lon_min + lon_max) / 2, lon_max, depth - 1))

    def is_inside(self, lat_min, lat_max, lon_min, lon_max):
        if lat_min >= self.lat_min and lat_max <= self.lat_max:
            if lon_min >= self.lon_min and lon_max <= self.lon_max:
                return 1
        if lon_min > self.lon_max:
            return -1
        if lon_max < self.lon_min:
            return -1
        if lat_min > self.lat_max:
            return -1
        if lat_max < self.lat_min:
            return -1
        return 0

    def add(self, obj):
        if self.is_inside(*obj.get_border_coordinates()) == -1:
            return
        for x in self.subcontainers:
            if x.is_inside(*obj.get_border_coordinates()) == 1:
                x.add(obj)
                return
        self.data.add(obj)

    def clear(self):
        self.data = set()
        for x in self.subcontainers:
            x.clear()

    def get_objects(self, lat_min, lat_max, lon_min, lon_max):
        ret = set()
        if self.is_inside(lat_min, lat_max, lon_min, lon_max) == -1:
            return ret
        ret = ret | self.data
        for x in self.subcontainers:
            ret = ret | x.get_objects(lat_min, lat_max, lon_min, lon_max)
        return ret
