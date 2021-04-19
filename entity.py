from pygame import Surface, draw
import globals
from utility import *
from map import Map
from random import random, choice, randint
from math import sin, cos, sqrt


class Entity:

    def __init__(self, win, map, id, shape, width, color, coordinates):
        if not isinstance(win, Surface): raise TypeError("win has to be a Surface object")
        if not isinstance(map, Map): raise ValueError("map has to be a Map object")
        if not isinstance(id, int): raise TypeError("id has to be an int")
        if shape not in ("square", "circle"): raise TypeError("shape has to be square, or circle")
        if not isinstance(width, int): raise TypeError("width has to be an int")
        if not is_rgb_color_value(color): raise TypeError("color has to be an RGB color tuple")
        if not isinstance(coordinates, Point) and coordinates is not None: raise TypeError("coordinates has to be a Point object or None")
        self.win = win
        self.map = map
        self.id = id
        self.shape = shape
        self.width = width
        self.height = width
        if self.shape == "circle":
            self.radius = self.width / 2
        self.original_color = color
        self.color = color
        self.coordinates = coordinates
        if self.coordinates is not None:
            self.coordinates_center = Point(self.coordinates.x + self.width / 2, self.coordinates.y + self.width / 2)
        else:
            self.coordinates_center = None
        self.grid_position = (0, 0)
        self.adjacent_grid_positions = None
        self.get_grid_coordinates(self.map)

    def update_at_start_of_frame(self):
        if self.coordinates is not None:
            if self.shape == "square":
                self.coordinates_center.x = self.coordinates.x + self.width / 2
                self.coordinates_center.y = self.coordinates.y + self.width / 2
            else:
                self.coordinates_center.x = self.coordinates.x
                self.coordinates_center.y = self.coordinates.y
            self.get_grid_coordinates(self.map)

    def draw(self):
        if self.coordinates is not None:
            if self.shape == "square":
                color = self.color
                draw.rect(self.win, color, (self.coordinates.x, self.coordinates.y, self.width, self.height))
            elif self.shape == "circle":
                color = self.color
                draw.circle(self.win, color, (self.coordinates.x, self.coordinates.y), self.radius)

    def get_grid_coordinates(self, map):
        if not isinstance(map, Map): raise ValueError("map has to be a Map object")
        if self.coordinates is not None:
            self.grid_position = self.map.get_grid_position_of_point(self.coordinates_center)
            self.adjacent_grid_positions = self.map.get_neighboring_grid_positions(self.grid_position)


class Soldier(Entity):

    def __init__(self, win, map, id, shape, width, coordinates, faction, weapon_type, aim_factor):
        if faction not in ("TR", "NC", "VS"): raise ValueError("faction has to be either TR, NC, or VS")
        if not isinstance(map, Map): raise ValueError("map has to be a Map object")
        if weapon_type not in ("short range", "med range", "long range"): raise ValueError("weapon type not valid.")
        if faction == "TR":
            color = globals.FactionColor.TR.value
        elif faction == "NC":
            color = globals.FactionColor.NC.value
        elif faction == "VS":
            color = globals.FactionColor.VS.value
        super().__init__(win, map, id, shape, width, color, coordinates)

        self.movement_speed = 0.05
        self.destination = None
        self.destination_queue = []
        self.is_moving = False
        self.moving_to_point = False
        self.enable_collisions = True

        # Ray list format: ((end_x, end_y), (R, G, B))
        self.ray_list = []
        self.show_rays = True
        self.show_destination_queue = False
        self.faction = faction
        self.dead_color = [max(i - 150, 0) for i in self.color]
        self.shield_recharge_delay_active_color = [min(i + 200, 255) for i in self.color]

        self.maximum_health = 200
        self.health = self.maximum_health
        self.weapon_type = weapon_type
        self.fire_rate = 10
        self.fire_rate_counter = self.fire_rate
        self.damage_falloff = {}
        self.determine_damage_falloff()
        self.aim_factor = aim_factor
        self.enemy_engagement_range = 1000
        self.shooting = False
        self.current_target_enemy = None
        self.current_target_enemy_distance = None
        self.shield_recharge_delay = 1000
        self.shield_recharge_delay_active = False
        self.shield_recharge_delay_counter = 0
        self.shield_recharge_delay_blinking_effect_rate = 50
        self.shield_recharge_delay_blinking_effect_counter = 0
        self.shield_is_recharging = False
        self.shield_recharge_rate = 10
        self.getting_shot_at_by_list = []

        self.kills = 0
        self.deaths = 0
        self.alive = False
        self.spawn_timer_counter = 0
        self.revivable = False

    def update_at_start_of_frame(self):
        super().update_at_start_of_frame()
        if self.ray_list:
            self.ray_list = []
        if self.coordinates is None:
            self.alive = False
            self.color = self.dead_color
        if self.health <= 0 and self.alive:
            self.alive = False
            self.color = self.dead_color
            self.deaths += 1
        elif not self.alive:
            self.spawn_timer_counter += 1
            best_spawn_point = self.find_best_spawn_point(globals.spawn_point_dict.values())
            self.spawn(best_spawn_point)
        elif self.alive:
            if self.shield_recharge_delay_active:
                self.shield_recharge_delay_counter += 1
                self.shield_recharge_delay_blinking_effect_counter += 1
                self.shield_is_recharging = False
                if self.shield_recharge_delay_counter >= self.shield_recharge_delay:
                    self.shield_recharge_delay_counter = 0
                    self.shield_recharge_delay_blinking_effect_counter = 0
                    self.shield_recharge_delay_active = False
                    self.shield_is_recharging = True
                    self.color = self.original_color
            if self.shield_is_recharging:
                self.health = min(self.health + self.shield_recharge_rate, self.maximum_health)
            if self.health == self.maximum_health:
                self.shield_is_recharging = False
            self.fire_rate_counter = min(self.fire_rate_counter + 1, self.fire_rate)
            if self.current_target_enemy is not None:
                self.current_target_enemy_distance = euclidean_distance(self.coordinates_center, self.current_target_enemy.coordinates_center)
            self.enemy_engagement_artificial_intelligence(globals.soldiers_dict.values())
            self.movement_ai(globals.dt, self.find_best_capture_point())

    def determine_damage_falloff(self):
        if self.weapon_type == "short range":
            self.damage_falloff[(0, 200)] = 7
            self.damage_falloff[(200, 500)] = 5
            self.damage_falloff[(500, 3000)] = 3
        elif self.weapon_type == "med range":
            self.damage_falloff[(0, 200)] = 6
            self.damage_falloff[(200, 500)] = 6
            self.damage_falloff[(500, 3000)] = 3
        elif self.weapon_type == "long range":
            self.damage_falloff[(0, 200)] = 5
            self.damage_falloff[(200, 500)] = 5
            self.damage_falloff[(500, 3000)] = 5

    def draw(self):
        if self.show_rays:
            self.draw_rays()
        if self.show_destination_queue:
            for destination in self.destination_queue:
                draw.circle(self.win, globals.GREEN, (destination.x, destination.y), 7)
        if self.alive:
            if self.shield_recharge_delay_active:
                if self.shield_recharge_delay_blinking_effect_counter % self.shield_recharge_delay_blinking_effect_rate == 0 and self.color == self.original_color:
                    self.color = self.shield_recharge_delay_active_color
                elif self.shield_recharge_delay_blinking_effect_counter % self.shield_recharge_delay_blinking_effect_rate == 0 and self.color == self.shield_recharge_delay_active_color:
                    self.color = self.original_color
        super().draw()

    def draw_rays(self):
        for ray in self.ray_list:
            ray_end_coordinate = ray[0]
            ray_color = ray[1]
            draw.line(self.win, ray_color, (self.coordinates_center.x, self.coordinates_center.y), (ray_end_coordinate.x, ray_end_coordinate.y), width=1)

    def add_to_destination_queue(self, destination):
        if not isinstance(destination, Point): raise ValueError("destination has to be a Point object")
        self.destination_queue.insert(0, destination)

    def get_next_destination_from_queue(self):
        return self.destination_queue.pop()

    def cancel_move(self):
        self.destination = None
        self.is_moving = False

    def cancel_all_queued_moves(self):
        self.destination = None
        self.is_moving = False
        self.destination_queue = []

    def move(self, dt, destination=None):
        if not isinstance(destination, Point) and destination is not None: raise TypeError("destination has to be a Point object")
        if not self.alive:
            return
        if self.shooting:
            return
        if destination is None and self.destination is None:
            if not self.destination_queue:
                return
            else:
                self.destination = self.get_next_destination_from_queue()
                self.is_moving = True
        if destination is not None:
            if destination.x == self.coordinates_center.x and destination.y == self.coordinates_center.y:
                return
            self.destination = destination
            self.is_moving = True
        distance = self.movement_speed * dt
        component_distances = calculate_component_distances(distance_moved=distance, start_x=self.coordinates_center.x,
                                                            start_y=self.coordinates_center.y, end_x=self.destination.x,
                                                            end_y=self.destination.y)
        new_coordinates_center = Point(self.coordinates_center.x + component_distances.x, self.coordinates_center.y + component_distances.y)
        # Check for collisions with nearby walls
        if self.enable_collisions:
            for adjacent_grid_position in self.adjacent_grid_positions:
                adjacent_grid_position_row = adjacent_grid_position[0]
                adjacent_grid_position_col = adjacent_grid_position[1]
                square_coordinates = Point(0, 0)
                cancel_move_flag = False
                if adjacent_grid_position_col < 0:
                    cancel_move_flag = True
                    square_coordinates.x = 0 - self.map.grid_width
                    square_coordinates.y = self.coordinates_center.y
                elif adjacent_grid_position_col == self.map.ncols:
                    cancel_move_flag = True
                    square_coordinates.x = globals.WIN_WIDTH
                    square_coordinates.y = self.coordinates_center.y
                elif adjacent_grid_position_row < 0:
                    cancel_move_flag = True
                    square_coordinates.x = self.coordinates_center.x
                    square_coordinates.y = 0 - self.map.grid_width
                elif adjacent_grid_position_row == self.map.nrows:
                    cancel_move_flag = True
                    square_coordinates.x = self.coordinates_center.x
                    square_coordinates.y = globals.WIN_HEIGHT
                if not cancel_move_flag:
                    if self.map.map_array[adjacent_grid_position_row][adjacent_grid_position_col] == 1:
                        cancel_move_flag = True
                        square_coordinates = self.map.grid_coordinates[adjacent_grid_position_row][adjacent_grid_position_col]
                        square_coordinates = Point(square_coordinates[0], square_coordinates[1])
                if cancel_move_flag:
                    if point_overlaps_with_rect(new_coordinates_center, square_coordinates, self.map.grid_width, self.map.grid_width):
                        self.cancel_move()
                        return
        if euclidean_distance(self.coordinates_center, self.destination) <= distance:
            self.coordinates_center = self.destination.get_coordinates()
            self.coordinates.x = self.coordinates_center.x - self.width / 2
            self.coordinates.y = self.coordinates_center.y - self.width / 2
            self.cancel_move()
        else:
            component_distances = calculate_component_distances(distance_moved=distance, start_x=self.coordinates_center.x,
                                                                start_y=self.coordinates_center.y, end_x=self.destination.x,
                                                                end_y=self.destination.y)
            self.coordinates_center.x += component_distances.x
            self.coordinates_center.y += component_distances.y
            self.coordinates.x += component_distances.x
            self.coordinates.y += component_distances.y

    def move_random(self, dt, probability_of_changing_destination):
        if self.alive:
            random_number = random()
            if random_number <= probability_of_changing_destination or self.destination is None:
                if not self.destination_queue:
                    random_destination_x = random() * globals.WIN_WIDTH
                    random_destination_y = random() * globals.WIN_HEIGHT
                    self.add_to_destination_queue(Point(random_destination_x, random_destination_y))
        self.move(dt)

    def move_astar(self, dt, destination):
        """Use the A* Algorithm to find path to destination"""
        destination_grid_position = self.map.get_grid_position_of_point(destination)
        if self.destination_queue or self.is_moving:
            self.move(dt)
            return
        # Determine grid position of destination
        if destination_grid_position == self.grid_position:
            return
        def reconstruct_path(came_from, current_node):
            total_path = []
            current_node_coordinates_center = self.map.grid_coordinates[current_node[0]][current_node[1]]
            total_path.append(Point(current_node_coordinates_center[0] + self.map.grid_width / 2,
                                    current_node_coordinates_center[1] + self.map.grid_width / 2))
            while current_node in came_from.keys():
                current_node = came_from[current_node]
                current_node_coordinates_center = self.map.grid_coordinates[current_node[0]][current_node[1]]
                total_path.append(Point(current_node_coordinates_center[0] + self.map.grid_width / 2,
                                        current_node_coordinates_center[1] + self.map.grid_width / 2))
            return total_path
        def heuristic_function(grid_position):
            """Calculates euclidean distance"""
            grid_position_coordinates_center = self.map.grid_coordinates[grid_position[0]][grid_position[1]]
            destination_grid_position_coordinates_center = self.map.grid_coordinates[destination_grid_position[0]][destination_grid_position[1]]
            return int(euclidean_distance(Point(grid_position_coordinates_center[0] + self.map.grid_width / 2, grid_position_coordinates_center[1] + self.map.grid_width / 2),
                                          Point(destination_grid_position_coordinates_center[0] + self.map.grid_width / 2, destination_grid_position_coordinates_center[1] + self.map.grid_width / 2)))
        open_set = [self.grid_position]
        came_from = {}
        g_scores = {self.grid_position: 0}
        f_scores = {self.grid_position: heuristic_function(self.grid_position)}
        current_node = None
        distance_to_corner_neighbor = sqrt(2 * (abs(self.map.grid_width) ** 2))
        while open_set:
            # Determine lowest f-score node
            lowest_f_score_node = None
            for node in open_set:
                if lowest_f_score_node is None:
                    lowest_f_score_node = node
                elif f_scores[node] < f_scores[lowest_f_score_node]:
                    lowest_f_score_node = node
            current_node = lowest_f_score_node
            if current_node == destination_grid_position:
                total_path = reconstruct_path(came_from, current_node)
                for i in range(0, len(total_path)):
                    next_node = total_path.pop()
                    self.add_to_destination_queue(next_node)
                self.move(dt)
                return
            open_set.remove(current_node)
            corner_neighbors = self.map.get_neighboring_corner_grid_positions(current_node)
            edge_neighbors = self.map.get_neighboring_edge_grid_positions(current_node)
            for corner_neighbor in corner_neighbors:
                if corner_neighbor[1] < 0 or corner_neighbor[1] > self.map.ncols - 1:
                    continue
                if corner_neighbor[0] < 0 or corner_neighbor[0] > self.map.nrows - 1:
                    continue
                if self.enable_collisions:
                    if self.map.map_array[corner_neighbor[0]][corner_neighbor[1]] == 1:
                        continue
                    # This is to prevent movement diagonally through two touching wall's corners
                    corner_neighbor_row = corner_neighbor[0]
                    corner_neighbor_col = corner_neighbor[1]
                    current_node_row = current_node[0]
                    current_node_col = current_node[1]
                    relative_row_position_to_current_node = corner_neighbor_row - current_node_row
                    relative_col_position_to_current_node = corner_neighbor_col - current_node_col
                    if self.map.map_array[current_node_row][current_node_col + relative_col_position_to_current_node] == 1 and self.map.map_array[current_node_row + relative_row_position_to_current_node][current_node_col] == 1:
                        continue
                tentative_g_score = g_scores[current_node] + distance_to_corner_neighbor
                better_path = False
                if g_scores.setdefault(corner_neighbor, None) is None:
                    better_path = True
                elif tentative_g_score < g_scores[corner_neighbor]:
                    better_path = True
                if better_path:
                    came_from[corner_neighbor] = current_node
                    g_scores[corner_neighbor] = tentative_g_score
                    f_scores[corner_neighbor] = tentative_g_score + heuristic_function(corner_neighbor)
                    if corner_neighbor not in open_set:
                        open_set.append(corner_neighbor)
            for edge_neighbor in edge_neighbors:
                if edge_neighbor[1] < 0 or edge_neighbor[1] > self.map.ncols - 1:
                    continue
                if edge_neighbor[0] < 0 or edge_neighbor[0] > self.map.nrows - 1:
                    continue
                if self.map.map_array[edge_neighbor[0]][edge_neighbor[1]] == 1 and self.enable_collisions:
                    continue
                tentative_g_score = g_scores[current_node] + self.map.grid_width
                better_path = False
                if g_scores.setdefault(edge_neighbor, None) is None:
                    better_path = True
                elif tentative_g_score < g_scores[edge_neighbor]:
                    better_path = True
                if better_path:
                    came_from[edge_neighbor] = current_node
                    g_scores[edge_neighbor] = tentative_g_score
                    f_scores[edge_neighbor] = tentative_g_score + heuristic_function(edge_neighbor)
                    if edge_neighbor not in open_set:
                        open_set.append(edge_neighbor)
        return

    def movement_ai(self, dt, capture_point):
        if self.alive:
            if capture_point is None:
                self.move_random(dt=dt, probability_of_changing_destination=0.01)
                return
            if not self.moving_to_point:
                probability_of_deciding_to_move_to_point = 0.003
                if random() <= probability_of_deciding_to_move_to_point:
                    if capture_point.current_faction != self.faction:
                        distance_to_point = euclidean_distance(self.coordinates_center, capture_point.coordinates_center)
                        if distance_to_point > capture_point.capture_radius:
                            self.move_astar(dt=dt, destination=capture_point.coordinates_center)
                            self.moving_to_point = True
                        else:
                            if distance_to_point < capture_point.capture_radius / 4:
                                if self.moving_to_point:
                                    self.cancel_all_queued_moves()
                                self.move_random(dt=dt, probability_of_changing_destination=0.01)
                                self.moving_to_point = False
                            else:
                                self.move_astar(dt=dt, destination=capture_point.coordinates_center)
                                self.moving_to_point = True
                    else:
                        self.move_random(dt=dt, probability_of_changing_destination=0.01)
                        self.moving_to_point = False
                else:
                    self.move_random(dt=dt, probability_of_changing_destination=0.01)
                    self.moving_to_point = False
            elif self.moving_to_point:
                probability_of_deciding_not_to_move_to_point_anymore = 0.001
                if random() <= probability_of_deciding_not_to_move_to_point_anymore:
                    self.cancel_all_queued_moves()
                    self.moving_to_point = False
                self.move_astar(dt=dt, destination=capture_point.coordinates_center)

    def shoot_ray(self, angle, collide=True):
        if not self.alive:
            return
        large_circle_outside_view_radius = 3000
        unit_circle_coordinates = get_point_on_unit_circle(angle)
        point_on_large_circle = Point((unit_circle_coordinates.x * large_circle_outside_view_radius + self.coordinates_center.x),
                                      (unit_circle_coordinates.y * -large_circle_outside_view_radius) + self.coordinates_center.y)
        if not collide:
            self.ray_list.append((point_on_large_circle, WHITE))
        else:
            if angle in (0, 180):
                is_vertical = True
                slope = 0
                intercept = 0
                x_value = self.coordinates_center.x
            else:
                is_vertical = False
                equation_of_line = find_equation_of_line(self.coordinates_center, point_on_large_circle)
                slope = equation_of_line[1]
                intercept = equation_of_line[2]
                x_value = None
            ray = Ray(angle=angle, slope=slope, intercept=intercept, is_vertical=is_vertical, x_value=x_value)
            end_point_of_ray = self.get_collision_point_of_ray(ray)
            if end_point_of_ray is not None:
                self.ray_list.append((end_point_of_ray, WHITE))
            else:
                self.ray_list.append((point_on_large_circle, WHITE))

    def get_collision_point_of_ray(self, ray):
        if not isinstance(ray, Ray): raise ValueError("ray has to be a Ray object")
        current_grid_row_index = self.grid_position[0]
        current_grid_col_index = self.grid_position[1]
        if self.map.grid_coordinates[current_grid_row_index][current_grid_col_index] == 1:
            return self.coordinates_center.get_coordinates()
        # If line goes straight up then search grid squares straight above for walls and collide with first one encountered on its bottom line
        if ray.angle == 0:
            if current_grid_row_index == 0:
                return None
            for row_index in range(current_grid_row_index - 1, -1, -1):
                if self.map.map_array[row_index][current_grid_col_index] == 1:
                    return Point(self.coordinates_center.x, self.map.grid_coordinates[row_index][current_grid_col_index][1] + self.map.grid_width)
            return None
        elif ray.angle == 180:
            if current_grid_row_index == self.map.nrows - 1:
                return None
            for row_index in range(current_grid_row_index + 1, self.map.nrows):
                if self.map.map_array[row_index][current_grid_col_index] == 1:
                    return Point(self.coordinates_center.x, self.map.grid_coordinates[row_index][current_grid_col_index][1])
            return None
        elif ray.angle == 90:
            if current_grid_col_index == self.map.ncols - 1:
                return None
            for col_index in range(current_grid_col_index + 1, self.map.ncols):
                if self.map.map_array[current_grid_row_index][col_index] == 1:
                    return Point(self.map.grid_coordinates[current_grid_row_index][col_index][0], self.coordinates_center.y)
            return None
        elif ray.angle == 270:
            if current_grid_col_index == 0:
                return None
            for col_index in range(current_grid_col_index - 1, -1, -1):
                if self.map.map_array[current_grid_row_index][col_index] == 1:
                    return Point(self.map.grid_coordinates[current_grid_row_index][col_index][0] + self.map.grid_width, self.coordinates_center.y)
            return None
        elif 0 < ray.angle < 90:
            while current_grid_row_index != -1 and current_grid_col_index != self.map.ncols:
                if current_grid_row_index == 0 and current_grid_col_index == self.map.ncols - 1:
                    return None
                elif current_grid_col_index != self.map.ncols - 1:
                    grid_square_to_the_right_coordinates = self.map.grid_coordinates[current_grid_row_index][current_grid_col_index + 1]
                    y_value_of_ray_at_x_value_of_grid_square_to_the_right = ray.slope * grid_square_to_the_right_coordinates[0] + ray.intercept
                    # If it intersects
                    if grid_square_to_the_right_coordinates[1] <= y_value_of_ray_at_x_value_of_grid_square_to_the_right <= grid_square_to_the_right_coordinates[1] + self.map.grid_width:
                        current_grid_col_index += 1
                        if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                            left_edge_of_grid_square_line = Line(slope=0, intercept=0, is_vertical=True, x_value=grid_square_to_the_right_coordinates[0])
                            return get_intersection_point_of_lines(ray, left_edge_of_grid_square_line)
                    # Else it must mean that it intersects with the bottom edge of the grid square above
                    else:
                        if current_grid_row_index == 0:
                            return None
                        else:
                            grid_square_above_coordinates = self.map.grid_coordinates[current_grid_row_index - 1][current_grid_col_index]
                            current_grid_row_index -= 1
                            if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                                bottom_edge_of_grid_square_line = Line(slope=0, intercept=grid_square_above_coordinates[1] + self.map.grid_width, is_vertical=False)
                                return get_intersection_point_of_lines(ray, bottom_edge_of_grid_square_line)
                else:
                    grid_square_above_coordinates = self.map.grid_coordinates[current_grid_row_index - 1][current_grid_col_index]
                    x_value_of_ray_at_y_value_of_grid_square_above = (grid_square_above_coordinates[1] + self.map.grid_width - ray.intercept) / ray.slope
                    # If it intersects
                    if grid_square_above_coordinates[0] <= x_value_of_ray_at_y_value_of_grid_square_above <= grid_square_above_coordinates[0] + self.map.grid_width:
                        current_grid_row_index -= 1
                        if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                            bottom_edge_of_grid_square_line = Line(slope=0, intercept=grid_square_above_coordinates[1] + self.map.grid_width, is_vertical=False)
                            return get_intersection_point_of_lines(ray, bottom_edge_of_grid_square_line)
                    else:
                        return None
        elif 90 < ray.angle < 180:
            while current_grid_row_index != self.map.nrows and current_grid_col_index != self.map.ncols:
                if current_grid_row_index == self.map.nrows - 1 and current_grid_col_index == self.map.ncols - 1:
                    return None
                elif current_grid_col_index != self.map.ncols - 1:
                    grid_square_to_the_right_coordinates = self.map.grid_coordinates[current_grid_row_index][current_grid_col_index + 1]
                    y_value_of_ray_at_x_value_of_grid_square_to_the_right = ray.slope * grid_square_to_the_right_coordinates[0] + ray.intercept
                    # If it intersects
                    if grid_square_to_the_right_coordinates[1] <= y_value_of_ray_at_x_value_of_grid_square_to_the_right <= grid_square_to_the_right_coordinates[1] + self.map.grid_width:
                        current_grid_col_index += 1
                        if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                            left_edge_of_grid_square_line = Line(slope=0, intercept=0, is_vertical=True, x_value=grid_square_to_the_right_coordinates[0])
                            return get_intersection_point_of_lines(ray, left_edge_of_grid_square_line)
                    # Else it must mean that it intersects with the top edge of the grid square below
                    else:
                        if current_grid_row_index == self.map.nrows - 1:
                            return None
                        else:
                            grid_square_below_coordinates = self.map.grid_coordinates[current_grid_row_index + 1][current_grid_col_index]
                            current_grid_row_index += 1
                            if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                                top_edge_of_grid_square_line = Line(slope=0, intercept=grid_square_below_coordinates[1], is_vertical=False)
                                return get_intersection_point_of_lines(ray, top_edge_of_grid_square_line)
                else:
                    grid_square_below_coordinates = self.map.grid_coordinates[current_grid_row_index + 1][current_grid_col_index]
                    x_value_of_ray_at_y_value_of_grid_square_below = (grid_square_below_coordinates[1] - ray.intercept) / ray.slope
                    # If it intersects
                    if grid_square_below_coordinates[0] <= x_value_of_ray_at_y_value_of_grid_square_below <= grid_square_below_coordinates[0] + self.map.grid_width:
                        current_grid_row_index += 1
                        if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                            top_edge_of_grid_square_line = Line(slope=0, intercept=grid_square_below_coordinates[1], is_vertical=False)
                            return get_intersection_point_of_lines(ray, top_edge_of_grid_square_line)
                    else:
                        return None
        elif 180 < ray.angle < 270:
            while current_grid_row_index != self.map.nrows and current_grid_col_index != -1:
                if current_grid_row_index == self.map.nrows - 1 and current_grid_col_index == 0:
                    return None
                elif current_grid_col_index != 0:
                    grid_square_to_the_left_coordinates = self.map.grid_coordinates[current_grid_row_index][current_grid_col_index - 1]
                    y_value_of_ray_at_x_value_of_grid_square_to_the_left = ray.slope * (grid_square_to_the_left_coordinates[0] + self.map.grid_width) + ray.intercept
                    # If it intersects
                    if grid_square_to_the_left_coordinates[1] <= y_value_of_ray_at_x_value_of_grid_square_to_the_left <= grid_square_to_the_left_coordinates[1] + self.map.grid_width:
                        current_grid_col_index -= 1
                        if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                            right_edge_of_grid_square_line = Line(slope=0, intercept=0, is_vertical=True, x_value=grid_square_to_the_left_coordinates[0] + self.map.grid_width)
                            return get_intersection_point_of_lines(ray, right_edge_of_grid_square_line)
                    # Else it must mean that it intersects with the top edge of the grid square below
                    else:
                        if current_grid_row_index == self.map.nrows - 1:
                            return None
                        else:
                            grid_square_below_coordinates = self.map.grid_coordinates[current_grid_row_index + 1][current_grid_col_index]
                            current_grid_row_index += 1
                            if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                                top_edge_of_grid_square_line = Line(slope=0, intercept=grid_square_below_coordinates[1], is_vertical=False)
                                return get_intersection_point_of_lines(ray, top_edge_of_grid_square_line)
                else:
                    grid_square_below_coordinates = self.map.grid_coordinates[current_grid_row_index + 1][current_grid_col_index]
                    x_value_of_ray_at_y_value_of_grid_square_below = (grid_square_below_coordinates[1] - ray.intercept) / ray.slope
                    # If it intersects
                    if grid_square_below_coordinates[0] <= x_value_of_ray_at_y_value_of_grid_square_below <= grid_square_below_coordinates[0] + self.map.grid_width:
                        current_grid_row_index += 1
                        if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                            top_edge_of_grid_square_line = Line(slope=0, intercept=grid_square_below_coordinates[1], is_vertical=False)
                            return get_intersection_point_of_lines(ray, top_edge_of_grid_square_line)
                    else:
                        return None
        elif ray.angle > 270:
            while current_grid_row_index != -1 and current_grid_col_index != -1:
                if current_grid_row_index == 0 and current_grid_col_index == 0:
                    return None
                elif current_grid_col_index != 0:
                    grid_square_to_the_left_coordinates = self.map.grid_coordinates[current_grid_row_index][current_grid_col_index - 1]
                    y_value_of_ray_at_x_value_of_grid_square_to_the_left = ray.slope * (grid_square_to_the_left_coordinates[0] + self.map.grid_width) + ray.intercept
                    # If it intersects
                    if grid_square_to_the_left_coordinates[1] <= y_value_of_ray_at_x_value_of_grid_square_to_the_left <= grid_square_to_the_left_coordinates[1] + self.map.grid_width:
                        current_grid_col_index -= 1
                        if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                            right_edge_of_grid_square_line = Line(slope=0, intercept=0, is_vertical=True, x_value=grid_square_to_the_left_coordinates[0] + self.map.grid_width)
                            return get_intersection_point_of_lines(ray, right_edge_of_grid_square_line)
                    # Else it must mean that it intersects with the bottom edge of the grid square above
                    else:
                        if current_grid_row_index == 0:
                            return None
                        else:
                            grid_square_above_coordinates = self.map.grid_coordinates[current_grid_row_index - 1][current_grid_col_index]
                            current_grid_row_index -= 1
                            if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                                bottom_edge_of_grid_square_line = Line(slope=0, intercept=grid_square_above_coordinates[1] + self.map.grid_width, is_vertical=False)
                                return get_intersection_point_of_lines(ray, bottom_edge_of_grid_square_line)
                else:
                    grid_square_above_coordinates = self.map.grid_coordinates[current_grid_row_index - 1][current_grid_col_index]
                    x_value_of_ray_at_y_value_of_grid_square_above = (grid_square_above_coordinates[1] + self.map.grid_width - ray.intercept) / ray.slope
                    # If it intersects
                    if grid_square_above_coordinates[0] <= x_value_of_ray_at_y_value_of_grid_square_above <= grid_square_above_coordinates[0] + self.map.grid_width:
                        current_grid_row_index -= 1
                        if self.map.map_array[current_grid_row_index][current_grid_col_index] == 1:
                            bottom_edge_of_grid_square_line = Line(slope=0, intercept=grid_square_above_coordinates[1] + self.map.grid_width, is_vertical=False)
                            return get_intersection_point_of_lines(ray, bottom_edge_of_grid_square_line)
                    else:
                        return None

    def find_enemy_target(self, list_of_enemies):
        if self.current_target_enemy is not None:
            ray_line = find_equation_of_line(self.coordinates_center, self.current_target_enemy.coordinates_center)
            ray = Ray(angle=find_angle_of_line(self.coordinates_center, self.current_target_enemy.coordinates_center),
                      slope=ray_line[1], intercept=ray_line[2], is_vertical=ray_line[0], x_value=ray_line[3])
            ray_collision_point = self.get_collision_point_of_ray(ray)
            if ray_collision_point is None:
                return self.current_target_enemy, self.current_target_enemy_distance
            else:
                if self.current_target_enemy_distance <= euclidean_distance(self.coordinates_center, ray_collision_point):
                    return self.current_target_enemy, self.current_target_enemy_distance
        best_enemy = None
        best_enemy_distance = None
        for enemy in list_of_enemies:
            if enemy.faction == self.faction:
                continue
            if not enemy.alive:
                continue
            distance_to_enemy = euclidean_distance(self.coordinates_center, enemy.coordinates_center)
            if best_enemy is None and distance_to_enemy <= self.enemy_engagement_range:
                ray_line = find_equation_of_line(self.coordinates_center, enemy.coordinates_center)
                ray = Ray(angle=find_angle_of_line(self.coordinates_center, enemy.coordinates_center),
                          slope=ray_line[1], intercept=ray_line[2], is_vertical=ray_line[0], x_value=ray_line[3])
                ray_collision_point = self.get_collision_point_of_ray(ray)
                if ray_collision_point is not None:
                    if distance_to_enemy > euclidean_distance(self.coordinates_center, ray_collision_point):
                        continue
                best_enemy = enemy
                best_enemy_distance = distance_to_enemy
            elif distance_to_enemy <= self.enemy_engagement_range and distance_to_enemy < best_enemy_distance:
                ray_line = find_equation_of_line(self.coordinates_center, enemy.coordinates_center)
                ray = Ray(angle=find_angle_of_line(self.coordinates_center, enemy.coordinates_center),
                          slope=ray_line[1], intercept=ray_line[2], is_vertical=ray_line[0], x_value=ray_line[3])
                ray_collision_point = self.get_collision_point_of_ray(ray)
                if ray_collision_point is not None:
                    if distance_to_enemy > euclidean_distance(self.coordinates_center, ray_collision_point):
                        continue
                best_enemy = enemy
                best_enemy_distance = distance_to_enemy
        return best_enemy, best_enemy_distance

    def shoot_enemy(self, enemy):
        if self.fire_rate_counter == self.fire_rate:
            self.shooting = True
            self.fire_rate_counter = 0
            damage_dealt = None
            for damage_falloff_range, damage in self.damage_falloff.items():
                if damage_falloff_range[0] <= self.current_target_enemy_distance <= damage_falloff_range[1]:
                    damage_dealt = damage
            if random() <= self.aim_factor:
                enemy.health -= damage_dealt
                enemy.shield_recharge_delay_active = True
                enemy.shield_recharge_delay_counter = 0
                if enemy.health <= 0:
                    self.kills += 1
                    self.shooting = False
                    self.current_target_enemy = None
                    self.current_target_enemy_distance = None
            self.ray_list.append((Point(enemy.coordinates_center.x, enemy.coordinates_center.y), self.original_color))

    def enemy_engagement_artificial_intelligence(self, enemy_list):
        if self.alive:
            enemy_target_info = self.find_enemy_target(enemy_list)
            self.current_target_enemy = enemy_target_info[0]
            self.current_target_enemy_distance = enemy_target_info[1]
            if self.current_target_enemy is not None:
                if self.current_target_enemy.health <= 0:
                    self.shooting = False
                    self.current_target_enemy.getting_shot_at = False
                    self.current_target_enemy = None
                    self.current_target_enemy_distance = None
                else:
                    self.current_target_enemy.getting_shot_at = True
                    self.shoot_enemy(self.current_target_enemy)
            else:
                self.shooting = False

    def find_best_spawn_point(self, list_of_spawn_points):
        if not self.alive and list_of_spawn_points:
            best_spawn_point = None
            faction_spawn_point_list = []
            for spawn_point in list_of_spawn_points:
                if spawn_point.faction == self.faction:
                    faction_spawn_point_list.append(spawn_point)
            if faction_spawn_point_list:
                best_spawn_point = choice(faction_spawn_point_list)
            return best_spawn_point

    def find_best_capture_point(self):
        if self.alive:
            best_capture_point = None
            capture_point_list = globals.capture_point_dict.values()
            for capture_point in capture_point_list:
                if best_capture_point is None:
                    best_capture_point = capture_point
                elif best_capture_point.current_faction == self.faction and capture_point.current_faction != self.faction:
                    best_capture_point = capture_point
                elif best_capture_point.current_faction != self.faction and capture_point.current_faction != self.faction:
                    if euclidean_distance(self.coordinates_center, best_capture_point.coordinates_center) > euclidean_distance(self.coordinates_center, capture_point.coordinates_center):
                        best_capture_point = capture_point
            return best_capture_point

    def spawn(self, spawn_point):
        if not isinstance(spawn_point, SpawnPoint) and spawn_point is not None: raise ValueError("spawn_point has to be a SpawnPoint or None")
        if not self.alive and spawn_point is not None:
            if self.spawn_timer_counter >= spawn_point.spawn_timer:
                self.coordinates = spawn_point.coordinates.get_coordinates()
                self.coordinates_center = spawn_point.coordinates_center.get_coordinates()
                self.current_target_enemy = None
                self.current_target_enemy_distance = None
                self.destination = None
                self.destination_queue = []
                self.health = self.maximum_health
                self.shield_recharge_delay_blinking_effect_counter = 0
                self.shield_recharge_delay_counter = 0
                self.shield_recharge_delay_active = False
                self.shield_is_recharging = False
                self.alive = True
                self.color = self.original_color
                self.spawn_timer_counter = 0


class CapturePoint(Entity):

    def __init__(self, win, map, id, coordinates, faction="Neutral"):
        if faction != "Neutral" and faction not in globals.FACTION_LIST: raise TypeError("faction has to be None or a valid faction")
        shape = "circle"
        width = 10
        neutral_color = globals.YELLOW
        super().__init__(win, map, id, shape, width, neutral_color, coordinates)
        self.capture_radius = 40
        self.current_faction = faction
        self.neutral_color = neutral_color
        self.time_to_be_flipped = 100
        self.time_to_be_flipped_counter = 0
        self.draw_radius = True

    def update_at_start_of_frame(self):
        super().update_at_start_of_frame()
        list_of_soldiers = globals.soldiers_dict.values()
        faction_counter = {"TR": 0, "NC": 0, "VS": 0, "Contested": 0}
        for soldier in list_of_soldiers:
            if soldier.alive:
                if euclidean_distance(self.coordinates_center, soldier.coordinates_center) <= self.capture_radius:
                    faction_counter[soldier.faction] += 1
        if not (faction_counter["TR"] == faction_counter["NC"] and faction_counter["NC"] == faction_counter["VS"]):
            self.time_to_be_flipped_counter = min(self.time_to_be_flipped_counter + 1, self.time_to_be_flipped)
            faction_owner = None
            for faction in faction_counter:
                if faction == "Contested":
                    continue
                if faction_owner is None:
                    faction_owner = faction
                elif faction_counter[faction] == faction_counter[faction_owner]:
                    faction_owner = "Contested"
                    faction_counter["Contested"] = faction_counter[faction]
                elif faction_counter[faction] > faction_counter[faction_owner]:
                    faction_owner = faction
            if faction_owner != self.current_faction and faction_owner != "Contested":
                if self.time_to_be_flipped_counter == self.time_to_be_flipped:
                    if self.current_faction != "Neutral":
                        self.current_faction = "Neutral"
                    else:
                        self.current_faction = faction_owner
                    self.time_to_be_flipped_counter = 0
        else:
            self.time_to_be_flipped_counter = max(self.time_to_be_flipped_counter - 1, 0)

    def draw(self):
        if self.draw_radius:
            draw.circle(self.win, globals.WHITE, (self.coordinates_center.x, self.coordinates_center.y), self.capture_radius, width=1)
        if self.current_faction == "Neutral":
            self.color = self.neutral_color
        elif self.current_faction == "TR":
            self.color = globals.FactionColor.TR.value
        elif self.current_faction == "NC":
            self.color = globals.FactionColor.NC.value
        elif self.current_faction == "VS":
            self.color = globals.FactionColor.VS.value
        super().draw()


class SpawnPoint(Entity):

    def __init__(self, win, map, id, shape, width, color, coordinates, faction):
        if faction not in ("TR", "NC", "VS"): raise ValueError("faction has to be valid")
        super().__init__(win, map, id, shape, width, color, coordinates)
        self.spawn_timer = 0
        self.faction = faction


class Sunderer(SpawnPoint):

    def __init__(self, win, map, id, coordinates, faction):
        shape = "circle"
        width = 15
        color = globals.FactionColor[faction].value
        super().__init__(win, map, id, shape, width, color, coordinates, faction)
        self.spawn_timer = 2000


