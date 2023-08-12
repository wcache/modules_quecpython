from math import radians, cos, sqrt, pi

MAX_LNG = 180
MAX_LAT = 90
ARC = 6371393.0


class Point(object):

    def __init__(self, longitude, latitude):
        """经纬度表示的点"""
        self.longitude = longitude
        self.latitude = latitude

    def is_in_earth(self):
        return (-MAX_LNG < self.longitude < MAX_LNG) and (-MAX_LAT < self.latitude < MAX_LAT)

    @property
    def coordinate(self):
        return [self.longitude, self.latitude]



class Circular(object):

    def __init__(self, point, radius):
        """圆形围栏"""
        self.point = point
        self.radius = radius
        self.circumscribed_rectangle = None

    def __repr__(self):
        return 'Circular({})'.format(self.coordinate)

    def __contains__(self, point):
        dx = point.longitude - self.point.longitude
        dy = point.latitude - self.point.latitude
        b = (point.latitude + self.point.latitude) / 2.0
        lx = radians(dx) * ARC * cos(radians(b))
        ly = radians(dy) * ARC
        dist = int(sqrt(lx * lx + ly * ly))
        return dist <= int(self.radius)

    def get_circumscribed_rectangle(self, fresh=False):
        if self.circumscribed_rectangle is None or fresh:
            lat_offset = self.radius * (360 / (ARC * 2 * pi))
            lng_offset = self.radius * (360 / (ARC * cos(radians(self.point.latitude)) * 2 * pi))
            self.circumscribed_rectangle = Rectangle(
                Point(self.point.longitude - lng_offset, self.point.latitude + lat_offset),
                Point(self.point.longitude + lng_offset, self.point.latitude - lat_offset),
            )
        return self.circumscribed_rectangle

    @property
    def coordinate(self):
        return self.point.coordinate + [self.radius]


class Rectangle(object):

    def __init__(self, left_top_point, right_bottom_point):
        """矩形围栏"""
        self.left_top_point = left_top_point
        self.right_bottom_point = right_bottom_point

    def __repr__(self):
        return 'Rectangle({})'.format(self.coordinate)

    def __contains__(self, point):
        return self.__poi_in_rectangle(
            point.longitude, point.latitude,
            self.left_top_point.latitude, self.left_top_point.longitude,
            self.right_bottom_point.latitude, self.right_bottom_point.longitude,
        )

    @staticmethod
    def __poi_in_rectangle(longitude, latitude, max_latitude, min_longitude, min_latitude, max_longitude):
        if min_latitude <= latitude <= max_latitude:
            if min_longitude * max_longitude > 0:
                if min_longitude <= longitude <= max_longitude:
                    return True
            else:
                if (abs(min_longitude) + abs(max_longitude)) < MAX_LNG:
                    if min_longitude <= longitude <= max_longitude:
                        return True
                else:
                    left = max(min_longitude, max_longitude)
                    right = min(min_longitude, max_longitude)
                    if left <= longitude <= MAX_LNG or right <= longitude <= -MAX_LNG:
                        return True
        return False

    def get_circumscribed_rectangle(self):
        return self

    @property
    def coordinate(self):
        return self.left_top_point.coordinate + self.right_bottom_point.coordinate


class Polygon(object):

    def __init__(self, *points):
        """多边形围栏"""
        self.__points = points
        self.__circumscribed_rectangle = None
        if len(self.__points) < 2:
            raise ValueError('Polygon has more than 2 points, less 2 points were given.')

    def __repr__(self):
        return 'Polygon({})'.format(self.coordinate)

    def __contains__(self, point):
        if not point.is_in_earth():
            return False
        count = 0
        for index in range(len(self.points)-1):
            if self.__is_ray_intersects_segment(point, self.__points[index], self.__points[index+1]):
                count += 1
        return count % 2 != 0

    @staticmethod
    def __is_ray_intersects_segment(poi, s_poi, e_poi):
        if s_poi.latitude == e_poi.latitude:
            return False
        if s_poi.latitude > poi.latitude and e_poi.latitude > poi.latitude:
            return False
        if s_poi.latitude < poi.latitude and e_poi.latitude < poi.latitude:
            return False
        if s_poi.latitude == poi.latitude and e_poi.latitude > poi.latitude:
            return False
        if e_poi.latitude == poi.latitude and s_poi.latitude > poi.latitude:
            return False
        if s_poi.longitude < poi.longitude and e_poi.longitude < poi.longitude:
            return False
        xseg = (
            e_poi.longitude
            + (poi.latitude - e_poi.latitude)
            / (s_poi.latitude - e_poi.latitude)
            * (s_poi.longitude - e_poi.longitude)
        )
        if xseg < poi.longitude:
            return False
        return True
    
    @property
    def circumscribed_rectangle():
        if self.__circumscribed_rectangle is None or fresh:
            if self.circumscribed_rectangle is None or fresh:
                lngs = [p.longitude for p in self.points]
                lats = [p.latitude for p in self.points]
                self.__circumscribed_rectangle = Rectangle(
                    Point(min(lngs), max(lats)),
                    Point(max(lngs), min(lats))
                )
        return self.__circumscribed_rectangle

    @property
    def coordinate(self):
        rv = []
        for p in self.points:
            rv += p.coordinate
        return rv


def Fence(params_list):
    total_points = int(params_list[0])
    flag = int(params_list[1])
    coordinate = [float(x) for x in params_list[2:]]
    if total_points == 1:
        fence = Circular(Point(coordinate[0], coordinate[1]), coordinate[2], flag=flag)
    elif total_points == 2:
        fence = Rectangle(
            Point(coordinate[0], coordinate[1]),
            Point(coordinate[2], coordinate[3]),
            flag=flag
        )
    else:
        fence = Polygon(
            *[Point(coordinate[index], coordinate[index+1]) for index in range(0, len(coordinate), 2)],
            flag=flag
        )
    return fence


class GeoFence:

    def __init__(self):
        self.__path = "/usr/GFS"
        self.__gfsp_file = "/usr/GFS/properties.json"
        self.__gfscr_file = "/usr/GFS/cir_rectangle.json"
        self.__gfscrt_file = "/usr/GFS/cir_rectangle_tree.json"
        self.__gfsp_data = {}
        self.__gfscr_data = {}
        self.__gfscrt_data = {}

        self.__init_db()

    def __init_db(self):
        if not ql_fs.path_exists(self.__path):
            ql_fs.mkdirs(self.__path)
        if not ql_fs.path_exists(self.__gfsp_file):
            ql_fs.touch(self.__gfsp_file, {})
        if not ql_fs.path_exists(self.__gfscr_file):
            ql_fs.touch(self.__gfscr_file, {})
        if not ql_fs.path_exists(self.__gfscrt_file):
            ql_fs.touch(self.__gfscrt_file, {})

        self.__gfsp_data = ql_fs.read_json(self.__gfsp_file)
        self.__gfscr_data = ql_fs.read_json(self.__gfscr_file)
        self.__gfscrt_data = ql_fs.read_json(self.__gfscrt_file)

    @property
    def gfsp_data(self):
        return self.__gfsp_data

    def update(self, data):
        """update fences"""
        self.__gfsp_data.update(data)
        self.init_fence_circumscribed_rectangle()
        self.init_fence_circumscribed_rectangle_tree()

    def delete(self, fence_ids):
        """delete fences by id"""
        if not fence_ids:
            return
        for fence_id in fence_ids:
            if fence_id in self.__gfsp_data:
                del self.__gfsp_data[fence_id]
        self.init_fence_circumscribed_rectangle()
        self.init_fence_circumscribed_rectangle_tree()

    def delete_all(self):
        self.delete(self.__gfsp_data.keys())

    def save(self):
        """save fence data to file system"""
        ql_fs.touch(self.__gfsp_file, self.__gfsp_data)
        ql_fs.touch(self.__gfscr_file, self.__gfscr_data)
        ql_fs.touch(self.__gfscrt_file, self.__gfscrt_data)

    def init_fence_circumscribed_rectangle(self):
        gfscr_data = {}
        for fence_id, params in self.__gfsp_data.items():
            rect = Fence(params).get_circumscribed_rectangle()
            gfscr_data[fence_id] = rect.coordinate
        self.__gfscr_data.update(gfscr_data)

    def __init_root_circumscribed_rectangle(self):
        root_coordinate = None
        for coordinate in self.__gfscr_data.values():
            if root_coordinate is None:
                root_coordinate = coordinate
            if root_coordinate[0] > coordinate[0]:
                root_coordinate[0] = coordinate[0]
            if root_coordinate[1] < coordinate[1]:
                root_coordinate[1] = coordinate[1]
            if root_coordinate[2] < coordinate[2]:
                root_coordinate[2] = coordinate[2]
            if root_coordinate[3] > coordinate[3]:
                root_coordinate[3] = coordinate[3]
        if root_coordinate:
            self.__gfscrt_data["coordinate"] = root_coordinate

    @staticmethod
    def __init_fence_circumscribed_rectangle_coordinate(p_coordinate, s_coordinate):
        return [
            min(p_coordinate[0], s_coordinate[0]),
            max(p_coordinate[1], s_coordinate[1]),
            max(p_coordinate[2], s_coordinate[2]),
            min(p_coordinate[3], s_coordinate[3]),
        ]

    def __init_fence_circumscribed_rectangle_from_sun_area(self, sk, sl, line_num, _ij, sun_area):
        _area = {}
        for k in range(sk, sk + 2):
            for l in range(sl, sl + 2):
                _kl = k * line_num + l
                if sun_area.get(_kl):
                    if _area.get(_ij) is None:
                        _area[_ij] = {
                            "coordinate": sun_area[_kl]["coordinate"],
                            "areas": [sun_area[_kl]]
                        }
                    else:
                        _area[_ij]["coordinate"] = self.__init_fence_circumscribed_rectangle_coordinate(
                            _area[_ij]["coordinate"], sun_area[_kl]["coordinate"]
                        )
                        _area[_ij]["areas"].append(sun_area[_kl])
        return _area

    def __init_fence_circumscribed_rectangle_recursion(self, line_num, sun_area):
        _area = {}
        _line_num = int(line_num / 2)
        if _line_num > 1:
            for i in range(_line_num):
                sk = i * 2
                for j in range(_line_num):
                    _ij = i * _line_num + j
                    sl = j * 2
                    _area_ = self.__init_fence_circumscribed_rectangle_from_sun_area(sk, sl, line_num, _ij, sun_area)
                    _area.update(_area_)
            sun_area = _area
            return self.__init_fence_circumscribed_rectangle_recursion(_line_num, sun_area)
        else:
            return list(sun_area.values())

    def __init_fence_circumscribed_rectangle_tree(self, line_num):
        root_coordinate = self.__gfscrt_data.get("coordinate")
        if not root_coordinate:
            return

        lat_range = (root_coordinate[2] - root_coordinate[0]) / line_num
        lng_range = (root_coordinate[1] - root_coordinate[3]) / line_num
        leaf_area = {}
        for fence_id, coordinate in self.__gfscr_data.items():
            _lng_no = int((coordinate[3] - root_coordinate[3]) / lng_range)
            _lat_no = int((coordinate[0] - root_coordinate[0]) / lat_range)
            k = _lat_no * line_num + _lng_no
            if leaf_area.get(k) is None:
                leaf_area[k] = {
                    "fence_ids": [fence_id],
                    "coordinate": coordinate,
                }
            else:
                leaf_area[k]["fence_ids"].append(fence_id)
                leaf_area[k]["coordinate"] = self.__init_fence_circumscribed_rectangle_coordinate(
                    leaf_area[k]["coordinate"],
                    coordinate
                )

        self.__gfscrt_data["areas"] = self.__init_fence_circumscribed_rectangle_recursion(line_num, leaf_area)

    def init_fence_circumscribed_rectangle_tree(self, line_num=16):
        self.__gfscrt_data = {}
        self.__init_root_circumscribed_rectangle()
        self.__init_fence_circumscribed_rectangle_tree(line_num)

    def __poi_in_fence(self, point, fence_id):
        fence_info = {}
        coordinate = self.__gfscr_data[fence_id]
        if point in Rectangle(Point(*coordinate[:2]), Point(*coordinate[2:])):
            params_list = self.__gfsp_data.get(fence_id)
            fence = Fence(params_list)
            if point in fence:
                fence_info[fence_id] = fence
        return fence_info

    def __check_point_in_fence_rtree(self, point, rectangle, areas, fence_ids):
        _in_fence = {}
        if point in rectangle:
            for item in areas:
                _coordinate = item["coordinate"]
                _areas = item.get("areas", [])
                _fence_ids = item.get("fence_ids", [])
                _in_fence.update(
                    self.__check_point_in_fence_rtree(
                        point,
                        Rectangle(Point(*_coordinate[:2]),Point(*_coordinate[2:])),
                        _areas,
                        _fence_ids
                    )
                )
            if fence_ids:
                for fence_id in fence_ids:
                    _in_fence.update(self.__poi_in_fence(point, fence_id))
        return _in_fence

    def check_point_in_fence(self, longitude, latitude):
        coordinate = self.__gfscrt_data.get("coordinate")
        if not coordinate:
            return {}
        areas = self.__gfscrt_data.get("areas")
        if not areas:
            return {}
        fence_ids = []
        point = Point(longitude, latitude)
        rectangle = Rectangle(Point(*coordinate[:2]), Point(*coordinate[2:]))
        return self.__check_point_in_fence_rtree(point, rectangle, areas, fence_ids)
