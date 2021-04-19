"""Global variables shared across all scripts"""
from enum import Enum


# Pygame
pygame_running = False
# Window size
WIN_SIZE = WIN_WIDTH, WIN_HEIGHT = (1200, 600)
# Frames Per Second
FPS = 240
# Color Constants
BLACK = [0, 0, 0]
WHITE = [255, 255, 255]
GREY = [100, 100, 100]
RED = [255, 0, 0]
DARK_RED = [102, 0, 0]
ORANGE = [255, 128, 0]
GREEN = [0, 255, 0]
DARK_GREEN = [0, 100, 0]
BLUE = [0, 0, 255]
TEAL = [135, 229, 239]
PURPLE = [255, 0, 255]
PINK = [255, 0, 102]
YELLOW = [255, 255, 0]
ALMOND = [200, 180, 170]
BROWNISH_GREY = [135, 119, 119]
# Window Position Constants
TOPLEFT = (0, 0)
TOP = (WIN_WIDTH / 2, 0)
TOPRIGHT = (WIN_WIDTH, 0)
LEFT = (0, WIN_HEIGHT / 2)
CENTER = (WIN_WIDTH / 2, WIN_HEIGHT / 2)
RIGHT = (WIN_WIDTH, WIN_HEIGHT / 2)
BOTTOMLEFT = (0, WIN_HEIGHT)
BOTTOM = (WIN_WIDTH / 2, WIN_HEIGHT)
BOTTOMRIGHT = (WIN_WIDTH, WIN_HEIGHT)
OFFSCREEN = (-1000, -1000)


# Game Options

# Control
paused = False
# Delta time a.k.a how much time passed between the current frame and last frame
dt = 0

# Map
map_name = None
MAP_BLANK = [[0 for i in range(0, 80)] for i in range(0, 40)]
def generate_random_map(width=80, p_of_wall=0.2):
    map_array = [[0 for i in range(0, width)] for j in range(0, width // 2)]
    for i in range(0, len(map_array)):
        for j in range(0, len(map_array[0])):
            far_from_center_penalty = 0
            closeness_to_center_factor = (abs(i - width / 4)) + (abs(j - width / 2))
            if closeness_to_center_factor != 0:
                closeness_to_center_factor = 1 / closeness_to_center_factor
            if closeness_to_center_factor <= 0.01:
                far_from_center_penalty = 0.3
            if min(random() - max((closeness_to_center_factor), 0) + far_from_center_penalty, 1) <= p_of_wall:
                map_array[i][j] = 1
    for i in range(0, len(map_array)):
        for j in range(0, len(map_array[0])):
            if map_array[i][j] == 0:
                if i - 1 >= 0:
                    if map_array[i - 1][j] == 1:
                        if j - 1 >= 0:
                            if map_array[i][j - 1] == 1:
                                map_array[i][j] = 1
                                continue
                        elif j + 1 <= len(map_array[0]) - 1:
                            if map_array[i][j + 1] == 1:
                                map_array[i][j] = 1
                                continue
                elif i + 1 <= len(map_array) - 1:
                    if map_array[i + 1][j] == 1:
                        if j - 1 >= 0:
                            if map_array[i][j - 1] == 1:
                                map_array[i][j] = 1
                                continue
                        elif j + 1 <= len(map_array[0]) - 1:
                            if map_array[i][j + 1] == 1:
                                map_array[i][j] = 1
                                continue
    return map_array

# Map Creator
save_map = False
save_map_name = None

# Factions
class FactionColor(Enum):
    TR = RED
    NC = BLUE
    VS = PURPLE
FACTION_LIST = ["NC", "TR", "VS"]

# Weapons
WEAPON_TYPES = ["short range", "med range", "long range"]

# Entities
entity_list = []
# Soldiers
soldiers_dict = {}
next_soldiers_dict_key = 0
soldiers_being_added = False
number_of_TR_to_add = 0
number_of_NC_to_add = 0
number_of_VS_to_add = 0
# Spawns
SPAWN_TYPES = ("Sunderer",)
spawn_point_dict = {}
next_spawn_dict_key = 0
spawn_being_placed = False
spawn_being_placed_type = None
spawn_being_placed_faction = None
# Capture Points
capture_point_dict = {}
next_capture_point_dict_key = 0
capture_point_being_placed = False
capture_point_being_placed_faction = None
