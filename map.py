from pygame import Surface, draw
import globals
from utility import *


class Map:

    def __init__(self, win, map_array, wall_color):
        if not isinstance(win, Surface): raise TypeError("win has to be a Surface object")
        if not is_rgb_color_value(wall_color): raise TypeError("Wall color has to be an RGB color tuple")
        self.validate_map(map_array)
        self.win = win
        self.grid_width = globals.WIN_WIDTH // len(map_array[0])
        self.map_array = map_array
        self.nrows = len(self.map_array)
        self.ncols = len(self.map_array[0])
        self.empty_squares = []
        for i in range(0, self.nrows - 1):
            for j in range(0, self.ncols - 1):
                if self.map_array[i][j] == 0:
                    self.empty_squares.append((i, j))
        self.grid_coordinates = [[(0, 0) for j in range(0, self.ncols)] for i in range(0, self.nrows)]
        self.grid_column_x_values = []
        self.grid_row_y_values = []
        self.get_gridline_coordinates()
        self.wall_color = wall_color
        self.show_gridlines = True

    def validate_map(self, map_array):
        valid_values = (0, 1)
        if not isinstance(map_array, list) and not isinstance(map_array, tuple):
            raise ValueError("Map array has to be a list or tuple")
        if len(set([len(i) for i in map_array])) != 1:
            raise ValueError("Each row has to be the same length in the map array")
        if len(map_array) * 2 != len(map_array[0]):
            raise ValueError("The number of rows has to be half the number of columns")
        for i in map_array:
            if not isinstance(i, list) and not isinstance(i, tuple):
                raise ValueError("Each row has to be a list or tuple in the map array")
            for j in i:
                if j not in valid_values:
                    raise ValueError(f"Each value in the map array must be in {valid_values}")

    def get_gridline_coordinates(self):
        current_x = 0
        current_y = 0
        for i in range(0, self.nrows):
            for j in range(0, self.ncols):
                self.grid_coordinates[i][j] = (current_x, current_y)
                current_x += self.grid_width
            current_x = 0
            current_y += self.grid_width
        for row in self.grid_coordinates:
            for c in row:
                self.grid_column_x_values.append(c[0])
                self.grid_row_y_values.append(c[1])
        self.grid_column_x_values = sorted(list(set(self.grid_column_x_values)))
        self.grid_row_y_values = sorted(list(set(self.grid_row_y_values)))

    def get_grid_position_of_point(self, point):
        if not isinstance(point, Point): raise ValueError("point has to be a Point object")
        closest_column_x_value = get_closest_number(number_list=self.grid_column_x_values, number=point.x)
        closest_row_y_value = get_closest_number(number_list=self.grid_row_y_values, number=point.y)
        column_index = closest_column_x_value // self.grid_width
        row_index = closest_row_y_value // self.grid_width
        # Determine if point is before or after the values
        if closest_column_x_value - point.x > 0:
            column_index -= 1
        if closest_row_y_value - point.y > 0:
            row_index -= 1
        return row_index, column_index

    def get_neighboring_grid_positions(self, grid_position):
        adjacent_grid_coordinates = ((grid_position[0] - 1, grid_position[1] - 1),
                                     (grid_position[0] - 1, grid_position[1]),
                                     (grid_position[0] - 1, grid_position[1] + 1),
                                     (grid_position[0], grid_position[1] - 1),
                                     (grid_position[0], grid_position[1] + 1),
                                     (grid_position[0] + 1, grid_position[1] - 1),
                                     (grid_position[0] + 1, grid_position[1]),
                                     (grid_position[0] + 1, grid_position[1] + 1))
        return adjacent_grid_coordinates

    def get_neighboring_corner_grid_positions(self, grid_position):
        adjacent_grid_coordinates = ((grid_position[0] - 1, grid_position[1] - 1),
                                     (grid_position[0] - 1, grid_position[1] + 1),
                                     (grid_position[0] + 1, grid_position[1] - 1),
                                     (grid_position[0] + 1, grid_position[1] + 1))
        return adjacent_grid_coordinates

    def get_neighboring_edge_grid_positions(self, grid_position):
        adjacent_grid_coordinates = ((grid_position[0] - 1, grid_position[1]),
                                     (grid_position[0], grid_position[1] - 1),
                                     (grid_position[0], grid_position[1] + 1),
                                     (grid_position[0] + 1, grid_position[1]))
        return adjacent_grid_coordinates

    def draw_gridlines(self):
        current_x = 0
        current_y = 0
        # Verical lines
        for i in range(0, self.ncols):
            draw.line(self.win, globals.GREY, (current_x, current_y), (current_x, current_y + globals.WIN_HEIGHT), width=1)
            current_x += self.grid_width
        # Horizontal lines
        current_x = 0
        for i in range(0, self.nrows):
            draw.line(self.win, globals.GREY, (current_x, current_y), (current_x + globals.WIN_WIDTH, current_y), width=1)
            current_y += self.grid_width

    def draw(self):
        current_x = 0
        current_y = 0
        for row in self.map_array:
            for value in row:
                if value == 1:
                    draw.rect(self.win, self.wall_color, (current_x, current_y, self.grid_width, self.grid_width))
                current_x += self.grid_width
            current_x = 0
            current_y += self.grid_width

