# Planetside Battle Simulator

A very basic program that aims to simulate planetside battle flow at the base-level. The main goal of this is learning and fun, however, if useful or interesting insights into how battle flow progresses can be learned then that's a bonus. 

Currently, it's built using Python's Pygame library. This was chosen because I'm already familiar with Pygame and I don't know how much time I'd commit to this project so it's meant to serve as a prototype of a potential simulation in a better engine like Unity (which I'm still in the process of learning). 

# How To Run

1. Download the repository (go to the green "Code" button and then click "Download ZIP")
2. Download the latest version of Python if you don't have it already
3. Install Pygame using the command "pip install pygame" in your terminal
4. Run battle_simulator.py
5. Note that there's 2 windows, the pygame window and the tkinter window (tkinter is a library in Python that lets you make basic GUIs). The tkinter window will be hidden behind the pygame window when the pygame window starts up. Just a heads up as the tkinter window contains the controls to create spawn points, capture points, and soldiers, otherwise if you weren't aware it was hidden it might be anti-climactic when a blank map with nothing on it opens up
