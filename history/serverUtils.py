from .utils import assign_key, assign_key_no_pop, get_data_path, create_level_string, robtop_unxor, create_song_record_from_data, get_song_object
from .models import ServerResponse, Level, LevelRecord

from .constants import XORKeys, GetLevelTypes

from datetime import datetime
from time import sleep
import requests

class RequestResult:
	def __init__(self, response_object, response_text):
		self.response_object = response_object
		self.response_text = response_text

def send_request(endpoint, data):
	data_path = get_data_path()

	mandatory_data = {
		"gameVersion": "21",
		"binaryVersion": "35",
		"gdw": "0",
		"secret": "Wmfd2893gb7"
	}

	data |= mandatory_data 

	headers = {'User-Agent': ''}

	response = requests.post(f"http://www.boomlings.com/database/{endpoint}.php", data=data, headers=headers)

	response_object = ServerResponse(unprocessed_post_parameters=data, endpoint=endpoint)
	response_object.save()

	f = open(f"{data_path}/ServerResponse/{response_object.pk}", "w")
	f.write(response.text)
	f.close()

	return RequestResult(response_object, response.text)

def response_to_dict(response, separator):
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
		song_array.append(response_to_dict(item, '~|~'))
	return song_array

def get_level_object(level_id):
	try:
		level_object = Level.objects.get(online_id=level_id)
	except:
		level_object = Level(online_id=level_id)
		level_object.save()
	return level_object

def create_level_record_from_data(level_data, level_object, record_type, server_response):
	level_password = assign_key(level_data, 27)
	try:
		level_password = int(level_password)
	except:
		level_password = None if level_password is None else robtop_unxor(level_password, XORKeys.PASSWORD_KEY)

	try: #TODO: merge the 2 cases
		return LevelRecord.objects.get(level=level_object,
			level_name = assign_key_no_pop(level_data, 2),
			description = assign_key_no_pop(level_data, 3),
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
			custom_song = assign_key_no_pop(level_data, 35),
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
			record_type = record_type,
			#username = not included,
			password = level_password,
			#account_id = not included,
		)
	except:
		record = LevelRecord(level=level_object,
			level_name = assign_key(level_data, 2),
			description = assign_key(level_data, 3),
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
			custom_song = assign_key(level_data, 35),
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
			record_type = record_type,
			unprocessed_data = level_data,
			server_response = server_response
		)
		record.save()
		return record

def download_level(online_id):
	if LevelRecord.objects.filter(level__online_id=online_id, server_response__created__gte=datetime.today().replace(day=1), record_type=LevelRecord.RecordType.DOWNLOAD).count() > 0:
		return

	post_parameters = {'levelID': online_id, 'extras': '1'}
	request_result = send_request('downloadGJLevel22', post_parameters)
	response = request_result.response_text
	response_object = request_result.response_object

	if response[:2] == '-1': #level doesn't exist or other error
		return

	level_info = response_to_dict(response.split('#')[0], ':')

	level_id = level_info[1] if 1 in level_info else 0
	level_object = get_level_object(online_id)

	record = create_level_record_from_data(level_info, level_object, LevelRecord.RecordType.DOWNLOAD, response_object)

	#record.server.add(save_file)

	if 4 in level_info:
		level_string = assign_key(level_info, 4)
		record.level_string = create_level_string(level_string)
		record.unprocessed_data = level_info
		record.save()

def get_level_page(page_type, page):
	post_parameters = {'type': page_type, 'page': page}
	request_result = send_request('getGJLevels21', post_parameters)
	response = request_result.response_text
	if response == "-1":
		return False

	if not response:
		print("Connection failed... waiting")
		Sleep(60)
		print("Connection failed... trying again")
		return get_level_page(page_type, page)

	response_object = request_result.response_object

	request_info = response.split('#')
	user_dict = create_user_dict(request_info[1])

	song_array = create_song_array(request_info[2])

	for item in request_info[0].split('|'):
		level_info = response_to_dict(item, ':')
		level_object = get_level_object(level_info[1])

		print(level_info)

		record = create_level_record_from_data(level_info, level_object, LevelRecord.RecordType.GET, response_object)
		if record.user_id in user_dict:
			user_record = user_dict[record.user_id]
			record.username = record.username if 1 not in user_record is None else user_record[1]
			record.account_id = record.account_id if 2 not in user_record is None else user_record[2]
			record.save()

	for item in song_array:
		create_song_record_from_data(item, get_song_object(item[1]))
		#TODO: link song records to server responses

	sleep(0.1)
	return True

def get_first_level_pages(page_type, amount):
	for i in range(0, amount):
		print(f"Page {i}")
		get_level_page(page_type, i)

def get_level_pages_from(page_type, starting_page):
	while get_level_page(page_type, starting_page):
		starting_page += 1
		print(f"Page {starting_page}")
