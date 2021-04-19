"""Tower Defense Game: Functions for utility"""
from math import atan, sin, cos, sqrt, pi
from bisect import bisect_left
import globals


def is_string(string):
    return isinstance(string, type(""))


def is_rgb_color_value(color_value):
    if isinstance(color_value, tuple) or isinstance(color_value, list):
        if len(color_value) == 3:
            for _ in color_value:
                if _ < 0 or _ > 255:
                    return False
            return True
    return False


def generate_next_id(existing_ids):
    if not existing_ids:
        return 1
    else:
        return max(existing_ids) + 1


def calculate_component_distances(distance_moved, start_x, start_y, end_x, end_y):
    """To calculate x and y distance (the component distances) travelled by an entity
    given that they move at a constant velocity. i.e. if the velocity is 5 then you
    can't calculate the new position as x + 5 and y + 5 because then the hypoteneuse
    of the triangle is longer than 5 units, so the hypoteneuse is set to 5, the angle
    is calculated based on the coordinates of the start position and end position, and
    then the x and y component distances are calculated"""
    # First determine if line is horizontal or vertical or if there's no line
    # No Line
    if end_y - start_y == 0 and end_x - start_x == 0:
        return Point(0, 0)
    # Horizontal
    if end_y - start_y == 0:
        if end_x - start_x > 0:
            return Point(distance_moved, 0)
        else:
            return Point(-distance_moved, 0)
    # Vertical
    if end_x - start_x == 0:
        if end_y - start_y > 0:
            return Point(0, distance_moved)
        else:
            return Point(0, -distance_moved)
    # Determine which quadrant of the coordinate system the end point is if the start point is the origin
    quadrant = None
    if end_x > start_x and end_y > start_y:
        quadrant = "br"
    elif end_x < start_x and end_y > start_y:
        quadrant = "bl"
    elif end_x > start_x and end_y < start_y:
        quadrant = "tr"
    elif end_x < start_x and end_y < start_y:
        quadrant = "tl"
    angle = abs(atan((end_x - start_x) / (end_y - start_y)))
    component_x = sin(angle) * distance_moved
    component_y = cos(angle) * distance_moved
    if quadrant in ("bl", "tl"):
        component_x = -component_x
    if quadrant in ("tl", "tr"):
        component_y = -component_y
    return Point(component_x, component_y)


def euclidean_distance(a, b):
    if not isinstance(a, Point):
        a = Point(a[0], a[1])
    if not isinstance(b, Point):
        b = Point(b[0], b[1])
    return sqrt(abs(a.x - b.x)**2 + abs(a.y - b.y)**2)


def point_overlaps_with_rect(point_coordinates, rect_coordinates, rect_width, rect_heigth):
    if not isinstance(point_coordinates, Point): raise TypeError("point coordinates has to be a Point object")
    if not isinstance(rect_coordinates, Point): raise TypeError("rect coordinates has to be a Point object")
    if rect_coordinates.x <= point_coordinates.x <= rect_coordinates.x + rect_width and rect_coordinates.y <= point_coordinates.y <= rect_coordinates.y + rect_heigth:
        return True
    else:
        return False


def rects_overlap(rect1_coordinates, rect1_width, rect1_height, rect2_coordinates, rect2_width, rect2_height):
    if not isinstance(rect1_coordinates, Point): raise TypeError("rect1 coordinates has to be a Point object")
    if not isinstance(rect2_coordinates, Point): raise TypeError("rect2 coordinates has to be a Point object")
    rect1_corners = (rect1_coordinates, Point(rect1_coordinates.x + rect1_width, rect1_coordinates.y),
                     Point(rect1_coordinates.x, rect1_coordinates.y + rect1_height),
                     Point(rect1_coordinates.x + rect1_width, rect1_coordinates.y + rect1_height))
    for corner in rect1_corners:
        if point_overlaps_with_rect(corner, rect2_coordinates, rect2_width, rect2_height):
            return True
    return False


def find_angle_of_line(p1, p2):
    """Assuming p1 is the origin point"""
    if p1.x == p2.x and p1.y == p2.y:
        return 0
    line = find_equation_of_line(p1, p2)
    is_vertical = line[0]
    slope = line[1]
    if is_vertical:
        if p1.y > p2.y:
            return 0
        else:
            return 180
    else:
        if slope == 0:
            if p1.x < p2.x:
                return 90
            else:
                return 270
        else:
            if p1.x < p2.x and p1.y > p2.y:
                # Upper right quadrant
                return atan(abs(p2.y - p1.y) / abs(p2.x - p1.x)) * (180 / pi)
            elif p1.x < p2.x and p1.y < p2.y:
                # Bottom right quadrant
                return (atan(abs(p2.y - p1.y) / abs(p2.x - p1.x))) * (180 / pi) + 90
            elif p1.x > p2.x and p1.y > p2.y:
                # Upper left quadrant
                return (atan(abs(p2.y - p1.y) / abs(p2.x - p1.x))) * (180 / pi) + 270
            else:
                # Bottom left quadrant
                return (atan(abs(p2.y - p1.y) / abs(p2.x - p1.x))) * (180 / pi) + 180


def find_equation_of_line(p1, p2):
    if not isinstance(p1, Point): raise ValueError("p1 has to be a Point object")
    if not isinstance(p2, Point): raise ValueError("p2 has to be a Point object")
    try:
        slope = (p2.y - p1.y) / (p2.x - p1.x)
        is_vertical = False
    except ZeroDivisionError:
        x = p1.x
        slope = None
        intercept = None
        is_vertical = True
    if not is_vertical:
        intercept = -(slope * p1.x - p1.y)
        x = None
        return is_vertical, slope, intercept, x
    else:
        return is_vertical, slope, intercept, x


def get_intersection_point_of_lines(line1, line2):
    if not line1.is_vertical and not line2.is_vertical:
        x = (line1.intercept / (line2.slope - line1.slope)) - (line2.intercept / (line2.slope - line1.slope))
        y = line1.slope * x + line1.intercept
        return Point(x, y)
    elif line1.is_vertical:
        y = line2.slope * line1.x_value + line2.intercept
        return Point(line1.x_value, y)
    elif line2.is_vertical:
        y = line1.slope * line2.x_value + line1.intercept
        return Point(line2.x_value, y)


def get_point_on_unit_circle(angle):
    radians = pi/180 * angle
    x = sin(radians)
    y = cos(radians)
    return Point(x, y)


def determine_relative_position_of_two_points(p1, p2):
    if not isinstance(p1, Point): raise ValueError("p1 has to be a Point object")
    if not isinstance(p2, Point): raise ValueError("p2 has to be a Point object")
    if p1.x == p2.x and p1.y == p2.y:
        return "same"
    elif p1.x == p2.x:
        if p1.y < p2.y:
            return "top"
        else:
            return "bottom"
    elif p1.y == p2.y:
        if p1.x < p2.x:
            return "left"
        else:
            return "right"
    elif p1.x > p2.x:
        if p1.y < p2.y:
            return "top right"
        else:
            return "bottom right"
    elif p1.x < p2.x:
        if p1.y < p2.y:
            return "top left"
        else:
            return "bottom left"


def get_closest_number(number_list, number):
    pos = bisect_left(number_list, number)
    if pos == 0:
        return number_list[0]
    if pos == len(number_list):
        return number_list[-1]
    before = number_list[pos - 1]
    after = number_list[pos]
    if after - number < number - before:
        return after
    else:
        return before


class Point:

    def __init__(self, x, y):
        if not isinstance(x, int) and not isinstance(x, float): raise TypeError("x has to be an integer or float")
        if not isinstance(y, int) and not isinstance(y, float): raise TypeError("y has to be an integer or float")
        self.x = x
        self.y = y

    def get_coordinates(self):
        return Point(self.x, self.y)

    def to_tuple(self):
        return self.x, self.y


class Line:

    def __init__(self, slope, intercept, is_vertical, x_value=None):
        if is_vertical:
            self.slope = None
            self.intercept = None
            if x_value is not None:
                self.x_value = x_value
            else:
                raise ValueError("If line is vertical x_value argument can't be None")
        else:
            self.slope = slope
            self.intercept = intercept
            self.x_value = None
        self.is_vertical = is_vertical


class Ray(Line):

    def __init__(self, angle, slope, intercept, is_vertical, x_value=None):
        super().__init__(slope, intercept, is_vertical, x_value)
        self.angle = angle


if __name__ == "__main__":
    test_color = (255, 255, 255)

    rect1 = (50, 50, 50, 50)
    rect2 = (10, 100, 50, 50)

    line1 = Line(0, 3, True, 3)
    line2 = Line(5, 4, False)
    intersection = get_intersection_point_of_lines(line1, line2)
    print(calculate_component_distances(5, 802.5, 502.5, 802.5, 487.5).x, calculate_component_distances(5, 802.5, 502.5, 802.5, 487.5).y)

    print(find_angle_of_line(Point(100, 100), Point(0, 0)))