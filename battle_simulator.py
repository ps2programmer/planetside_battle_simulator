import pygame
import tkinter
import globals
from page import *
from entity import *
from map import *
import os
import sys
import threading


class TkinterProgram(tkinter.Tk):

    def __init__(self, *args, **kwargs):
        tkinter.Tk.__init__(self, *args, *kwargs)
        self.title = "Battle Simulator v1.0"
        tkinter.Tk.wm_title(self, self.title)
        # Set window size
        self.geometry("600x400")
        # Protocol for when user wants to close the window
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Main container to which all other container frames will be children
        self.container = tkinter.Frame(self)
        self.container.pack()
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Pygame related
        self.win = None # Initialize pygame window variable
        self.clock = None # Initialize pygame clock variable
        self.current_pygame_page = None # Initialize variable that holds currently running pygame page
        self.pygame_thread = None

        self.frames = {}
        self.current_frame = None
        # When a new Frame subclass is created, it needs to be added to this list
        for F in [StartFrame, LevelSelectorFrame, OptionsFrame, MapCreatorOptionsFrame]:
            frame = F(self.container, self)
            self.frames[F] = frame
            # nsew = north south east west
            frame.grid(row=0, column=0, sticky="nsew")
            # Weight = 1 tells row/column to expand to fill empty space allowing widgets to be centered
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)
        self.current_frame = StartFrame
        self.show_frame(StartFrame)

    def on_window_close(self):
        self.end_pygame_thread()
        self.destroy()
        sys.exit()

    def end_pygame_thread(self):
        globals.pygame_running = False
        pygame.quit()
        if self.pygame_thread is not None:
            self.pygame_thread.join()
            self.pygame_thread = None

    def show_frame(self, frame):
        self.current_frame = frame
        frame = self.frames[frame]
        frame.tkraise()

    def start_pygame(self):
        self.pygame_thread = threading.Thread(target=self.create_and_run_pygame_thread)
        self.pygame_thread.daemon = True
        self.pygame_thread.start()

    def create_and_run_pygame_thread(self):
        pygame.init()
        self.win = pygame.display.set_mode(globals.WIN_SIZE)
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
        pygame_instance = self.current_pygame_page(win=self.win, name="pygame instance", clock=self.clock)
        pygame_instance.mainloop()


class StartFrame(tkinter.Frame):

    def __init__(self, parent, controller):
        """Parent is parent Frame (i.e. self.container in TkinterProgram), controller is TkinterProgram itself"""
        tkinter.Frame.__init__(self, parent)
        self.controller = controller

        # Add widgets below
        # Dropdown to select Pygame page
        self.pygame_page_dropdown_label = tkinter.Label(master=self, text="Select the Program: ")
        self.pygame_page_dropdown_label.grid(row=0, column=0)
        self.pygame_page_dropdown_options = ["Simulation", "Map Creator"]
        self.pygame_page_dropdown_string_holder = tkinter.StringVar()
        self.pygame_page_dropdown_string_holder.set("Simulation")
        self.pygame_page_dropdown = tkinter.OptionMenu(self, self.pygame_page_dropdown_string_holder,
                                                       *self.pygame_page_dropdown_options)
        self.pygame_page_dropdown.grid(row=0, column=1)

        # Button to go to options screen
        self.next_button = tkinter.Button(master=self, text="Next",
                                                command=self.go_to_level_selector_frame)
        self.next_button.grid(row=1, column=0, columnspan=2)

    def go_to_level_selector_frame(self):
        self.get_selected_pygame_page()
        self.controller.show_frame(LevelSelectorFrame)

    def get_selected_pygame_page(self):
        selected_page_string = self.pygame_page_dropdown_string_holder.get()
        if selected_page_string == "Simulation":
            self.controller.current_pygame_page = SimulationPage
        elif selected_page_string == "Map Creator":
            self.controller.current_pygame_page = MapCreatorPage


class LevelSelectorFrame(tkinter.Frame):

    def __init__(self, parent, controller):
        tkinter.Frame.__init__(self, parent)
        self.controller = controller

        # Add widgets below
        # Dropdown to select map
        self.map_dropdown_label = tkinter.Label(master=self, text="Load Map: ")
        self.map_dropdown_label.grid(row=0, column=0)
        self.map_dropdown_options = ["Blank", "Randomly Generated"]
        # Only txt files recognized as saved maps in Maps directory
        for file in os.listdir("./Maps/"):
            if file[-4:] == ".txt":
                self.map_dropdown_options.append(file[:-4])
        self.map_dropdown_string_holder = tkinter.StringVar()
        self.map_dropdown_string_holder.set("Blank")
        self.map_dropdown = tkinter.OptionMenu(self, self.map_dropdown_string_holder, *self.map_dropdown_options)
        self.map_dropdown.grid(row=0, column=1)

        # Start game button
        self.start_game_button = tkinter.Button(master=self, text="Start Game", command=self.start_game)
        self.start_game_button.grid(row=1, column=0, columnspan=2)

        # Back button
        self.back_button = tkinter.Button(master=self, text="Back", command=self.go_back_to_start_frame)
        self.back_button.grid(row=2, column=0, columnspan=2)

    def go_back_to_start_frame(self):
        self.controller.end_pygame_thread()
        self.controller.show_frame(StartFrame)

    def start_game(self):
        globals.pygame_running = True
        globals.map_name = self.map_dropdown_string_holder.get()
        if self.controller.current_pygame_page != MapCreatorPage:
            self.controller.show_frame(OptionsFrame)
        else:
            self.controller.show_frame(MapCreatorOptionsFrame)
        self.controller.start_pygame()


class OptionsFrame(tkinter.Frame):

    def __init__(self, parent, controller):
        tkinter.Frame.__init__(self, parent)
        self.controller = controller

        # Add widgets below
        # Place spawn
        self.place_spawn_section_label = tkinter.Label(master=self, text="Spawn Placement")
        self.place_spawn_type_label = tkinter.Label(master=self, text="Type:")
        self.place_spawn_faction_label = tkinter.Label(master=self, text="Faction:")
        self.place_spawn_type_dropdown_string_holder = tkinter.StringVar()
        self.place_spawn_type_dropdown_string_holder.set("Sunderer")
        self.place_spawn_type_dropdown_string_holder.trace("w", self.set_spawn_placement_global_variables)
        self.place_spawn_type_dropdown = tkinter.OptionMenu(self, self.place_spawn_type_dropdown_string_holder,
                                                            *globals.SPAWN_TYPES)
        self.place_spawn_faction_dropdown_string_holder = tkinter.StringVar()
        self.place_spawn_faction_dropdown_string_holder.set("NC")
        self.place_spawn_faction_dropdown_string_holder.trace("w", self.set_spawn_placement_global_variables)
        self.place_spawn_faction_dropdown = tkinter.OptionMenu(self, self.place_spawn_faction_dropdown_string_holder,
                                                               *globals.FACTION_LIST)
        self.place_spawn_button = tkinter.Button(master=self, text="Place Spawn Point", command=self.place_spawn)
        self.place_spawn_section_label.grid(row=0, column=0, columnspan=2)
        self.place_spawn_type_label.grid(row=1, column=0)
        self.place_spawn_type_dropdown.grid(row=1, column=1)
        self.place_spawn_faction_label.grid(row=2, column=0)
        self.place_spawn_faction_dropdown.grid(row=2, column=1)
        self.place_spawn_button.grid(row=3, column=0, columnspan=2)

        # Place capture point
        self.place_capture_point_section_label = tkinter.Label(master=self, text="Capture Point Placement")
        self.place_capture_point_faction_label = tkinter.Label(master=self, text="Faction:")
        self.place_capture_point_faction_dropdown_string_holder = tkinter.StringVar()
        self.place_capture_point_faction_dropdown_string_holder.set("Neutral")
        self.place_capture_point_faction_dropdown_string_holder.trace("w", self.set_capture_point_placement_global_variables)
        self.place_capture_point_faction_dropdown = tkinter.OptionMenu(self, self.place_capture_point_faction_dropdown_string_holder,
                                                                       *["Neutral"] + globals.FACTION_LIST)
        self.place_capture_point_button = tkinter.Button(master=self, text="Place Capture Point", command=self.place_capture_point)
        self.place_capture_point_section_label.grid(row=4, column=0, columnspan=2)
        self.place_capture_point_faction_label.grid(row=5, column=0)
        self.place_capture_point_faction_dropdown.grid(row=5, column=1)
        self.place_capture_point_button.grid(row=6, column=0, columnspan=2)

        # Add Soldiers
        self.add_soldiers_section_label = tkinter.Label(master=self, text="Add Soldiers")
        self.add_soldiers_number_of_NC_label = tkinter.Label(master=self, text="Number of NC to Add: ")
        self.add_soldiers_number_of_NC_entry_int_holder = tkinter.IntVar()
        self.add_soldiers_number_of_NC_entry_int_holder.set(0)
        self.add_soldiers_number_of_NC_entry = tkinter.Entry(master=self, text=self.add_soldiers_number_of_NC_entry_int_holder)
        self.add_soldiers_number_of_TR_label = tkinter.Label(master=self, text="Number of TR to Add: ")
        self.add_soldiers_number_of_TR_entry_int_holder = tkinter.IntVar()
        self.add_soldiers_number_of_TR_entry_int_holder.set(0)
        self.add_soldiers_number_of_TR_entry = tkinter.Entry(master=self, text=self.add_soldiers_number_of_TR_entry_int_holder)
        self.add_soldiers_number_of_VS_label = tkinter.Label(master=self, text="Number of VS to Add: ")
        self.add_soldiers_number_of_VS_entry_int_holder = tkinter.IntVar()
        self.add_soldiers_number_of_VS_entry_int_holder.set(0)
        self.add_soldiers_number_of_VS_entry = tkinter.Entry(master=self, text=self.add_soldiers_number_of_VS_entry_int_holder)
        self.add_soldiers_button = tkinter.Button(master=self, text="Add Soldiers", command=self.add_soldiers)
        self.add_soldiers_section_label.grid(row=7, column=0, columnspan=2)
        self.add_soldiers_number_of_NC_label.grid(row=8, column=0)
        self.add_soldiers_number_of_NC_entry.grid(row=8, column=1)
        self.add_soldiers_number_of_TR_label.grid(row=9, column=0)
        self.add_soldiers_number_of_TR_entry.grid(row=9, column=1)
        self.add_soldiers_number_of_VS_label.grid(row=10, column=0)
        self.add_soldiers_number_of_VS_entry.grid(row=10, column=1)
        self.add_soldiers_button.grid(row=11, column=0, columnspan=2)

        # Cancel Placement Button
        self.cancel_placement_button = tkinter.Button(master=self, text="Cancel Placement", command=self.cancel_all_placements)
        self.cancel_placement_button.grid(row=18, column=0, columnspan=2)

        # Quit Button
        self.quit_button = tkinter.Button(master=self, text="Quit", command=self.quit_pygame)
        self.quit_button.grid(row=19, column=0, columnspan=2)

        # Info Label
        self.info_label = tkinter.Label(master=self, text="", wraplength=300)
        self.info_label.grid(row=20, column=0, columnspan=2)

    def quit_pygame(self):
        self.controller.end_pygame_thread()
        self.controller.show_frame(StartFrame)

    def cancel_all_placements(self):
        self.place_spawn_cancel()
        self.place_capture_point_cancel()

    def set_spawn_placement_global_variables(self, *args):
        globals.spawn_being_placed_type = self.place_spawn_type_dropdown_string_holder.get()
        globals.spawn_being_placed_faction = self.place_spawn_faction_dropdown_string_holder.get()

    def place_spawn(self):
        self.cancel_all_placements()
        self.info_label["text"] = "Spawn is being placed, left click to place the spawn. Click Cancel Placement when you are finished."
        globals.spawn_being_placed = True
        self.set_spawn_placement_global_variables()

    def place_spawn_cancel(self):
        self.info_label["text"] = ""
        globals.spawn_being_placed = False
        globals.spawn_being_placed_type = None
        globals.spawn_being_placed_faction = None

    def set_capture_point_placement_global_variables(self, *args):
        globals.capture_point_being_placed_faction = self.place_capture_point_faction_dropdown_string_holder.get()

    def place_capture_point(self):
        self.cancel_all_placements()
        self.info_label["text"] = "Capture Point is being placed, left click to place the capture point. Click Cancel Placement when you are finished."
        globals.capture_point_being_placed = True
        self.set_capture_point_placement_global_variables()

    def place_capture_point_cancel(self):
        self.info_label["text"] = ""
        globals.capture_point_being_placed = False
        globals.capture_point_being_placed_faction = None

    def validate_add_soldier_entry_widget(self, action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name):
        """All those parameters required by Tkinter although they are not used here"""
        if value_if_allowed:
            try:
                int(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return False

    def add_soldiers(self):
        globals.soldiers_being_added = True
        globals.number_of_NC_to_add = self.add_soldiers_number_of_NC_entry_int_holder.get()
        globals.number_of_TR_to_add = self.add_soldiers_number_of_TR_entry_int_holder.get()
        globals.number_of_VS_to_add = self.add_soldiers_number_of_VS_entry_int_holder.get()


class MapCreatorOptionsFrame(tkinter.Frame):

    def __init__(self, parent, controller):
        tkinter.Frame.__init__(self, parent)
        self.controller = controller

        # Add widgets below
        # Save Map
        self.save_map_label = tkinter.Label(master=self, text="Map Name: ")
        self.info_label = tkinter.Label(master=self, text="", wraplength=300)
        self.save_map_entry_string_holder = tkinter.StringVar()
        self.save_map_entry_string_holder.set("")
        self.save_map_entry = tkinter.Entry(master=self, text=self.save_map_entry_string_holder)
        self.save_map_button = tkinter.Button(master=self, text="Save Map", command=self.save_map)
        self.quit_button = tkinter.Button(master=self, text="Quit", command=self.quit_pygame)
        self.save_map_label.grid(row=0, column=0)
        self.save_map_entry.grid(row=0, column=1)
        self.save_map_button.grid(row=1, column=0, columnspan=2)
        self.quit_button.grid(row=9, column=0, columnspan=2)
        self.info_label.grid(row=10, column=0, columnspan=2)

    def quit_pygame(self):
        self.controller.end_pygame_thread()
        self.controller.show_frame(StartFrame)

    def save_map(self):
        self.info_label["text"] = "Map saved. You will need to restart for it to show up in the list."
        globals.save_map = True
        globals.save_map_name = self.save_map_entry_string_holder.get()


app = TkinterProgram()
app.mainloop()

