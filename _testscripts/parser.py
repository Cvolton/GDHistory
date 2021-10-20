import plistlib
import os

game_manager_file = open(os.path.expanduser('~/testdata/gdhistory/CCGameManager.dat'), "rb")
game_manager = plistlib.load(game_manager_file)
glm_03 = game_manager['GLM_03']

for level, data in glm_03.items():
	print(level)
	#print(data)