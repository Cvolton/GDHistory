from .models import ManualSubmission, Level, LevelRecord, HistoryUser, LevelRecordType
from .utils import assign_key, get_data_path, assign_key_no_pop, create_level_string, get_song_object, decode_base64_text, get_level_object

from django.utils import timezone

import json
import os

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
			relative_upload_date = assign_key_no_pop(data, 'relative_upload_date'),
			relative_update_date = assign_key_no_pop(data, 'relative_update_date'),
			original = assign_key_no_pop(data, 'original'),
			manual_submission = submission,
			record_type = record_type,
			song = get_song_object(assign_key_no_pop(data, 'custom_song'))
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
			relative_upload_date = assign_key(data, 'relative_upload_date'),
			relative_update_date = assign_key(data, 'relative_update_date'),
			original = assign_key(data, 'original'),
			record_type = record_type,
			manual_submission = submission,
			unprocessed_data = {},
			song = get_song_object(assign_key(data, 'custom_song'))
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
  
def validate_submission(data):
	if "created" not in data: return 1
	if not isinstance(data["created"], str): return 2
	try:
		timezone.datetime.fromisoformat(data["created"])
	except:
		return False
	
	if "submissions" in data:
		for child in data['submissions']:
			res = validate_submission(child)
			if not res: return res + 10
	if "levels" in data:
		for level in data['levels']:
			if not "id" in level: return 4
			if not isinstance(level["id"], int) and not level["id"].isnumeric(): return 5
   
	return 0

def upload_submission_delayed(content, user):
	data_path = get_data_path()

	os.makedirs(f"{data_path}/ManualSubmission-Delayed/{user.pk}", exist_ok=True)
	with open(f"{data_path}/ManualSubmission-Delayed/{user.pk}/{data}", "w") as f:
		json.dump(content, f)

def process_delayed_submissions():
	data_path = get_data_path()
	directory = f"{data_path}/ManualSubmission-Delayed/"
	users = os.listdir(directory)
	for user in users:
		user_object = HistoryUser.objects.get(pk=user)
		files = os.listdir(f"{directory}/{user}")
		for file in files:
			with open(f"{directory}/{user}/{file}", "r") as f:
				data = json.load(f)
				upload_submission_data(data, user_object, None, True)
				os.remove(f"{directory}/{user}/{file}")

def delete_queued_submissions():
	queued = ManualSubmission.objects.filter(queued_deletion=True)
	for submission in queued:
		delete_submission(submission)

def delete_submission(submission):
	print(f"Deleting {submission.pk}")
	for subsubmission in submission.manualsubmission_set.all():
		delete_submission(subsubmission)

	levels = [levelrecord.level for levelrecord in submission.levelrecord_set.all()]
	submission.delete()

	for level in levels:
		level.cache_needs_revalidation = True
		level.best_record = None
		level.save()

def upload_submission(file, user):

	content = json.load(file)

	upload_submission_data(content, user, None, True)

	return True

def upload_submission_data(data, user, parent=None, save_file=False):
	submission = ManualSubmission(
		author = user,
		created = data['created'],
		comment = data['comment'],
		parent = parent,
	)

	submission.save()

	if save_file:
		data_path = get_data_path()

		f = open(f"{data_path}/ManualSubmission/{submission.pk}", "w")
		json.dump(data, f)
		f.close()

	if "levels" in data:
		process_levels_in_submission(data['levels'], LevelRecordType.MANUAL, submission)

	if "submissions" in data:
		for child in data['submissions']:
			upload_submission_data(child, user, submission)

	submission.cache_level_count = None
	submission.cache_full_level_count = None
	submission.cache_children_count = None
	submission.save()

	return submission.pk