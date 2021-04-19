"""Class for managing Pages (e.g. main menu, options, game, etc.)"""
from utility import *
import globals
from entity import *
from map import *
import pygame
from random import random, choice, randint
import sys
import _pickle


class Page:

    def __init__(self, win, name, clock, bg_color):
        if not isinstance(win, pygame.Surface): raise TypeError("window has to be a pygame.Surface object")
        if not is_string(name): raise TypeError("name has to be a string")
        if not isinstance(clock, type(pygame.time.Clock())): raise TypeError("clock has to be a pygame.time.Clock object")
        if not is_rgb_color_value(bg_color) and bg_color is not None: raise TypeError("bg_color has to be a RGB tuple")
        self.win = win
        self.name = name
        self.clock = clock
        self.bg_color = bg_color

    def mainloop(self):
        pass


class SimulationPage(Page):

    def __init__(self, win, name, clock, bg_color=None):
        super().__init__(win, name, clock, bg_color)
        # Font
        self.font = pygame.font.SysFont("Times New Roman", 30, bold=True)
        self.button_font = pygame.font.SysFont("Times New Roman", 20, bold=False)

        # Screenshots
        self.take_screenshots = False
        self.frame_counter = 0

        # Map
        self.map_name = None
        self.map = None
        self.load_map()

    def mainloop(self):
        while True:

            # This is for if the user closes the tkinter window (the main thread) while pygame is running
            # This allows for the pygame thread to terminate using the thread.join() method before calling sys.exit()
            # for the main thread to terminate as well
            if not globals.pygame_running:
                break

            # Time since last clock tick
            globals.dt = self.clock.tick(globals.FPS)
            # Do not use dt if taking screenshots
            if self.take_screenshots and not globals.paused:
                globals.dt = 1

            # Update mouse position
            mouse_pos = pygame.mouse.get_pos()
            mouse_pos = Point(mouse_pos[0], mouse_pos[1])
            mouse_pos_grid_position = self.map.get_grid_position_of_point(mouse_pos)

            # Update entities
            for entity in globals.entity_list:
                entity.update_at_start_of_frame()

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if pygame.mouse.get_pressed()[0]:
                        # If the user is placing a spawn point
                        if globals.spawn_being_placed:
                            if self.map.map_array[mouse_pos_grid_position[0]][mouse_pos_grid_position[1]] == 0:
                                self.create_spawn_point(mouse_pos)
                        elif globals.capture_point_being_placed:
                            if self.map.map_array[mouse_pos_grid_position[0]][mouse_pos_grid_position[1]] == 0:
                                self.create_capture_point(mouse_pos)

            # Updates Based on Changes in Tkinter Options
            if globals.soldiers_being_added:
                globals.soldiers_being_added = False
                for i in range(0, globals.number_of_NC_to_add):
                    random_weapon_type = choice(globals.WEAPON_TYPES)
                    aim_factor = min(random() + 0.3, 1)
                    self.create_soldier(faction="NC", weapon_type=random_weapon_type, aim_factor=aim_factor)
                for i in range(0, globals.number_of_TR_to_add):
                    random_weapon_type = choice(globals.WEAPON_TYPES)
                    aim_factor = min(random() + 0.3, 1)
                    self.create_soldier(faction="TR", weapon_type=random_weapon_type, aim_factor=aim_factor)
                for i in range(0, globals.number_of_VS_to_add):
                    random_weapon_type = choice(globals.WEAPON_TYPES)
                    aim_factor = min(random() + 0.3, 1)
                    self.create_soldier(faction="VS", weapon_type=random_weapon_type, aim_factor=aim_factor)

            # Simulation Logic
            if not globals.paused:
                pass

            """DRAW STUFF BELOW"""
            self.win.fill(globals.BLACK)
            if self.map.show_gridlines:
                self.map.draw_gridlines()
            for entity in globals.entity_list:
                entity.draw()
            self.map.draw()

            # Update frame
            pygame.display.update()
            if self.take_screenshots:
                pygame.image.save(self.win, f"./Images/screenshot{self.frame_counter}.jpg")
                self.frame_counter += 1

    def load_map(self):
        self.map_name = globals.map_name
        if self.map_name == "Blank":
            map_array = globals.MAP_BLANK
        elif self.map_name == "Randomly Generated":
            map_array = globals.generate_random_map()
        else:
            with open(f"./Maps/{self.map_name}.txt", "rb") as f:
                map_array = _pickle.load(f)
        self.map = Map(win=self.win, map_array=map_array, wall_color=globals.BROWNISH_GREY)

    def create_spawn_point(self, coordinates):
        if globals.spawn_being_placed_type == "Sunderer":
            new_spawn_point = Sunderer(win=self.win, map=self.map, id=globals.next_spawn_dict_key,
                                       coordinates=coordinates, faction=globals.spawn_being_placed_faction)
            globals.spawn_point_dict[globals.next_spawn_dict_key] = new_spawn_point
            globals.entity_list.append(new_spawn_point)
            globals.next_spawn_dict_key += 1

    def create_capture_point(self, coordinates):
        new_capture_point = CapturePoint(win=self.win, map=self.map, id=globals.next_capture_point_dict_key,
                                         coordinates=coordinates, faction=globals.capture_point_being_placed_faction)
        globals.capture_point_dict[globals.next_capture_point_dict_key] = new_capture_point
        globals.entity_list.append(new_capture_point)
        globals.next_capture_point_dict_key += 1

    def create_soldier(self, faction, weapon_type, aim_factor, coordinates=None):
        new_soldier = Soldier(win=self.win, map=self.map, id=globals.next_soldiers_dict_key,
                              shape="square", width=5, coordinates=coordinates, faction=faction,
                              weapon_type=weapon_type, aim_factor=aim_factor)
        globals.soldiers_dict[globals.next_soldiers_dict_key] = new_soldier
        globals.entity_list.append(new_soldier)
        globals.next_soldiers_dict_key += 1


class MapCreatorPage(Page):

    def __init__(self, win, name, clock, bg_color=None):
        super().__init__(win, name, clock, bg_color)
        # Font
        self.font = pygame.font.SysFont("Times New Roman", 30, bold=True)
        self.button_font = pygame.font.SysFont("Times New Roman", 20, bold=False)

        # Screenshots
        self.take_screenshots = False
        self.frame_counter = 0

        # Map
        self.map_name = None
        self.map = None
        self.load_map()

        # Format: ((grid_col, grid_row), (from, to))
        self.previous_actions = []

        # Other variables
        self.dt = None

    def mainloop(self):
        while True:

            # This is for if the user closes the tkinter window (the main thread) while pygame is running
            # This allows for the pygame thread to terminate using the thread.join() method before calling sys.exit()
            # for the main thread to terminate as well
            if not globals.pygame_running:
                break

            # Time since last clock tick
            globals.dt = self.clock.tick(globals.FPS)
            # Do not use dt if taking screenshots
            if self.take_screenshots:
                globals.dt = 1

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if pygame.mouse.get_pressed()[0]:
                    mouse_pos = pygame.mouse.get_pos()
                    mouse_pos = Point(mouse_pos[0], mouse_pos[1])
                    mouse_pos_grid_position = self.map.get_grid_position_of_point(mouse_pos)
                    value_at_grid_position = self.map.map_array[mouse_pos_grid_position[0]][mouse_pos_grid_position[1]]
                    if value_at_grid_position != 1:
                        new_value = 1
                        self.map.map_array[mouse_pos_grid_position[0]][mouse_pos_grid_position[1]] = new_value
                        self.previous_actions.append((mouse_pos_grid_position, (value_at_grid_position, new_value)))
                if pygame.mouse.get_pressed()[2]:
                    mouse_pos = pygame.mouse.get_pos()
                    mouse_pos = Point(mouse_pos[0], mouse_pos[1])
                    mouse_pos_grid_position = self.map.get_grid_position_of_point(mouse_pos)
                    value_at_grid_position = self.map.map_array[mouse_pos_grid_position[0]][mouse_pos_grid_position[1]]
                    if value_at_grid_position != 0:
                        new_value = 0
                        self.map.map_array[mouse_pos_grid_position[0]][mouse_pos_grid_position[1]] = new_value
                        self.previous_actions.append((mouse_pos_grid_position, (value_at_grid_position, new_value)))
                if pygame.key.get_pressed()[pygame.K_LCTRL]:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_z:
                            if len(self.previous_actions) != 0:
                                previous_action = self.previous_actions.pop()
                                previous_value = previous_action[1][0]
                                previous_action_grid_position = previous_action[0]
                                self.map.map_array[previous_action_grid_position[0]][previous_action_grid_position[1]] = previous_value

            # Tkinter Options Updates
            if globals.save_map:
                globals.save_map = False
                self.save_map()

            """DRAW STUFF BELOW"""
            # Redraw level
            self.win.fill(globals.BLACK)
            if self.map.show_gridlines:
                self.map.draw_gridlines()
            self.map.draw()

            # Update frame
            pygame.display.update()
            if self.take_screenshots:
                pygame.image.save(self.win, f"./Images/screenshot{self.frame_counter}.jpg")
                self.frame_counter += 1

    def load_map(self):
        self.map_name = globals.map_name
        if self.map_name == "Blank":
            map_array = globals.MAP_BLANK
        elif self.map_name == "Randomly Generated":
            map_array = globals.generate_random_map()
        else:
            with open(f"./Maps/{self.map_name}.txt", "rb") as f:
                map_array = _pickle.load(f)
        self.map = Map(win=self.win, map_array=map_array, wall_color=globals.BROWNISH_GREY)

    def save_map(self):
        map_name = globals.save_map_name
        with open(f"./Maps/{map_name}.txt", "wb") as f:
            _pickle.dump(self.map.map_array, f)
