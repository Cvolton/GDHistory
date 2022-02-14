from .utils import assign_key, assign_key_no_pop, get_data_path, create_level_string, robtop_unxor, create_song_record_from_data, get_song_object, decode_base64_text
from .models import ServerResponse, Level, LevelRecord, SongRecord

from .constants import XORKeys, MiscConstants

from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_naive

from datetime import datetime
from time import sleep
import requests
import json

def create_request(response_json):
	data_path = get_data_path()

	response_count = ServerResponse.objects.filter(unprocessed_post_parameters=response_json["unprocessed_post_parameters"], endpoint=response_json["endpoint"], created=response_json["created"]).count()
	if response_count > 0:
		return False

	response_object = ServerResponse(unprocessed_post_parameters=response_json["unprocessed_post_parameters"], endpoint=response_json["endpoint"], created=response_json["created"])
	response_object.save()

	f = open(f"{data_path}/ServerResponse/{response_object.pk}", "w")
	f.write(response_json["raw_output"])
	f.close()

	return response_object

def response_to_dict(response, separator):
	if response == "":
		return False

	result = {}
	i = 0
	last_key = 0
	for item in response.split(separator):
		if i % 2 == 0:
			last_key = int(item)
		else:
			result[last_key] = item
		i += 1
	return result

def create_user_dict(response):
	user_dict = {}
	for item in response.split('|'):
		user_info = item.split(':')
		user_dict[user_info[0]] = user_info
	return user_dict

def create_song_array(response):
	song_array = []
	for item in response.split('~:~'):
		response_dict = response_to_dict(item, '~|~')
		if response_dict is not False:
			song_array.append(response_dict)
	return song_array

def get_level_object(level_id):
	try:
		level_object = Level.objects.get(online_id=level_id)
	except:
		level_object = Level(online_id=level_id)
		level_object.save()
	return level_object

def create_level_record_from_data(level_data, level_object, record_type, server_response, *args, **kwargs):
	level_password = assign_key(level_data, 27)
	try:
		level_password = int(level_password)
	except:
		level_password = None if level_password is None else robtop_unxor(level_password, XORKeys.PASSWORD_KEY)

	description = assign_key(level_data, 3)
	description_encoded = False
	if not kwargs.get('legacy_description', False):
		description_result = decode_base64_text(description)
		description = description_result.text
		description_encoded = description_result.encoded

	try: #TODO: merge the 2 cases
		return LevelRecord.objects.get(level=level_object,
			level_name = assign_key_no_pop(level_data, 2),
			description = description,
			description_encoded = description_encoded,
			user_id = assign_key_no_pop(level_data, 6),
			official_song = assign_key_no_pop(level_data, 12),
			rating = assign_key_no_pop(level_data, 8),
			rating_sum = assign_key_no_pop(level_data, 9),
			downloads = assign_key_no_pop(level_data, 10),
			level_version = assign_key_no_pop(level_data, 5),
			game_version = assign_key_no_pop(level_data, 13),
			likes = assign_key_no_pop(level_data, 14),
			length = assign_key_no_pop(level_data, 15),
			dislikes = assign_key_no_pop(level_data, 16),
			demon = assign_key_no_pop(level_data, 17),
			stars = assign_key_no_pop(level_data, 18),
			feature_score = assign_key_no_pop(level_data, 19),
			auto = assign_key_no_pop(level_data, 25),
			two_player = assign_key_no_pop(level_data, 31),
			song = get_song_object(assign_key_no_pop(level_data, 35)),
			objects_count = assign_key_no_pop(level_data, 45),
			coins = assign_key_no_pop(level_data, 37),
			coins_verified = assign_key_no_pop(level_data, 38),
			requested_stars = assign_key_no_pop(level_data, 39),
			extra_string = assign_key_no_pop(level_data, 36),
			daily_id = assign_key_no_pop(level_data, 41),
			epic = assign_key_no_pop(level_data, 42),
			demon_type = assign_key_no_pop(level_data, 43),
			seconds_spent_editing = assign_key_no_pop(level_data, 46),
			seconds_spent_editing_copies = assign_key_no_pop(level_data, 47),
			relative_upload_date = assign_key_no_pop(level_data, 28),
			relative_update_date = assign_key_no_pop(level_data, 29),
			original = assign_key_no_pop(level_data, 30),
			record_type = record_type,
			#username = not included,
			password = level_password,
			#account_id = not included,
		)
	except:
		record = LevelRecord(level=level_object,
			level_name = assign_key(level_data, 2),
			description = description,
			description_encoded = description_encoded,
			#username = not included,
			user_id = assign_key(level_data, 6),
			official_song = assign_key(level_data, 12),
			rating = assign_key(level_data, 8),
			rating_sum = assign_key(level_data, 9),
			downloads = assign_key(level_data, 10),
			level_version = assign_key(level_data, 5),
			game_version = assign_key(level_data, 13),
			likes = assign_key(level_data, 14),
			length = assign_key(level_data, 15),
			dislikes = assign_key(level_data, 16),
			demon = assign_key(level_data, 17),
			stars = assign_key(level_data, 18),
			feature_score = assign_key(level_data, 19),
			auto = assign_key(level_data, 25),
			password = level_password,
			two_player = assign_key(level_data, 31),
			song = get_song_object(assign_key(level_data, 35)),
			objects_count = assign_key(level_data, 45),
			#account_id = not included,
			coins = assign_key(level_data, 37),
			coins_verified = assign_key(level_data, 38),
			requested_stars = assign_key(level_data, 39),
			extra_string = assign_key(level_data, 36),
			daily_id = assign_key(level_data, 41),
			epic = assign_key(level_data, 42),
			demon_type = assign_key(level_data, 43),
			seconds_spent_editing = assign_key(level_data, 46),
			seconds_spent_editing_copies = assign_key(level_data, 47),
			relative_upload_date = assign_key(level_data, 28),
			relative_update_date = assign_key(level_data, 29),
			original = assign_key(level_data, 30),
			record_type = record_type,
			unprocessed_data = level_data,
			server_response = server_response
		)
		record.save()
		return record

def process_download(response_json):
	online_id = response_json["unprocessed_post_parameters"]["levelID"]
	level_object = get_level_object(online_id)

	response_object = create_request(response_json)
	response = response_json["raw_output"]

	if response[:2] == '-1' or not response: #level doesn't exist or other error
		level_object.is_deleted = True
		level_object.save()
		return

	request_info = response.split('#')
	if len(request_info) < 3:
		return False

	level_info = response_to_dict(request_info[0], ':')

	record = create_level_record_from_data(level_info, level_object, LevelRecord.RecordType.DOWNLOAD, response_object)

	time_created = parse_datetime(response_json["created"])
	if is_naive(time_created):
		time_created = make_aware(time_created)

	if time_created >= MiscConstants.UNLISTED_EXPLOIT_FIX_TIME:
		level_object.set_public(True)
		record.cache_is_public = True

	#record.server.add(save_file)

	if 4 in level_info and level_info[4]:
		level_string = assign_key(level_info, 4)
		record.level_string = create_level_string(level_string)
		record.unprocessed_data = level_info
	record.save()

def process_get(response_json):
	response_object = create_request(response_json)
	response = response_json["raw_output"]
	if response_object is False or response == "-1" or response == "":
		return False

	request_info = response.split('#')
	if len(request_info) < 4:
		return False

	user_dict = create_user_dict(request_info[1])

	song_array = create_song_array(request_info[2])

	for item in request_info[0].split('|'):
		level_info = response_to_dict(item, ':')
		level_object = get_level_object(level_info[1])
		level_object.set_public(True)

		#print("among")
		#print(level_info)

		record = create_level_record_from_data(level_info, level_object, LevelRecord.RecordType.GET, response_object)
		record.cache_is_public = True

		if record.user_id in user_dict:
			user_record = user_dict[record.user_id]
			record.username = record.username if 1 not in user_record is None else user_record[1]
			record.account_id = record.account_id if 2 not in user_record is None else user_record[2]
			
		record.save()

	for item in song_array:
		record = create_song_record_from_data(item, get_song_object(item[1]), SongRecord.RecordType.LEVEL_INFO, decode_link=True)
		record.server_response.add(response_object)

	return True

def import_json(file):
	response_json = json.load(file)
	#Avoid importing invalid data from CloudFlare
	if response_json["raw_output"][:5] == '<html' or response_json["raw_output"][:5] == 'error':
		return False

	if response_json["endpoint"] == "getGJLevels21":
		print(process_get(response_json))
	if response_json["endpoint"] == "downloadGJLevel22":
		process_download(response_json)

