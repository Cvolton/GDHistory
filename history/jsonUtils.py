from .models import ManualSubmission, Level, LevelRecord, HistoryUser, Song, SongRecord, LevelString, LevelRecordType
from .utils import assign_key, get_data_path, assign_key_no_pop, create_level_string, create_song_record_from_data, get_song_object, decode_base64_text, encode_base64_text, get_level_object

from celery import shared_task

import json
import os
import base64
import gzip
from datetime import datetime

def create_level_record_from_data(data, level_object, record_type, submission):
	description = assign_key(data, 'description')
	description_encoded = assign_key(data, 'description_encoded')
	if description_encoded:
		description_result = decode_base64_text(description)
		description = description_result.text
		description_encoded = description_result.encoded

	try:
		return LevelRecord.objects.get(level=level_object,
			level_name = assign_key_no_pop(data, 'level_name'),
			description = description,
			description_encoded = description_encoded,
			username = assign_key_no_pop(data, 'username'),
			user_id = assign_key_no_pop(data, 'user_id'),
			official_song = assign_key_no_pop(data, 'official_song'),
			rating = assign_key_no_pop(data, 'rating'),
			rating_sum = assign_key_no_pop(data, 'rating_sum'),
			downloads = assign_key_no_pop(data, 'downloads'),
			level_version = assign_key_no_pop(data, 'level_version'),
			game_version = assign_key_no_pop(data, 'game_version'),
			likes = assign_key_no_pop(data, 'likes'),
			length = assign_key_no_pop(data, 'length'),
			dislikes = assign_key_no_pop(data, 'dislikes'),
			demon = assign_key_no_pop(data, 'demon'),
			stars = assign_key_no_pop(data, 'stars'),
			feature_score = assign_key_no_pop(data, 'feature_score'),
			auto = assign_key_no_pop(data, 'auto'),
			password = assign_key_no_pop(data, 'password'),
			two_player = assign_key_no_pop(data, 'two_player'),
			song = assign_key_no_pop(data, 'song'),
			objects_count = assign_key_no_pop(data, 'objects_count'),
			account_id = assign_key_no_pop(data, 'account_id'),
			coins = assign_key_no_pop(data, 'coins'),
			coins_verified = assign_key_no_pop(data, 'coins_verified'),
			requested_stars = assign_key_no_pop(data, 'requested_stars'),
			extra_string = assign_key_no_pop(data, 'extra_string'),
			daily_id = assign_key_no_pop(data, 'daily_id'),
			epic = assign_key_no_pop(data, 'epic'),
			demon_type = assign_key_no_pop(data, 'demon_type'),
			seconds_spent_editing = assign_key_no_pop(data, 'seconds_spent_editing'),
			seconds_spent_editing_copies = assign_key_no_pop(data, 'seconds_spent_editing_copies'),
			original = assign_key_no_pop(data, 'original'),
			manual_submission = submission,
			record_type = record_type
		)
	except:
		record = LevelRecord(level=level_object,
			level_name = assign_key(data, 'level_name'),
			description = description,
			description_encoded = description_encoded,
			username = assign_key(data, 'username'),
			user_id = assign_key(data, 'user_id'),
			official_song = assign_key(data, 'official_song'),
			rating = assign_key(data, 'rating'),
			rating_sum = assign_key(data, 'rating_sum'),
			downloads = assign_key(data, 'downloads'),
			level_version = assign_key(data, 'level_version'),
			game_version = assign_key(data, 'game_version'),
			likes = assign_key(data, 'likes'),
			length = assign_key(data, 'length'),
			dislikes = assign_key(data, 'dislikes'),
			demon = assign_key(data, 'demon'),
			stars = assign_key(data, 'stars'),
			feature_score = assign_key(data, 'feature_score'),
			auto = assign_key(data, 'auto'),
			password = assign_key(data, 'password'),
			two_player = assign_key(data, 'two_player'),
			song = assign_key(data, 'song'),
			objects_count = assign_key(data, 'objects_count'),
			account_id = assign_key(data, 'account_id'),
			coins = assign_key(data, 'coins'),
			coins_verified = assign_key(data, 'coins_verified'),
			requested_stars = assign_key(data, 'requested_stars'),
			extra_string = assign_key(data, 'extra_string'),
			daily_id = assign_key(data, 'daily_id'),
			epic = assign_key(data, 'epic'),
			demon_type = assign_key(data, 'demon_type'),
			seconds_spent_editing = assign_key(data, 'seconds_spent_editing'),
			seconds_spent_editing_copies = assign_key(data, 'seconds_spent_editing_copies'),
			original = assign_key(data, 'original'),
			record_type = record_type,
			manual_submission = submission,
			unprocessed_data = {}
		)
		record.save()
		record.create_user()
		return record

def process_levels_in_submission(level_list, record_type, submission):
	#records = []
	for level in level_list:
		level_id = level['id'] if 'id' in level else 0
		level_object = get_level_object(level_id)
		
		record = create_level_record_from_data(level, level_object, record_type, submission)

		if 'level_string' in level:
			level_string = level['level_string']
			record.level_string = create_level_string(level_string)
			record.save()

		level_object.revalidate_cache()

def upload_submission(file, user):
	data_path = get_data_path()

	content = json.load(file)

	submission_id = upload_submission_data(content, user)

	f = open(f"{data_path}/ManualSubmission/{submission_id}", "w")
	json.dump(content, f)
	f.close()

	return True

def upload_submission_data(data, user, parent=None):
	submission = ManualSubmission(
		author = user,
		created = data['created'],
		comment = data['comment'],
		parent = parent,
	)

	submission.save()

	if "levels" in data:
		process_levels_in_submission(data['levels'], LevelRecordType.MANUAL, submission)

	if "submissions" in data:
		for child in data['submissions']:
			upload_submission_data(child, user, submission)

	return submission.pk

def process_submission(submission_id):
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