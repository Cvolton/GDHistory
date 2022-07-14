from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive

from django.db.models import Min, Max, Q
from django.db.models.functions import Coalesce

from . import utils

from datetime import datetime
import os

class LevelRecordType(models.TextChoices):
		GLM_03 = 'glm_03', _('GLM_03')
		GLM_10 = 'glm_10', _('GLM_10')
		GLM_16 = 'glm_16', _('GLM_16')
		DOWNLOAD = 'download', _('downloadGJLevel')
		GET = 'get', _('getGJLevels')

class HistoryUser(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
    )
    def __str__(self):
        return self.user.username

class SaveFile(models.Model):
	author = models.ForeignKey(
		HistoryUser,
		on_delete=models.CASCADE,
		db_index=True,
	)
	submitted = models.DateTimeField(default=timezone.now)
	created = models.DateTimeField(default=timezone.now, db_index=True)
	comment = models.CharField(max_length=255)
	is_processed = models.BooleanField(default=False)

	player_name = models.TextField(blank=True, null=True)
	player_user_id = models.IntegerField(blank=True, null=True)
	player_account_id = models.IntegerField(blank=True, null=True)
	binary_version = models.IntegerField(blank=True, null=True)
	#also raw save file with password stripped out stored on the side in a file

class ServerResponse(models.Model):

	created = models.DateTimeField(default=timezone.now, db_index=True)
	unprocessed_post_parameters = models.JSONField()
	endpoint = models.CharField(max_length=32)

	get_type = models.IntegerField(blank=True, null=True, db_index=True)
	get_page = models.IntegerField(blank=True, null=True, db_index=True)

	def assign_get(self):
		if not self.endpoint.startswith("getGJLevels"): return

		get_type = self.unprocessed_post_parameters["type"] if "type" in self.unprocessed_post_parameters else None
		get_page = self.unprocessed_post_parameters["page"] if "page" in self.unprocessed_post_parameters else None
		self.save()

	class Meta:
		indexes = [
			models.Index(fields=['created', 'endpoint'])
		]

class GDUser(models.Model):
	online_id = models.IntegerField(unique=True, db_index=True) #k6

	cache_username = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_non_player_username = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_account_id = models.IntegerField(blank=True, null=True, db_index=True)

	cache_username_created = models.DateTimeField(blank = True, null=True, db_index=True)
	cache_non_player_username_created = models.DateTimeField(blank = True, null=True, db_index=True)

	def revalidate_cache(self):
		username_record_set = self.gduserrecord_set.exclude( Q(username='-') | Q(username=None) ).order_by('-cache_created')
		username_record = username_record_set[:1]
		if len(username_record) > 0:
			self.cache_username = username_record[0].username
			self.cache_username_created = username_record[0].cache_created
			print("Setting username from user record")
			if self.cache_username == 'Player':
				non_player_username_record = username_record_set.exclude(username='Player')[:1]
			else:
				non_player_username_record = username_record

			if len(non_player_username_record) > 0:
				self.cache_non_player_username = non_player_username_record[0].username
				self.cache_non_player_username_created = non_player_username_record[0].cache_created
				print("Setting non-player username from user record")
		else:
			print(":((( User record not found")

	def update_with_record(self, record):
		should_save = False
		if self.cache_username_created is not None and is_naive(self.cache_username_created):
			self.cache_username_created = make_aware(self.cache_username_created)

		if record.cache_created is not None and is_naive(record.cache_created):
			record.cache_created = make_aware(record.cache_created)

		if record.username is None or record.username == '-' or record.username == '' or record.cache_created is None:
			print("Null username")
			return

		if self.cache_username_created is None or record.cache_created > self.cache_username_created:
			print("Setting username from user record")
			self.cache_username = record.username
			self.cache_username_created = record.cache_created
			should_save = True

		if record.username != 'Player' and (self.cache_non_player_username_created is None or record.cache_created > self.cache_non_player_username_created):
			print("Setting non-player username from user record")
			self.cache_non_player_username = record.username
			self.cache_non_player_username_created = record.cache_created
			should_save = True

		if should_save:
			self.save()
			

class GDUserRecord(models.Model):
	user = models.ForeignKey(
		GDUser,
		on_delete=models.CASCADE,
		db_index=True,
	)

	record_type = models.CharField(
		max_length=8,
		choices=LevelRecordType.choices,
	)

	account_id = models.IntegerField(blank=True, null=True) #k60
	username = models.CharField(blank=True, null=True, max_length=255, db_index=True) #k5 #in the real world <= 15

	save_file = models.ManyToManyField(
		SaveFile,
	)

	server_response = models.ForeignKey(
		ServerResponse,
		on_delete=models.CASCADE,
		blank=True, null=True,
		db_index=True,
	)

	cache_created = models.DateTimeField(blank = True, null=True, db_index=True)

	def get_serialized_base(self):
		response = {
			'user_id': self.user.online_id,
			'username': self.username,
			'account_id': self.account_id
		}
		return response

class Song(models.Model):
	online_id = models.IntegerField(unique=True)

	cache_song_name = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_artist_name = models.CharField(blank=True, null=True, max_length=255, db_index=True)

	def revalidate_cache(self):
		best_record = self.songrecord_set.annotate(newest_created=Max('save_file__created'), real_date=Coalesce('newest_created', 'server_response__created')).exclude(real_date=None, song_name=None).order_by('-real_date')[:1]
		if len(best_record) < 1:
			self.cache_song_name = None
			self.cache_artist_name = None
			self.save()
			return

		best_record = best_record[0]
		self.cache_song_name = best_record.song_name
		self.cache_artist_name = best_record.artist_name
		self.save()

	def get_serialized_base(self):
		record = {
			'online_id': self.online_id,
			'song_name': self.cache_song_name,
			'arist_name': self.cache_artist_name
		}
		return record


class SongRecord(models.Model):

	class RecordType(models.TextChoices):
		MDLM_001 = 'mdlm_001', _('MDLM_001')
		SONG_INFO = 'songinfo', _('getGJSongInfo')
		LEVEL_INFO = 'levelinfo', _('getGJLevels')

	record_type = models.CharField(
		max_length=9,
		choices=RecordType.choices,
	)

	song = models.ForeignKey(
		Song,
		on_delete=models.CASCADE,
		db_index=True,
	)

	save_file = models.ManyToManyField(
		SaveFile,
	)

	server_response = models.ManyToManyField(
		ServerResponse,
	)

	song_name = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	artist_id = models.IntegerField(null=True)
	artist_name = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	size = models.FloatField(null=True)
	youtube_id = models.TextField(blank=True, null=True)
	youtube_channel = models.TextField(blank=True, null=True)
	is_verified = models.BooleanField(null=True)
	link = models.TextField(blank=True, null=True)

	unprocessed_data = models.JSONField() #this field should only be used for archival purposes, do not pull data from this directly in production

class Level(models.Model):
	online_id = models.IntegerField(db_index=True, unique=True)
	comment = models.TextField(blank=True, null=True)
	is_public = models.BooleanField(blank=True, null=True, db_index=True) #this is to prevent leaking unlisted levels publicly
	is_deleted = models.BooleanField(blank=True, null=True, db_index=True)
	hide_from_search = models.BooleanField(db_index=True, default=False)

	cache_level_name = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_submitted = models.DateTimeField(blank=True, null=True, db_index=True)
	cache_downloads = models.IntegerField(db_index=True, default=0)
	cache_likes = models.IntegerField(db_index=True, default=0)
	cache_rating_sum = models.IntegerField(db_index=True, default=0)
	cache_rating = models.IntegerField(db_index=True, default=0)
	cache_demon = models.BooleanField(db_index=True, default=False)
	cache_auto = models.BooleanField(db_index=True, default=False)
	cache_demon_type = models.IntegerField(blank=True, null=True, db_index=True)
	cache_stars = models.IntegerField(db_index=True, default=0)
	cache_username = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_level_string_available = models.BooleanField(default=False, db_index=True)
	cache_user_id = models.IntegerField(blank=True, null=True, db_index=True)
	cache_daily_id = models.IntegerField(default=0, db_index=True)
	cache_needs_updating = models.BooleanField(default=True, db_index=True)
	cache_available_versions = models.IntegerField(default=0, db_index=True)
	cache_search_available = models.BooleanField(default=False, db_index=True)
	cache_main_difficulty = models.IntegerField(default=0, db_index=True)

	submitted = models.DateTimeField(default=timezone.now, db_index=True)
	class Meta:
		indexes = [
			#models.Index(fields=['cache_search_available', 'online_id']),
			#models.Index(fields=['cache_search_available', 'cache_level_name']),
			#models.Index(fields=['cache_search_available', 'cache_submitted']),
			#models.Index(fields=['cache_search_available', 'cache_downloads']),
			##models.Index(fields=['cache_search_available', 'cache_likes']),
			#models.Index(fields=['cache_search_available', 'cache_username']),
			models.Index(fields=['online_id', 'cache_downloads']),
			models.Index(fields=['cache_level_name', 'cache_downloads']),
			models.Index(fields=['cache_submitted', 'cache_downloads']),
			models.Index(fields=['cache_likes', 'cache_downloads']),
			models.Index(fields=['cache_stars', 'cache_downloads']),
			models.Index(fields=['cache_username', 'cache_downloads']),
			models.Index(fields=['cache_user_id', 'cache_downloads']),
			models.Index(fields=['cache_available_versions', 'cache_downloads']),

			models.Index(fields=['cache_search_available', 'cache_level_name']),
			models.Index(fields=['cache_search_available', 'cache_user_id']),
		]

	def set_public(self, public):
		self.is_public = public
		self.save()

		self.levelrecord_set.update(cache_is_public=True)

	def verify_needs_updating(self):
		data_record = self.levelrecord_set.exclude( Q(level_name=None) | Q(level_string=None) ).order_by('-downloads')
		self.cache_needs_updating = False
		if len(data_record) > 0:
			best_record = self.levelrecord_set.exclude( Q(level_name=None) ).order_by('-downloads')[:1][0]

			level_strings = {}
			for record in data_record:
				level_strings[record.level_string.pk] = True
			self.cache_available_versions = len(level_strings)
			self.cache_level_string_available = True

			data_record = data_record[0]
			if best_record.description != data_record.description: self.cache_needs_updating = True
			if (best_record.official_song or 0) != (data_record.official_song or 0): self.cache_needs_updating = True
			if (best_record.song != data_record.song) and not ((data_record.song is None and best_record.song.online_id == 0) or (best_record.song is None and data_record.song.online_id == 0)): self.cache_needs_updating = True
			if (best_record.level_version or 0) != (data_record.level_version or 0): self.cache_needs_updating = True
			if (best_record.game_version or 0) != (data_record.game_version or 0): self.cache_needs_updating = True
			if (best_record.length or 0) != (data_record.length or 0): self.cache_needs_updating = True
			if (best_record.two_player or 0) != (data_record.two_player or 0): self.cache_needs_updating = True
			if (best_record.objects_count or 0) != (data_record.objects_count or 0): self.cache_needs_updating = True
			if (best_record.coins or 0) != (data_record.coins or 0): self.cache_needs_updating = True
			if (best_record.requested_stars or 0) != (data_record.requested_stars or 0): self.cache_needs_updating = True
			if (best_record.original or 0) != (data_record.original or 0): self.cache_needs_updating = True
		else:
			self.cache_needs_updating = True
			self.cache_level_string_available = False
		self.save()
	def update_with_record(self, record, record_date):
		changed = False
		check_level_string = False

		if record.downloads is not None and record_date is not None and (self.cache_downloads is None or int(record.downloads) > self.cache_downloads):
			changed = True
			self.cache_level_name = record.level_name
			self.cache_submitted = record_date
			self.cache_downloads = record.downloads or 0
			self.cache_likes = record.likes or 0
			self.cache_rating_sum = record.rating_sum or 0
			self.cache_rating = record.rating or 0
			self.cache_demon = record.demon or 0
			self.cache_auto = record.auto or 0
			self.cache_demon_type = record.demon_type or 0
			self.cache_stars = record.stars or 0
			self.cache_user_id = record.user_id or 0
			self.cache_main_difficulty = 0 if int(self.cache_rating) == 0 else int(self.cache_rating_sum) / int(self.cache_rating)
			self.cache_blank_name = (self.cache_level_name is None)
			check_level_string = True

			if record.real_user_record is not None and record.real_user_record.username is not None and record.real_user_record.username != '' and record.real_user_record.username != '-':
				self.cache_username = record.real_user_record.username

		if record.daily_id is not None and int(record.daily_id) > 0:
			changed = True
			self.cache_daily_id = record.daily_id

		if record.level_string:
			changed = True
			check_level_string = True

		if check_level_string:
			self.verify_needs_updating()

		if changed:
			self.cache_search_available = (self.is_public == True and self.hide_from_search == False and self.cache_level_name is not None)
			self.save()

	def revalidate_cache(self):
		best_record = self.levelrecord_set.annotate(oldest_created=Min('save_file__created'), real_date=Coalesce('oldest_created', 'server_response__created')).exclude( Q(real_date=None) | Q(level_name=None) ).order_by('-downloads', '-oldest_created')[:1]
		if len(best_record) < 1:
			self.cache_level_name = None
			self.save()
			return

		self.update_with_record(best_record[0], best_record[0].real_date)

		best_daily_record = self.levelrecord_set.exclude( Q(daily_id = 0) | Q(daily_id = None) ).order_by('-daily_id')
		best_record_set = best_daily_record[:1]
		if len(best_record_set) > 0:
			self.update_with_record(best_record_set[0], None)

		#set username
		best_record = best_record[0]
		self.cache_username = best_record.username
		if best_record.username is None or best_record.username == '-':
			user_record = GDUser.objects.filter(online_id=self.cache_user_id)[:1]
			if len(user_record) > 0:
				self.cache_username = user_record[0].cache_username
				print("Setting username from user record")
			else:
				print(":(((( Unable to set username")

		#needs updating field
		self.verify_needs_updating()

		self.save()

	def get_serialized_base(self):
		response = {
			'online_id': self.online_id,
			'comment': self.comment,
			'is_deleted': self.is_deleted,
			'cache_level_name': self.cache_level_name,
			'cache_submitted': self.cache_submitted,
			'cache_downloads': self.cache_downloads,
			'cache_likes': self.cache_likes,
			'cache_rating_sum': self.cache_rating_sum,
			'cache_rating': self.cache_rating,
			'cache_demon': self.cache_demon,
			'cache_auto': self.cache_auto,
			'cache_demon_type': self.cache_demon_type,
			'cache_stars': self.cache_stars,
			'cache_username': self.cache_username,
			'cache_level_string_available': self.cache_level_string_available,
			'cache_user_id': self.cache_user_id,
			'cache_daily_id': self.cache_daily_id,
			'cache_needs_updating': self.cache_needs_updating,
			'cache_available_versions': self.cache_available_versions,
			'cache_search_available': self.cache_search_available,
			'cache_main_difficulty': self.cache_main_difficulty,
		}
		return response

class LevelDateEstimation(models.Model):
	level = models.ForeignKey(
		Level,
		on_delete=models.CASCADE,
		db_index=True,
	)

	submitted = models.DateTimeField(default=timezone.now, db_index=True)

	created = models.DateTimeField(db_index=True)
	relative_upload_date = models.CharField(blank=True, null=True, max_length=255)

	estimation = models.DateTimeField(blank=True, null=True, db_index=True)

	def calculate(self):
		if "year" in self.relative_upload_date:
			years = int(self.relative_upload_date.split(' ')[0])
			self.estimation = self.created.replace(year=self.created.year - years)
		else:
			return

		self.save()

	def get_serialized_base(self):
		response = {
			'created': self.created,
			'relative_upload_date': self.relative_upload_date,
			'estimation': self.estimation,
			'online_id': self.level.online_id
		}
		return response

class LevelString(models.Model):
	sha256 = models.CharField(max_length=64, db_index=True)
	requires_base64 = models.BooleanField(default=False)

	def get_file_path(self):
		data_path = utils.get_data_path()
		directory = f"{data_path}/LevelString/{self.sha256[:2]}"
		if not os.path.exists(directory):
			os.mkdir(directory)
		return f"{directory}/{self.sha256}"

	def load_file_content(self):
		import base64

		directory = self.get_file_path()
		if not os.path.exists(directory):
			return None
		with open(directory, 'rb') as f:
			content = f.read()
			print(content)

		if self.requires_base64:
			content = base64.b64encode(content, altchars=b'-_')

		content = content.decode('windows-1252')
		return content


class LevelRecord(models.Model):

	record_type = models.CharField(
		max_length=8,
		choices=LevelRecordType.choices,
	)

	level = models.ForeignKey(
		Level,
		on_delete=models.CASCADE,
		db_index=True,
	)

	save_file = models.ManyToManyField(
		SaveFile
	)

	server_response = models.ForeignKey(
		ServerResponse,
		on_delete=models.CASCADE,
		blank=True, null=True,
		db_index=True,
	)

	level_string = models.ForeignKey(
		LevelString,
		on_delete=models.CASCADE,
		blank=True, null=True,
		db_index=True,
	)

	cache_user_record = models.ForeignKey(
		GDUserRecord,
		on_delete=models.SET_NULL,
		blank=True, null=True,
		db_index=True,
		related_name= "gd_user_record_set_cache"
	)

	real_user_record = models.ForeignKey(
		GDUserRecord,
		on_delete=models.SET_NULL,
		blank=True, null=True,
		db_index=True,
		related_name= "gd_user_record_set_real"
	)

	submitted = models.DateTimeField(default=timezone.now, db_index=True)

	cache_is_public = models.BooleanField(blank=True, null=True, db_index=True)

	level_name = models.CharField(blank=True, null=True, max_length=255, db_index=True) #k2 #in the real world this can't be more than 20, unless you're dealing with private server save files
	description = models.TextField(blank=True, null=True) #k3
	description_encoded = models.BooleanField(blank=True, null=True)
	username = models.CharField(blank=True, null=True, max_length=255, db_index=True) #k5 #in the real world <= 15
	user_id = models.IntegerField(blank=True, null=True, db_index=True) #k6
	official_song = models.IntegerField(blank=True, null=True) #k8
	rating = models.IntegerField(blank=True, null=True, db_index=True) #k9
	rating_sum = models.IntegerField(blank=True, null=True, db_index=True) #k10
	downloads = models.IntegerField(blank=True, null=True, db_index=True) #k11
	level_version = models.IntegerField(blank=True, null=True) #k16
	game_version = models.IntegerField(blank=True, null=True) #k17
	likes = models.IntegerField(blank=True, null=True, db_index=True) #k22
	length = models.IntegerField(blank=True, null=True) #k23 #technically speaking this would be better as an ENUM but nothing actually guarantees that the value won't go out of bounds
	dislikes = models.IntegerField(blank=True, null=True) #k24
	demon = models.BooleanField(blank=True, null=True, db_index=True) #k25
	stars = models.IntegerField(blank=True, null=True, db_index=True) #k26
	feature_score = models.IntegerField(blank=True, null=True) #k27
	auto = models.BooleanField(blank=True, null=True, db_index=True) #k33
	password = models.IntegerField(blank=True, null=True) #k41
	two_player = models.BooleanField(blank=True, null=True) #k43
	objects_count = models.IntegerField(blank=True, null=True) #k48
	account_id = models.IntegerField(blank=True, null=True) #k60
	coins = models.IntegerField(blank=True, null=True) #k64
	coins_verified = models.BooleanField(blank=True, null=True) #k65
	requested_stars = models.IntegerField(blank=True, null=True) #k66
	extra_string = models.TextField(blank=True, null=True) #k67 #also known as the capacity string
	daily_id = models.IntegerField(blank=True, null=True, db_index=True) #k74
	epic = models.BooleanField(blank=True, null=True) #k75
	demon_type = models.IntegerField(blank=True, null=True) #k76
	seconds_spent_editing = models.IntegerField(blank=True, null=True) #k80
	seconds_spent_editing_copies = models.IntegerField(blank=True, null=True) #k81
	relative_upload_date = models.CharField(blank=True, null=True, max_length=255) #28 #in the real world <= 10
	relative_update_date = models.CharField(blank=True, null=True, max_length=255) #29 #in the real world <= 10
	original = models.IntegerField(blank=True, null=True) #k42

	song = models.ForeignKey(
		Song,
		on_delete=models.CASCADE,
		blank=True, null=True,
		db_index=True,
	)

	unprocessed_data = models.JSONField() #this field should only be used for archival purposes, do not pull data from this directly in production

	#also levelstring stored on the side
	#and raw server response for download type records stored on the side

	def get_encoded_description(self):
		return self.description if self.description_encoded is True else utils.encode_base64_text(self.description)

	def create_user(self):

		record_date = None
		if self.server_response: record_date = self.server_response.created
		if self.save_file.count() > 0: record_date = self.save_file.order_by('-created')[:1][0].created
		
		user_object = utils.get_user_object(self.user_id)
		user_record = utils.create_user_record(user_object, self.account_id, self.username, record_date, self.server_response, self.save_file, self.record_type)
		if user_object is not None: user_object.update_with_record(user_record)

		self.real_user_record = user_record
		self.save()

	def get_serialized_base(self):
		response = self.__dict__.copy()

		del response['_prefetched_objects_cache']
		del response['_state']
		del response['unprocessed_data']
		del response['username']
		del response['user_id']
		del response['real_user_record_id']
		del response['cache_user_record_id']
		del response['level_id']
		del response['server_response_id']
		del response['submitted']
		del response['song_id']
		del response['level_string_id']

		response['level_string_available'] = self.level_string is not None

		return response

	def get_serialized_full(self):
		response = self.get_serialized_base()
		response['real_user_record'] = self.real_user_record.get_serialized_base()
		response['song'] = None if self.song is None else self.song.get_serialized_base()
		return response