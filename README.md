# Planetside Battle Simulator

A very basic program that aims to simulate planetside battle flow at the base-level. The main goal of this is learning and fun, however, if useful or interesting insights into how battle flow progresses can be learned then that's a bonus. 

Currently, it's built using Python's Pygame library. This was chosen because I'm already familiar with Pygame and I don't know how much time I'd commit to this project so it's meant to serve as a prototype of a potential simulation in a better engine like Unity (which I'm still in the process of learning). 

# How To Run

1. Download the repository (go to the green "Code" button and then click "Download ZIP")
2. Download the latest version of Python if you don't have it already (make sure to have "Add to PATH" checked during the installation)
3. Install Pygame using the command "pip install pygame" in your terminal/command line (CMD on Windows) (https://www.pygame.org/wiki/GettingStarted)
4. Run battle_simulator.py by going to your terminal/command line again, changing directory into where battle_simulator.py is ("cd" command on Windows) and then running "python battle_simulator.py" without the quotes. If it says something like "python is not a recognized command" then it means the PATH variable was not set properly. The PATH variable is a list of paths which are first searched when a command is run. In this case, if the path to python.exe is not in the list of paths under the PATH variable, then your computer won't recognize python as a command because it doesn't know where python.exe is located. Besides adding the path to python.exe inside your PATH variable (which is quick and Googling it would give a better answer than I can), the alternative is to change directory in your command line to where python.exe is located and then running "python <full path to where you saved battle_simulator.py>". 
5. Note that there's 2 windows, the pygame window and the tkinter window (tkinter is a library in Python that lets you make basic GUIs). The tkinter window will be hidden behind the pygame window when the pygame window starts up. Just a heads up as the tkinter window contains the controls to create spawn points, capture points, and soldiers, otherwise if you weren't aware it was hidden it might be anti-climactic when a blank map with nothing on it opens up. When adding soldiers, they will not appear unless there is a spawn point available for them and you might have to wait for the respawn timer before seeing them spawn in.
