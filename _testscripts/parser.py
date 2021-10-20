import plistlib
import os
import base64
import gzip

def get_game_manager_bytes():
	game_manager_file = open(os.path.expanduser('~/testdata/gdhistory/CCGameManager_21.dat'), "rb")
	game_manager_bytes = game_manager_file.read()
	game_manager_file.close()
	return game_manager_bytes

def xor_game_manager_if_needed(game_manager_bytes):
	game_manager_bytes = bytearray(get_game_manager_bytes())
	if game_manager_bytes[:5] == b'C?xBJ':
		i = 0
		for byte in game_manager_bytes:
			game_manager_bytes[i] = byte ^ 11
			i+=1
		#return bytes(a ^ b for a, b in zip(var, key))
	return bytes(game_manager_bytes)

def ungzip_if_needed(game_manager_bytes):
	if game_manager_bytes[:5] == b'H4sIA':
		game_manager_bytes = base64.b64decode(game_manager_bytes, altchars='-_')
		game_manager_bytes = gzip.decompress(game_manager_bytes)

	return game_manager_bytes

def robtop_plist_to_plist(game_manager_bytes):
	game_manager_bytes = game_manager_bytes.replace(b'</d>',b'</dict>')
	game_manager_bytes = game_manager_bytes.replace(b'</k>',b'</key>')
	game_manager_bytes = game_manager_bytes.replace(b'<d>',b'<dict>')
	game_manager_bytes = game_manager_bytes.replace(b'<d />',b'<dict />')
	game_manager_bytes = game_manager_bytes.replace(b'<k>',b'<key>')
	game_manager_bytes = game_manager_bytes.replace(b'<s>',b'<string>')
	game_manager_bytes = game_manager_bytes.replace(b'</s>',b'</string>')
	game_manager_bytes = game_manager_bytes.replace(b'<i>',b'<integer>')
	game_manager_bytes = game_manager_bytes.replace(b'</i>',b'</integer>')
	game_manager_bytes = game_manager_bytes.replace(b'<t />',b'<true />')
	game_manager_bytes = game_manager_bytes.replace(b'<r>',b'<real>')
	game_manager_bytes = game_manager_bytes.replace(b'</r>',b'</real>')
	return game_manager_bytes

def remove_invalid_characters(game_manager_bytes):
	game_manager_bytes = game_manager_bytes.replace(b'&',b'@@amp@@')
	game_manager_bytes = game_manager_bytes.replace(b'#',b'@@hash@@')
	return game_manager_bytes


gmb = remove_invalid_characters(robtop_plist_to_plist(ungzip_if_needed(xor_game_manager_if_needed(get_game_manager_bytes()))))

f = open(os.path.expanduser('~/testdata/gdhistory/CCGameManager_decodetest.dat'), "wb")
f.write(gmb)
f.close()

game_manager = plistlib.loads(gmb)
glm_03 = game_manager['GLM_03']

for level, data in glm_03.items():
	print(level)
	#print(data)