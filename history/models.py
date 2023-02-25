from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive, timedelta
from django.core.cache import cache

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
		MANUAL = 'manual', _('manual')

class HistoryUser(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_index=True,
    )
    def __str__(self):
        return self.user.username

class ManualSubmission(models.Model):
	author = models.ForeignKey(
		HistoryUser,
		on_delete=models.CASCADE,
		db_index=True,
	)
	submitted = models.DateTimeField(default=timezone.now)
	created = models.DateTimeField(default=timezone.now, db_index=True)
	comment = models.CharField(max_length=255)
	parent = models.ForeignKey(
		"ManualSubmission",
		on_delete=models.CASCADE,
		blank=True, null=True,
		db_index=True,
	)

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

	cache_levels_count = models.IntegerField(blank=True, null=True)

	def get_count(self):
		if self.cache_levels_count: return self.cache_levels_count
		count = self.levelrecord_set.count()
		if self.is_processed:
			self.cache_levels_count = count
			self.save()
		return count

class ServerResponse(models.Model):

	created = models.DateTimeField(default=timezone.now, db_index=True)
	unprocessed_post_parameters = models.JSONField()
	endpoint = models.CharField(max_length=32)

	get_type = models.IntegerField(blank=True, null=True, db_index=True)
	get_page = models.IntegerField(blank=True, null=True, db_index=True)

	def assign_get(self):
		if not self.endpoint.startswith("getGJLevels"): return

		self.get_type = self.unprocessed_post_parameters["type"] if "type" in self.unprocessed_post_parameters else None
		self.get_page = self.unprocessed_post_parameters["page"] if "page" in self.unprocessed_post_parameters else None
		self.save()

	def generate_date_estimation(self):
		if not self.endpoint.startswith("getGJLevels"): return
		if self.get_type != 4 or (self.get_page is not None and self.get_page != 0): return
		if LevelDateEstimation.objects.filter(server_response=self).count() > 0: return
		if "star" in self.unprocessed_post_parameters and self.unprocessed_post_parameters["star"] != 0: return

		print(f"Generating date estimate from {self.created}")

		record_set = self.levelrecord_set.prefetch_related('level').order_by('-level__online_id')[:1]
		if record_set.count() < 1: return
		
		level_object = utils.get_level_object(record_set[0].level.online_id)

		estimation = LevelDateEstimation(server_response=self, created=self.created, estimation=self.created, level=level_object)
		estimation.save()


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
		username_record_set = self.gduserrecord_set.exclude( Q(username='-') | Q(username=None) | Q(username='Unknown') ).order_by('-cache_created')
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

			self.save()
		else:
			print(":((( User record not found")

	def update_with_record(self, record):
		if record is not None and record.username is not None and self.cache_username != record.username:
			self.revalidate_cache()

	"""Implementation removed because usernames don't change most of the time therefore it's better to just revalidate cache every once in a while
	def update_with_record(self, record):
		should_save = False
		if record is None:
			return

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
			self.save()"""
			

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

	manual_submission = models.ForeignKey(
		ManualSubmission,
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
	online_id = models.IntegerField(unique=True, db_index=True)

	cache_song_name = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_artist_name = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_submitted = models.DateTimeField(blank=True, null=True, db_index=True)

	cache_needs_revalidation = models.BooleanField(db_index=True, default=False)

	def update_with_record(self, record):
		if record.song_name != self.cache_song_name or record.artist_name != self.cache_artist_name:
			self.cache_needs_revalidation = True
			self.save()

	"""		This implementation would require a date cache to be built in SongRecord, something not currently worth doing since the data almost never changes
	def update_with_record(self, record):
		if self.cache_submitted is None:
			self.revalidate_cache()
			return
		record_date = None
		if self.cache_submitted is not None and is_naive(self.cache_submitted):
			self.cache_submitted = make_aware(self.cache_submitted)

		save_files = record.save_file.order_by('-created')[:1]
		server_responses = record.server_response.order_by('-created')[:1]
		if len(server_responses) > 0:
			server_response = server_responses[0]
			if server_response is not None and server_response.created is not None: 
				record_date = make_aware(server_response.created) if is_naive(server_response.created) else server_response.created
		elif len(save_files) > 0:
			save_file = save_files[0]
			if save_file is not None and save_file.created is not None: 
				record_date = make_aware(save_file.created) if is_naive(save_file.created) else save_file.created

		if record_date is not None and record_date > self.cache_submitted:
			self.cache_song_name = record.song_name
			self.cache_artist_name = record.artist_name
			self.cache_submitted = record_date
			self.save()"""

	def revalidate_cache(self):
		self.cache_needs_revalidation = False
		
		best_record = self.songrecord_set.annotate(newest_created=Max('save_file__created'), real_date=Coalesce('newest_created', 'server_response__created')).exclude(real_date=None, song_name=None).order_by('-real_date')[:1]
		if len(best_record) < 1:
			self.cache_song_name = None
			self.cache_artist_name = None
			self.save()
			return

		best_record = best_record[0]
		self.cache_song_name = best_record.song_name
		self.cache_artist_name = best_record.artist_name
		self.cache_submitted = best_record.real_date

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
	is_deleted = models.BooleanField(default=False, db_index=True)
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

	cache_max_stars = models.IntegerField(db_index=True, default=0)
	cache_filter_difficulty = models.IntegerField(default=0, db_index=True)
	#cache_max_filter_difficulty = models.IntegerField(default=0, db_index=True)
	cache_length = models.IntegerField(default=0, db_index=True)
	cache_featured = models.IntegerField(default=0, db_index=True)
	cache_max_featured = models.IntegerField(default=0, db_index=True)
	cache_epic = models.IntegerField(default=0, db_index=True)
	cache_max_epic = models.IntegerField(default=0, db_index=True)
	cache_two_player = models.IntegerField(db_index=True, default=False)
	cache_max_two_player = models.IntegerField(db_index=True, default=False)
	cache_original = models.IntegerField(default=0, db_index=True)
	cache_max_original = models.IntegerField(default=0, db_index=True)

	cache_needs_revalidation = models.BooleanField(db_index=True, default=False)
	cache_needs_search_update = models.BooleanField(db_index=True, default=False)

	needs_priority_download = models.BooleanField(db_index=True, default=False)

	submitted = models.DateTimeField(default=timezone.now, db_index=True)
	class Meta:
		indexes = [
			#models.Index(fields=['-cache_downloads']),

			#models.Index(fields=['cache_search_available', 'online_id']),
			#models.Index(fields=['cache_search_available', 'cache_level_name']),
			#models.Index(fields=['cache_search_available', 'cache_submitted']),
			#models.Index(fields=['cache_search_available', 'cache_downloads']),
			##models.Index(fields=['cache_search_available', 'cache_likes']),
			#models.Index(fields=['cache_search_available', 'cache_username']),
			
			#models.Index(fields=['online_id', 'cache_downloads']),
			#models.Index(fields=['cache_level_name', 'cache_downloads']),
			#models.Index(fields=['cache_submitted', 'cache_downloads']),
			#models.Index(fields=['cache_likes', 'cache_downloads']),
			#models.Index(fields=['cache_stars', 'cache_downloads']),
			#models.Index(fields=['cache_username', 'cache_downloads']),
			#models.Index(fields=['cache_user_id', 'cache_downloads']),
			#models.Index(fields=['cache_available_versions', 'cache_downloads']),

			#models.Index(fields=['cache_level_name']),
			#models.Index(fields=['cache_user_id']),
			#models.Index(fields=['cache_auto', 'cache_demon', 'cache_main_difficulty'], name='auto_demon_diff'),
			#models.Index(fields=['cache_demon', 'cache_demon_type']),

			#models.Index(fields=['cache_main_difficulty'], name='diff'),

			#models.Index(fields=['cache_demon', 'cache_downloads'], name='demon_downloads'),
			#models.Index(fields=['cache_demon', 'cache_likes'], name='demon_likes'),
			#models.Index(fields=['cache_auto', 'cache_downloads'], name='auto_downloads'),
			#models.Index(fields=['cache_auto', 'cache_likes'], name='auto_likes'),

			#models.Index(fields=['cache_level_string_available'], name='playable'),
			#models.Index(fields=['is_deleted'], name='deleted'),
			#models.Index(fields=['is_deleted', 'cache_level_string_available'], name='deleted_playable'),
			#models.Index(fields=['is_deleted', 'cache_max_stars'], name='deleted_wasrated'),

			#models.Index(fields=['cache_stars', 'cache_max_stars'], name='wasrated_staronly'),
			#models.Index(fields=['is_deleted', 'cache_stars'], name='deleted_staronly'),
			#models.Index(fields=['is_deleted', 'cache_level_string_available', 'cache_stars'], name='deleted_playable_staronly'),

			#models.Index(fields=['cache_level_string_available', 'is_deleted']),
		]

	def set_public(self, public):
		self.is_public = public
		#self.save()

		#self.levelrecord_set.update(cache_is_public=True)

	def verify_needs_updating(self):
		print("verifying needs updating")

		data_record = self.levelrecord_set.filter(cache_is_dupe=False).exclude( Q(level_name=None) | Q(level_string=None) ).prefetch_related('level_string').prefetch_related('song').order_by('-downloads')
		self.cache_needs_updating = False
		if len(data_record) > 0:
			best_record = self.levelrecord_set.filter(cache_is_dupe=False).exclude( Q(level_name=None) ).prefetch_related('level_string').prefetch_related('song').order_by('-downloads')[:1][0]

			level_strings = {}
			for record in data_record:
				level_strings[record.level_string.get_decompressed_sha256()] = True
			self.cache_available_versions = len(level_strings)
			self.cache_level_string_available = True

			data_record = data_record[0]
			if best_record.description != data_record.description and not best_record.downloads == data_record.downloads: self.cache_needs_updating = True
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
		
		if self.cache_needs_updating == True and self.cache_stars > 0 and not self.is_deleted:
			self.needs_priority_download = True
		#self.save()
	def assign_username(self):
		try:
			user_object = GDUser.objects.get(online_id=self.cache_user_id)
			self.cache_username = user_object.cache_non_player_username if user_object.cache_non_player_username is not None else user_object.cache_username
			print(user_object.cache_username)
			print("assigned username")
		except:
			print("couldnt assign username")

	def update_with_record(self, record, record_date, force=False):
		print("updating with record")

		changed = False
		check_level_string = False

		if record.stars is not None and int(record.stars) > self.cache_max_stars: 
			self.cache_max_stars = record.stars
			changed = True
		if record.feature_score is not None and int(record.feature_score) > self.cache_max_featured:
			self.cache_max_featured = record.feature_score
			changed = True
		if record.epic is not None and int(record.epic) > self.cache_max_epic:
			self.cache_max_epic = record.epic
			changed = True
		if record.two_player is not None and int(record.two_player) > self.cache_max_two_player:
			self.cache_max_two_player = record.two_player
			changed = True
		if record.original is not None and int(record.original) > self.cache_max_original:
			self.cache_max_original = record.original
			changed = True

		if force or (record.downloads is not None and record_date is not None and (self.cache_downloads == 0 or int(record.downloads) >= self.cache_downloads)):
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

			self.cache_length = record.length or 0
			self.cache_featured = record.feature_score or 0
			self.cache_epic = record.epic or 0
			self.cache_two_player = record.two_player or 0
			self.cache_original = record.original or 0

			if record.auto:
				self.cache_filter_difficulty = 1
			elif not record.demon:
				if self.cache_main_difficulty == 0:
					self.cache_filter_difficulty = -1
				else:
					self.cache_filter_difficulty = self.cache_main_difficulty + 1
			else:
				if int(self.cache_demon_type) < 3: #hard demon
					self.cache_filter_difficulty = 10
				elif int(self.cache_demon_type) < 5: #easy medium
					self.cache_filter_difficulty = 8 - 3 + int(self.cache_demon_type)
				else:
					self.cache_filter_difficulty = 11 - 5 + int(self.cache_demon_type)


			if record.real_user_record is not None and record.real_user_record.username is not None and record.real_user_record.username != '' and record.real_user_record.username != '-':
				self.cache_username = record.real_user_record.username

		if record.daily_id is not None and int(record.daily_id) > 0:
			changed = True
			self.cache_daily_id = record.daily_id

		if record.level_string:
			changed = True
			check_level_string = True

		if check_level_string and not force:
			self.verify_needs_updating()

		if self.cache_username is None:
			self.assign_username()
			changed = True

		if changed:
			self.cache_search_available = (self.is_public == True and self.hide_from_search == False and self.cache_level_name is not None)
		
		if changed and not force:
			self.save()

	def recalculate_maximums(self):
		maximums = self.levelrecord_set.filter(cache_is_dupe=False).aggregate(Max('stars'), Max('feature_score'), Max('epic'), Max('two_player'), Max('original'), Max('daily_id'))
		self.cache_max_stars = maximums['stars__max'] or 0
		#self.cache_max_filter_difficulty = models.IntegerField(default=0, db_index=True)
		self.cache_max_featured = maximums['feature_score__max'] or 0
		self.cache_max_epic = maximums['epic__max'] or 0
		self.cache_max_two_player = maximums['two_player__max'] or 0
		self.cache_max_original = maximums['original__max'] or 0
		self.cache_daily_id = maximums['daily_id__max'] or 0
		print("set maximums, not saved")

	def dedup_records(self):
		"""This ensures there is only one record of each level version with cache_is_dupe set to False. The record with the highest amount of downloads is also kept."""
		print("deduplicating records")

		record_strings = set()
		records_to_update = set()
		highest_downloads = 0
		highest_downloads_record = None
		highest_downloads_with_levelstring = 0
		highest_downloads_with_levelstring_record = None

		for record in self.levelrecord_set.filter(cache_is_dupe=False).order_by('downloads'):
			if not record.real_user_record:
				record.create_user()
			#name, rating_sum, ratings, demon, auto, stars, version, real_user_record, game_version, levelstring
			current_record_string = f"{record.level_name or 0}, {record.rating or 0}, {record.rating_sum or 0}, {record.auto or 0}, {record.demon or 0}, {record.stars or 0}, {record.demon_type or 0}, {record.level_version or 0}, {record.real_user_record.get_serialized_base() if record.real_user_record else (record.username or 0)}, {record.game_version or 0}, {record.level_string or 0}, {record.coins or 0}, {record.description or 0}, {record.song or 0}, {record.official_song or 0}, {record.feature_score or 0}, {record.epic or 0}, {record.password or 0}, {record.two_player or 0}, {record.objects_count or 0}, {record.extra_string or 0}, {record.original or 0}"
			if (record.downloads or 0) > highest_downloads:
				highest_downloads_record = record
				highest_downloads = record.downloads or 0

			if record.level_string and (record.downloads or 0) > highest_downloads_with_levelstring:
				highest_downloads_with_levelstring_record = record
				highest_downloads_with_levelstring = record.downloads or 0

			if current_record_string in record_strings:
				record.cache_is_dupe = True
				records_to_update.add(record)
			record_strings.add(current_record_string)
			print(f"{record} - {current_record_string} - {record.cache_is_dupe}")

		if highest_downloads_record in records_to_update: records_to_update.remove(highest_downloads_record)
		if highest_downloads_with_levelstring_record in records_to_update: records_to_update.remove(highest_downloads_with_levelstring_record)
		self.levelrecord_set.bulk_update(records_to_update, ['cache_is_dupe'], batch_size=1000)

	def revalidate_cache(self):
		self.cache_needs_revalidation = False
		self.dedup_records()

		self.recalculate_maximums()

		#best_record = best_record.annotate(oldest_created=Min('save_file__created'), real_date=Coalesce('oldest_created', 'server_response__created'))

		best_record = self.levelrecord_set.filter(cache_is_dupe=False).exclude( Q(level_name=None) ).order_by('-downloads')[:1]
		if len(best_record) < 1:
			self.cache_level_name = None
			self.save()
			return

		best_record = best_record[0]
		real_date = best_record.server_response.created if best_record.server_response else best_record.save_file.aggregate(oldest=Min('created'))['oldest']

		self.update_with_record(best_record, real_date, True)

		self.verify_needs_updating()

		#set username
		"""best_record = best_record[0]
		self.cache_username = best_record.username
		if best_record.username is None or best_record.username == '-':
			user_record = GDUser.objects.filter(online_id=self.cache_user_id)[:1]
			if len(user_record) > 0:
				self.cache_username = user_record[0].cache_username
				print("Setting username from user record")
			else:
				print(":(((( Unable to set username")"""

		#needs updating field

		self.save()

	def get_serialized_base(self):
		if isinstance(self.cache_submitted, str): submitted_date = timezone.datetime.fromisoformat(self.cache_submitted)
		else: submitted_date = self.cache_submitted

		response = {
			'online_id': int(self.online_id),
			'comment': self.comment,
			'is_deleted': bool(self.is_deleted),
			'cache_level_name': self.cache_level_name,
			'cache_submitted': self.cache_submitted,
			'cache_submitted_timestamp': int(submitted_date.timestamp()),
			'cache_downloads': int(self.cache_downloads),
			'cache_likes': int(self.cache_likes),
			'cache_rating_sum': int(self.cache_rating_sum),
			'cache_rating': int(self.cache_rating),
			'cache_demon': bool(self.cache_demon),
			'cache_auto': bool(self.cache_auto),
			'cache_demon_type': int(self.cache_demon_type),
			'cache_stars': int(self.cache_stars),
			'cache_username': self.cache_username,
			'cache_level_string_available': bool(self.cache_level_string_available),
			'cache_user_id': int(self.cache_user_id),
			'cache_daily_id': int(self.cache_daily_id),
			'cache_needs_updating': bool(self.cache_needs_updating),
			'cache_available_versions': int(self.cache_available_versions),
			'cache_search_available': bool(self.cache_search_available),
			'cache_main_difficulty': int(self.cache_main_difficulty),
			'cache_max_stars': int(self.cache_max_stars),
			'cache_filter_difficulty': int(self.cache_filter_difficulty),
			'cache_length': int(self.cache_length),
			'cache_featured': int(self.cache_featured),
			'cache_max_featured': int(self.cache_max_featured),
			'cache_epic': int(self.cache_epic),
			'cache_max_epic': int(self.cache_max_epic),
			'cache_two_player': bool(self.cache_two_player),
			'cache_max_two_player': bool(self.cache_max_two_player),
			'cache_original': int(self.cache_original),
			'cache_max_original': int(self.cache_max_original),
			'cache_needs_revalidation': bool(self.cache_needs_revalidation),
		}
		return response

	def get_serialized_base_json(self):
		level_dict = self.get_serialized_base()
		level_dict['cache_submitted'] = str(level_dict['cache_submitted'])
		return level_dict

	def save(self, *args, **kwargs):
		self.cache_needs_search_update = True

		super(Level, self).save(*args, **kwargs)

class LevelDateEstimation(models.Model):
	level = models.ForeignKey(
		Level,
		on_delete=models.CASCADE,
		db_index=True,
	)

	server_response = models.ForeignKey(
		ServerResponse,
		on_delete=models.CASCADE,
		blank=True, null=True,
		db_index=True,
	)

	submitted = models.DateTimeField(default=timezone.now, db_index=True)

	created = models.DateTimeField(db_index=True)
	relative_upload_date = models.CharField(blank=True, null=True, max_length=255)

	is_offset = models.BooleanField(default=False)

	estimation = models.DateTimeField(blank=True, null=True, db_index=True)
	cache_online_id = models.IntegerField(blank=True, null=True, db_index=True) #I regret the database design decision that led to this

	def calculate(self):
		if self.relative_upload_date is not None and "year" in self.relative_upload_date:
			years = int(self.relative_upload_date.split(' ')[0])
			self.estimation = self.created - timedelta(days=365*years)
			#self.estimation = self.created.replace(year=self.created.year - years)
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

	def save(self, *args, **kwargs):
		self.cache_online_id = self.level.online_id

		super(LevelDateEstimation, self).save(*args, **kwargs)

class LevelString(models.Model):
	sha256 = models.CharField(max_length=64, db_index=True)
	requires_base64 = models.BooleanField(default=False)

	decompressed_sha256 = models.CharField(max_length=64, db_index=True, blank=True, null=True)
	file_size = models.IntegerField(blank=True, null=True, db_index=True)
	decompressed_file_size = models.IntegerField(blank=True, null=True, db_index=True)

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

		if self.requires_base64:
			content = base64.b64encode(content, altchars=b'-_')

		content = content.decode('windows-1252')
		return content

	def calculate_decompressed_string(self):
		import base64, zlib
		content = self.load_file_content()

		if content.startswith('kS'):
			return content.encode('windows-1252')
		
		try:
			if content.startswith('H4sIA'):
				content = base64.urlsafe_b64decode(content)
				return zlib.decompress(content, wbits = zlib.MAX_WBITS | 16)
			
			if content.startswith('eJ'):
				content = base64.urlsafe_b64decode(content)
				return zlib.decompress(content, wbits = zlib.MAX_WBITS)
		except:
			print("error while decompressing")

		return None

	def calculate_decompressed_sha256(self):
		import hashlib
		content = self.calculate_decompressed_string()
		if content is None: return None
		return hashlib.sha256(content).hexdigest()

	def get_decompressed_sha256(self):
		if not self.decompressed_sha256:
			self.decompressed_sha256 = self.calculate_decompressed_sha256()
			if self.decompressed_sha256: self.save()
		
		return self.decompressed_sha256

	def calculate_file_size(self):
		self.file_size = len(self.load_file_content())
		if self.calculate_decompressed_string():
			self.decompressed_file_size = len(self.calculate_decompressed_string())
		self.save()
		return self.file_size

	def get_file_size(self):
		if not self.file_size:
			return self.calculate_file_size()

		return self.file_size


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

	manual_submission = models.ForeignKey(
		ManualSubmission,
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
	cache_is_dupe = models.BooleanField(default=False, db_index=True)

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
	two_player = models.IntegerField(blank=True, null=True) #k43
	objects_count = models.IntegerField(blank=True, null=True) #k48
	account_id = models.IntegerField(blank=True, null=True) #k60
	coins = models.IntegerField(blank=True, null=True) #k64
	coins_verified = models.BooleanField(blank=True, null=True) #k65
	requested_stars = models.IntegerField(blank=True, null=True) #k66
	extra_string = models.TextField(blank=True, null=True) #k67 #also known as the capacity string
	daily_id = models.IntegerField(blank=True, null=True, db_index=True) #k74
	epic = models.IntegerField(blank=True, null=True) #k75
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

	def get_encoded_description(self, double_base64 = False):
		description = self.description if self.description_encoded is True else utils.encode_base64_text(self.description)
		if double_base64: description = utils.encode_base64_text(description)
		return description

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
		del response['manual_submission_id']
		del response['submitted']
		del response['song_id']
		del response['level_string_id']

		response['level_string_available'] = self.level_string is not None

		return response

	def get_serialized_full(self):
		response = self.get_serialized_base()
		response['real_user_record'] = None if self.real_user_record is None else self.real_user_record.get_serialized_base()
		response['song'] = None if self.song is None else self.song.get_serialized_base()
		return response

	class Meta:
		indexes = [
			models.Index(fields=['level', 'cache_is_dupe'], name='level_dupe')
		]