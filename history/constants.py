from datetime import datetime
from django.utils.timezone import make_aware

class SaveFailReasons:
	ALREADY_QUEUED = 1

class XORKeys:
	PASSWORD_KEY = 26364

class MiscConstants:
	FIRST_2_1_LEVEL = 28294638 #This constant is not entirely accurate - This level ID points to the original collab part for "Master of the World" by Viprin and Terron, which is the first rated 2.1 level.
	UNLISTED_EXPLOIT_FIX_TIME = make_aware(datetime.fromtimestamp(1637719800)) #2021-11-24 02:10:00+00:00
	ELEMENT_111_RG = 498620

class SongNames:
	PRACTICE = [
		"Stay Inside Me by OcularNebula"
	]
	MAIN = [
		"Stereo Madness by ForeverBound", "Back on Track by DJVI", "Polargeist by Step", "Dry Out by DJVI", "Base after Base by DJVI",
		"Can't Let Go by DJVI", "Jumper by Waterflame", "Time Machine by Waterflame", "Cycles by DJVI", "xStep by DJVI",
		"Clutterfunk by Waterflame", "Theory of Everything by DJ Nate", "Electroman Adventures by Waterflame", "Clubstep by DJ Nate", "Electrodynamix by DJ Nate",
		"Hexagon Force by Waterflame", "Blast Processing by Waterflame", "Theory of Everything 2 by DJ Nate", "Geometrical Dominator by Waterflame", "Deadlocked by F-777",
		"Fingerdash by MDK"
	]
	MELTDOWN = [
		"The Seven Seas by F-777", "Viking Arena by F-777", "Airborne Robots by F-777"
	]
	CHALLENGE = [
		"Secret (The Challenge)"
	]
	WORLD = [
		"Payload by Dex Arson",
		"Beast Mode by Dex Arson",
		"Machina by Dex Arson",
		"Years by Dex Arson",
		"Frontlines by Dex Arson",
		"Space Pirates by Waterflame",
		"Striker by Waterflame",
		"Embers by Dex Arson",
		"Round 1 by Dex Arson",
		"Monster Dance Off by F-777"
	]
	SUBZERO = [
		"Press Start by MDK",
		"Nock Em by Bossfight",
		"Power Trip by Boom Kitty"
	]

class GetLevelTypes:
	SEARCH = 0
	DOWNLOADED = 1
	LIKED = 2
	TRENDING = 3
	RECENT = 4
	USER_ID = 5
	FEATURED = 6
	MAGIC = 7
	SENT = 8
	UNKNOWN_1 = 9
	MAP_PACK = 10
	AWARDED = 11
	FOLLOWED = 12
	FRIENDS = 13
	UNKNOWN_2 = 14
	LIKED_GDW = 15
	HALL_OF_FAME = 16
	FEATURED_GDW = 17
	SIMILAR = 18
	LEVEL_LIST = 19