from .models import SaveFile, Level, LevelRecord, HistoryUser, Song, SongRecord, LevelString, LevelRecordType
from .utils import assign_key, get_data_path, assign_key_no_pop, create_level_string, create_song_record_from_data, get_song_object, decode_base64_text, encode_base64_text

from celery import shared_task

import plistlib
import os
import base64
import gzip
from datetime import datetime

def get_game_manager_bytes(game_manager_file):
	#game_manager_file = open(os.path.expanduser('~/testdata/gdhistory/CCGameManager_21.dat'), "rb")
	game_manager_bytes = game_manager_file.read()
	game_manager_file.close()
	return bytearray(game_manager_bytes)

def xor_game_manager_if_needed(game_manager_bytes):
	if game_manager_bytes[:5] == b'C?xBJ':
		i = 0
		for byte in game_manager_bytes:
			game_manager_bytes[i] = byte ^ 11
			i+=1
	return game_manager_bytes

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

def plist_to_robtop_plist(game_manager_bytes):
	game_manager_bytes = game_manager_bytes.replace(b'</dict>',b'</d>')
	game_manager_bytes = game_manager_bytes.replace(b'</key>',b'</k>')
	game_manager_bytes = game_manager_bytes.replace(b'<dict>',b'<d>')
	game_manager_bytes = game_manager_bytes.replace(b'<dict />',b'<d />')
	game_manager_bytes = game_manager_bytes.replace(b'<key>',b'<k>')
	game_manager_bytes = game_manager_bytes.replace(b'<string>',b'<s>')
	game_manager_bytes = game_manager_bytes.replace(b'</string>',b'</s>')
	game_manager_bytes = game_manager_bytes.replace(b'<integer>',b'<i>')
	game_manager_bytes = game_manager_bytes.replace(b'</integer>',b'</i>')
	game_manager_bytes = game_manager_bytes.replace(b'<true />',b'<t />')
	game_manager_bytes = game_manager_bytes.replace(b'<real>',b'<r>')
	game_manager_bytes = game_manager_bytes.replace(b'</real>',b'</r>')
	return game_manager_bytes

def remove_invalid_characters(game_manager_bytes):
	game_manager_bytes = game_manager_bytes.replace(b'&',b'@@amp@@')
	game_manager_bytes = game_manager_bytes.replace(b'#',b'@@hash@@')
	return game_manager_bytes

def load_game_manager_plist(file):
	gmb = get_game_manager_bytes(file)
	gmb = xor_game_manager_if_needed(gmb)
	gmb = ungzip_if_needed(gmb)
	gmb = robtop_plist_to_plist(gmb)
	gmb = remove_invalid_characters(gmb)
	return plistlib.loads(gmb)

def create_level_record_from_data(data, level_object, record_type, binary_version):
	description = assign_key_no_pop(data, 'k3')
	description_encoded = False
	if binary_version is not None and binary_version >= 27:
		description_result = decode_base64_text(description)
		description = description_result.text
		description_encoded = description_result.encoded

	try:
		return LevelRecord.objects.get(level=level_object,
			level_name = assign_key_no_pop(data, 'k2'),
			description = description,
			description_encoded = description_encoded,
			username = assign_key_no_pop(data, 'k5'),
			user_id = assign_key_no_pop(data, 'k6'),
			official_song = assign_key_no_pop(data, 'k8'),
			rating = assign_key_no_pop(data, 'k9'),
			rating_sum = assign_key_no_pop(data, 'k10'),
			downloads = assign_key_no_pop(data, 'k11'),
			level_version = assign_key_no_pop(data, 'k16'),
			game_version = assign_key_no_pop(data, 'k17'),
			likes = assign_key_no_pop(data, 'k22'),
			length = assign_key_no_pop(data, 'k23'),
			dislikes = assign_key_no_pop(data, 'k24'),
			demon = assign_key_no_pop(data, 'k25'),
			stars = assign_key_no_pop(data, 'k26'),
			feature_score = assign_key_no_pop(data, 'k27'),
			auto = assign_key_no_pop(data, 'k33'),
			password = assign_key_no_pop(data, 'k41'),
			two_player = assign_key_no_pop(data, 'k43'),
			song = get_song_object(assign_key_no_pop(data, 'k45')),
			objects_count = assign_key_no_pop(data, 'k48'),
			account_id = assign_key_no_pop(data, 'k60'),
			coins = assign_key_no_pop(data, 'k64'),
			coins_verified = assign_key_no_pop(data, 'k65'),
			requested_stars = assign_key_no_pop(data, 'k66'),
			extra_string = assign_key_no_pop(data, 'k67'),
			daily_id = assign_key_no_pop(data, 'k74'),
			epic = assign_key_no_pop(data, 'k75'),
			demon_type = assign_key_no_pop(data, 'k76'),
			seconds_spent_editing = assign_key_no_pop(data, 'k80'),
			seconds_spent_editing_copies = assign_key_no_pop(data, 'k81'),
			original = assign_key_no_pop(data, 'k42'),
			record_type = record_type
		)
	except:
		assign_key(data, 'k3')
		record = LevelRecord(level=level_object,
			level_name = assign_key(data, 'k2'),
			description = description,
			description_encoded = description_encoded,
			username = assign_key(data, 'k5'),
			user_id = assign_key(data, 'k6'),
			official_song = assign_key(data, 'k8'),
			rating = assign_key(data, 'k9'),
			rating_sum = assign_key(data, 'k10'),
			downloads = assign_key(data, 'k11'),
			level_version = assign_key(data, 'k16'),
			game_version = assign_key(data, 'k17'),
			likes = assign_key(data, 'k22'),
			length = assign_key(data, 'k23'),
			dislikes = assign_key(data, 'k24'),
			demon = assign_key(data, 'k25'),
			stars = assign_key(data, 'k26'),
			feature_score = assign_key(data, 'k27'),
			auto = assign_key(data, 'k33'),
			password = assign_key(data, 'k41'),
			two_player = assign_key(data, 'k43'),
			song = get_song_object(assign_key(data, 'k45')),
			objects_count = assign_key(data, 'k48'),
			account_id = assign_key(data, 'k60'),
			coins = assign_key(data, 'k64'),
			coins_verified = assign_key(data, 'k65'),
			requested_stars = assign_key(data, 'k66'),
			extra_string = assign_key(data, 'k67'),
			daily_id = assign_key(data, 'k74'),
			epic = assign_key(data, 'k75'),
			demon_type = assign_key(data, 'k76'),
			seconds_spent_editing = assign_key(data, 'k80'),
			seconds_spent_editing_copies = assign_key(data, 'k81'),
			original = assign_key(data, 'k42'),
			record_type = record_type,
			unprocessed_data = data
		)
		record.save()
		return record

def create_data_from_level_record(record):
	data = {
		'kCEK': 4,
		'k1': record.level.online_id,
		'k2': record.level_name,
		'k3': record.get_encoded_description(),
		'k4': record.level_string.load_file_content() if record.level_string is not None else None,
		'k5': record.username,
		'k6': record.user_id,
		'k8': record.official_song,
		'k9': record.rating,
		'k10': record.rating_sum,
		'k11': record.downloads,
		'k16': record.level_version,
		'k17': record.game_version,
		'k22': record.likes,
		'k23': record.length,
		'k24': record.dislikes,
		'k25': record.demon,
		'k26': record.stars,
		'k27': record.feature_score,
		'k33': record.auto,
		'k41': record.password,
		'k42': record.original,
		'k43': record.two_player,
		'k45': record.song.online_id if record.song else None,
		'k48': record.objects_count,
		'k60': record.account_id,
		'k64': record.coins,
		'k65': record.coins_verified,
		'k66': record.requested_stars,
		'k67': record.extra_string,
		'k74': record.daily_id,
		'k75': record.epic,
		'k76': record.demon_type,
		'k80': record.seconds_spent_editing,
		'k81': record.seconds_spent_editing_copies
	}

	data2 = {}

	for key in data:
		if data[key] is not None and data[key] is not False:
			data2[key] = data[key]

	return data2

def process_levels_in_glm(glm, record_type, save_file):
	#records = []
	for level, data in glm.items():
		level_id = data['k1'] if 'k1' in data else 0
		try:
			level_object = Level.objects.get(online_id=level_id)
		except:
			level_object = Level(online_id=level_id)
			level_object.save()

		record = create_level_record_from_data(data, level_object, record_type, save_file.binary_version)

		record.save_file.add(save_file)

		if 'k4' in data:
			level_string = assign_key(data, 'k4')
			record.level_string = create_level_string(level_string)
			record.unprocessed_data = data
			record.save()

		level_object.revalidate_cache()

	#LevelRecord.objects.bulk_create(records, ignore_conflicts=True, batch_size=1000)

def process_songs_in_mdlm(mdlm, save_file):
	for song, data in mdlm.items():
		song_object = get_song_object(song)
		record = create_song_record_from_data(data, song_object, SongRecord.RecordType.MDLM_001)
		record.save_file.add(save_file)
		song_object.revalidate_cache()

def upload_save_file(file, date, user, *args, **kwargs):
	data_path = get_data_path()

	game_manager = load_game_manager_plist(file)

	#stripping sensitive data
	game_manager['GJA_002'] = '' #password
	game_manager['GJA_004'] = '' #sessionID (2.2)

	save_file = SaveFile(
		author=HistoryUser.objects.get(user=user),
		player_name=assign_key_no_pop(game_manager, 'playerName'),
		player_user_id=assign_key_no_pop(game_manager, 'playerUserID'),
		player_account_id=assign_key_no_pop(game_manager, 'GJA_003'),
		binary_version=assign_key_no_pop(game_manager, 'binaryVersion'),
		created=date
	)
	save_file.save()

	f = open(f"{data_path}/SaveFile/{save_file.pk}", "wb")
	plistlib.dump(game_manager, f)
	f.close()

	if not kwargs.get('skip_processing', False):
		process_save_file.delay(save_file.pk)

@shared_task
def process_save_file(save_id):
	print(f"Processing save file {save_id}")

	data_path = get_data_path()
	save_file = SaveFile.objects.get(pk=save_id)

	with open(f"{data_path}/SaveFile/{save_id}", "rb") as game_manager_file:
		game_manager = plistlib.load(game_manager_file)

	if 'GLM_03' in game_manager:
		process_levels_in_glm(game_manager['GLM_03'], LevelRecordType.GLM_03, save_file)
	if 'GLM_10' in game_manager:
		process_levels_in_glm(game_manager['GLM_10'], LevelRecordType.GLM_10, save_file)
	if 'GLM_16' in game_manager:
		process_levels_in_glm(game_manager['GLM_16'], LevelRecordType.GLM_16, save_file)
	if 'MDLM_001' in game_manager:
		process_songs_in_mdlm(game_manager['MDLM_001'], save_file)

	save_file.is_processed = True
	save_file.save()
	print(f"Finished processing save file {save_id}")

def consolidate_plist(plist_content):
	test = plist_content.split(b'\n')[3:-2]
	#test = test[:-2]
	print(test)
	return b"".join(test)