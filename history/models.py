import bisect
from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive, timedelta
from django.core.cache import cache

from django.db.models import Min, Max, Q
from django.db.models.functions import Coalesce

from . import utils
from .constants import MiscConstants

from datetime import datetime
import os, math

class LevelRecordType(models.TextChoices):
		GLM_02 = 'glm_02', _('GLM_02')
		GLM_03 = 'glm_03', _('GLM_03')
		GLM_10 = 'glm_10', _('GLM_10')
		GLM_16 = 'glm_16', _('GLM_16')
		LLM_01 = 'llm_01', _('LLM_01')
		DOWNLOAD = 'download', _('downloadGJLevel')
		GET = 'get', _('getGJLevels')
		MANUAL = 'manual', _('manual')
  
class CommentEstimationType(models.IntegerChoices):
    LEVEL = 0
    ACCOUNT = 1
    FRIEND_REQUEST = 2
    MESSAGE = 3

class HistoryUser(models.Model):
	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		db_index=True,
	)
	def __str__(self):
		return self.user.username
	
	@staticmethod
	def get_user(user):
		try:
			return HistoryUser.objects.get(user=user)
		except HistoryUser.DoesNotExist:
			user = HistoryUser.objects.create(user=user)
			user.save()
			return user


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
	queued_deletion = models.BooleanField(default=False, db_index=True)
	is_browsable = models.BooleanField(default=False)

	cache_level_count = models.IntegerField(blank=True, null=True)
	cache_full_level_count = models.IntegerField(blank=True, null=True)
	cache_children_count = models.IntegerField(blank=True, null=True)

	def get_serialized_base(self):
		response = {
			'created': str(self.created),
			'comment': self.comment,
		}
		if self.parent is not None: response['parent'] = self.parent.get_serialized_base()
		return response

	def get_level_count(self):
		if self.cache_level_count is not None:
			return self.cache_level_count
		#TODO: optimize
		self.cache_level_count = self.levelrecord_set.count()
		self.save()
		print(f"level count: {self.cache_level_count}")
		return self.cache_level_count

	def get_full_level_count(self):
		if self.cache_full_level_count is not None:
			return self.cache_full_level_count

		count = self.get_level_count()
		for submission in self.manualsubmission_set.all():
			count += submission.get_full_level_count()
		#TODO: optimize
		print(self)
		print(count)
		self.cache_full_level_count = count
		self.save()
		return count

	def get_children_count(self):
		if self.cache_children_count is not None:
			return self.cache_children_count
		#TODO: optimize
		self.cache_children_count = self.manualsubmission_set.count()
		self.save()
		return self.cache_children_count


class SaveFile(models.Model):
	author = models.ForeignKey(
		HistoryUser,
		on_delete=models.CASCADE,
		db_index=True,
	)
	submitted = models.DateTimeField(default=timezone.now)
	created = models.DateTimeField(default=timezone.now, db_index=True)
	comment = models.CharField(max_length=255, blank=True, null=True)
	is_processed = models.BooleanField(default=False)
	is_browsable = models.BooleanField(default=False)

	player_name = models.TextField(blank=True, null=True)
	player_user_id = models.IntegerField(blank=True, null=True)
	player_account_id = models.IntegerField(blank=True, null=True)
	binary_version = models.IntegerField(blank=True, null=True)
	#also raw save file with password stripped out stored on the side in a file

	cache_levels_count = models.IntegerField(blank=True, null=True)
	cache_nonblank_count = models.IntegerField(blank=True, null=True)

	def get_count(self):
		if self.cache_levels_count: return self.cache_levels_count
		count = self.levelrecord_set.count()
		if self.is_processed:
			self.cache_levels_count = count
			self.save()
		return count

	def get_nonblank_count(self):
		if self.cache_nonblank_count: return self.cache_nonblank_count
		count = self.levelrecord_set.exclude(level_version=None, game_version=None, level_name=None, downloads=None).count()
		if self.is_processed:
			self.cache_nonblank_count = count
			self.save()
		return count
	
	def get_serialized_base(self):
		return {
			'id': self.pk,
			'author': self.author.user.username,
			'submitted': str(self.submitted),
			'created': str(self.created),
			'comment': self.comment,
			'is_processed': self.is_processed,
			'player_name': self.player_name,
			'player_user_id': self.player_user_id,
			'player_account_id': self.player_account_id,
			'binary_version': self.binary_version,
			'nonblank_count': self.get_nonblank_count(),
			'count': self.get_count()
		}

class ServerResponse(models.Model):

	created = models.DateTimeField(default=timezone.now, db_index=True)
	unprocessed_post_parameters = models.JSONField()
	endpoint = models.CharField(max_length=32)

	comment = models.CharField(max_length=255, blank=True, null=True)

	get_type = models.IntegerField(blank=True, null=True, db_index=True)
	get_page = models.IntegerField(blank=True, null=True, db_index=True)

	def get_serialized_base(self):
		return {
			'created': str(self.created),
			'endpoint': self.endpoint,
			'comment': self.comment,
			'get_type': self.get_type,
			'get_page': self.get_page
		}

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

	forced_record = models.ForeignKey(
		"GDUserRecord",
		on_delete=models.SET_NULL,
		blank=True, null=True,
	)

	def revalidate_cache(self):
		if self.forced_record is not None:
			self.cache_username = self.forced_record.username
			self.cache_account_id = self.forced_record.account_id
			self.cache_username_created = self.forced_record.cache_created

			self.cache_non_player_username = self.forced_record.username
			self.cache_non_player_username_created = self.forced_record.cache_created

			self.save()
			return

		username_record_set = self.gduserrecord_set.exclude( Q(username='-') | Q(username=None) | Q(username='Unknown') | Q(username='TeamHax') ).order_by('-cache_last_seen')
		username_record = username_record_set[:1]
		if len(username_record) > 0:
			self.cache_username = username_record[0].username
			self.cache_username_created = username_record[0].cache_created
			self.cache_account_id = username_record[0].account_id
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

	def get_serialized_base(self):
		response = {
			'user_id': self.online_id,
			'username': self.cache_username,
			'non_player_username': self.cache_non_player_username,
			'account_id': self.cache_account_id
		}
		return response

	@staticmethod
	def user_for_account_id(account_id):
		if account_id == None or account_id == 0: return None
		
		users = GDUser.objects.filter(cache_account_id=account_id)[:2]
		if len(users) != 1:
			return None
		return users[0]

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

	account_id = models.IntegerField(blank=True, null=True) #k60
	username = models.CharField(blank=True, null=True, max_length=255, db_collation='utf8mb4_bin', db_index=True) #k5 #in the real world <= 15

	cache_created = models.DateTimeField(blank = True, null=True, db_index=True)
	cache_last_seen = models.DateTimeField(blank = True, null=True, db_index=True)

	def get_serialized_base(self):
		response = {
			'user_id': self.user.online_id,
			'username': self.username,
			'account_id': self.account_id
		}
		return response

	def get_serialized_full(self):
		response = self.get_serialized_base()
		response['cache_created'] = self.cache_created
		response['cache_last_seen'] = self.cache_last_seen
		return response
	
	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['user_id', 'username', 'account_id'], name='hello')
		]

class GDUserGroup(models.Model):
	comment = models.CharField(max_length=255)
	users = models.ManyToManyField(GDUser)

class Song(models.Model):
	online_id = models.IntegerField(unique=True, db_index=True)

	cache_song_name = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_artist_id = models.IntegerField(default=0, db_index=True)
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
	
	def fix_null_dates(self):
		records = self.songrecord_set.filter(cache_real_date=None)
		for record in records:
			record.cache_real_date = record.calculate_real_date()
			record.save()

	def revalidate_cache(self):
		self.cache_needs_revalidation = False

		self.fix_null_dates()
		
		best_record = self.songrecord_set.exclude(song_name=None).order_by('-cache_real_date')[:1]
		if len(best_record) < 1:
			self.cache_song_name = None
			self.cache_artist_id = 0
			self.cache_artist_name = None
			self.save()
			return

		best_record = best_record[0]
		self.cache_song_name = best_record.song_name or self.cache_song_name
		self.cache_artist_name = best_record.artist_name or self.cache_artist_name
		self.cache_artist_id = best_record.artist_id or self.cache_artist_id
		self.cache_submitted = best_record.get_real_date() or self.cache_submitted

		self.save()

	def get_serialized_base(self):
		record = {
			'online_id': self.online_id,
			'song_name': self.cache_song_name,
			'artist_name': self.cache_artist_name,
			'artist_id': self.cache_artist_id,
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

	song_name = models.CharField(blank=True, null=True, max_length=255)
	artist_id = models.IntegerField(null=True)
	artist_name = models.CharField(blank=True, null=True, max_length=255)
	size = models.FloatField(null=True)
	youtube_id = models.TextField(blank=True, null=True)
	youtube_channel = models.TextField(blank=True, null=True)
	is_verified = models.BooleanField(null=True)
	link = models.TextField(blank=True, null=True)
	cache_real_date = models.DateTimeField(blank=True, null=True, db_index=True)

	unprocessed_data = models.JSONField() #this field should only be used for archival purposes, do not pull data from this directly in production

	def calculate_real_date(self):
		date = None

		if self.server_response.count() > 0: date = self.server_response.order_by('created')[:1][0].created
		if self.save_file.count() > 0: 
			date_2 = self.save_file.order_by('created')[:1][0].created
			if date is None or date_2 > date: date = date_2

		return date

	def get_real_date(self):
		if self.cache_real_date is not None: return self.cache_real_date

		self.cache_real_date = self.calculate_real_date()
		self.save()
		return self.cache_real_date
	
	class Meta:
		indexes = [
			models.Index(
				fields=['artist_id', 'song', 'record_type'], 
				name='idx_artist_song_type'
			),
		]

class Level(models.Model):
	online_id = models.IntegerField(db_index=True, unique=True)
	comment = models.TextField(blank=True, null=True)
	is_public = models.BooleanField(default=False, db_index=True) #this is to prevent leaking unlisted levels publicly
	is_deleted = models.BooleanField(default=False, db_index=True)
	deleted_date = models.DateTimeField(blank=True, null=True)
	hide_from_search = models.BooleanField(db_index=True, default=False)
	cache_is_blank = models.BooleanField(db_index=True, blank=True, null=True)

	cache_level_name = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_submitted = models.DateTimeField(blank=True, null=True, db_index=True)
	cache_downloads = models.IntegerField(db_index=True, default=0)
	cache_likes = models.IntegerField(db_index=True, default=0)
	#cache_rating_sum = models.IntegerField(db_index=True, default=0)
	#cache_rating = models.IntegerField(db_index=True, default=0)
	#cache_demon = models.BooleanField(db_index=True, default=False)
	#cache_auto = models.BooleanField(db_index=True, default=False)
	#cache_demon_type = models.IntegerField(blank=True, null=True, db_index=True)
	cache_stars = models.IntegerField(db_index=True, default=0)
	cache_username = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_level_string_available = models.BooleanField(default=False, db_index=True)
	cache_user_id = models.IntegerField(blank=True, null=True, db_index=True)
	cache_account_id = models.IntegerField(blank=True, null=True, db_index=True)

	cache_daily_id = models.IntegerField(default=0, db_index=True)
	is_test_daily = models.BooleanField(blank=True, null=True)
	cache_daily_date = models.DateTimeField(blank=True, null=True)

	cache_needs_updating = models.BooleanField(default=True, db_index=True)
	cache_needs_updating2 = models.BooleanField(default=False)
	cache_available_versions = models.IntegerField(default=0, db_index=True)
	cache_search_available = models.BooleanField(default=False, db_index=True)
	#cache_main_difficulty = models.IntegerField(default=0, db_index=True)

	cache_min_stars = models.IntegerField(db_index=True, default=0)
	cache_max_stars = models.IntegerField(db_index=True, default=0)
	cache_rating_changed = models.BooleanField(default=False, db_index=True)
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
	cache_min_game_version = models.IntegerField(default=0, db_index=True)
	cache_max_game_version = models.IntegerField(default=0, db_index=True)
	cache_game_version = models.IntegerField(default=0, db_index=True)

	cache_audiotrack = models.IntegerField(default=0, db_index=True)
	cache_song_id = models.IntegerField(default=0, db_index=True)
	cache_song_artist_id = models.IntegerField(default=0, db_index=True)

	cache_needs_revalidation = models.BooleanField(db_index=True, default=False)
	cache_needs_search_update = models.BooleanField(db_index=True, default=False)
 
	cache_file_size = models.IntegerField(blank=True, null=True, db_index=True)
	cache_decompressed_file_size = models.IntegerField(blank=True, null=True, db_index=True)
	cache_object_count = models.IntegerField(blank=True, null=True, db_index=True)

	needs_priority_download = models.BooleanField(db_index=True, default=False)

	best_record = models.ForeignKey(
		"LevelRecord",
		on_delete=models.SET_NULL,
		blank=True, null=True,
		related_name='best_record_level',
	)
	first_record = models.ForeignKey(
		"LevelRecord",
		on_delete=models.SET_NULL,
		blank=True, null=True,
		related_name='first_record_level',
	)

	submitted = models.DateTimeField(default=timezone.now, db_index=True)
	class Meta:
		indexes = [
			models.Index(fields=['cache_user_id', 'online_id']), # for user_to_level_estimation

			models.Index(
                fields=['cache_needs_revalidation', 'cache_needs_search_update', 'cache_search_available'], 
                name='search_sync_idx'
            ),
		]
  
	def is_blank(self):
		return self.cache_level_name is None and self.cache_game_version == 0 and self.cache_downloads == 0

	def make_blank(self):
		self.cache_level_name = None
		self.cache_game_version = 0
		self.cache_downloads = 0
		self.cache_likes = 0
		self.cache_submitted = None
		self.cache_username = None
		self.cache_user_id = None
		self.cache_account_id = None
		self.cache_search_available = False
		self.cache_is_blank = True
		self.save()

	def set_public(self, public):
		self.is_public = public
		#self.save()

		#self.levelrecord_set.update(cache_is_public=True)
  
	def assign_level_string_cache(self, level_string):
		print("assigning level string cache")
		info = level_string.get_serialized_base()
		self.cache_file_size = info['file_size']
		self.cache_decompressed_file_size = info['decompressed_file_size']
		self.cache_object_count = info['object_count']
  
	def get_data_record(self):
		return self.levelrecord_set.filter(cache_is_dupe=False, is_invalid=False).exclude( Q(level_string=None) ).prefetch_related('level_string').order_by('-downloads')

	def verify_needs_updating(self):
		print("verifying needs updating")

		data_record = self.get_data_record()
		self.cache_needs_updating = False
		if len(data_record) > 0:
			best_record = self.levelrecord_set.filter(cache_is_dupe=False, is_invalid=False).exclude( Q(level_name=None) ).prefetch_related('level_string').order_by('-downloads')[:1][0]

			level_strings = {}
			for record in data_record:
				level_strings[record.level_string.get_decompressed_sha256()] = True
			self.cache_available_versions = len(level_strings)
			self.cache_level_string_available = True

			data_record = data_record[0]
			if best_record.description != data_record.description and not best_record.downloads == data_record.downloads: self.cache_needs_updating = True
			elif (best_record.official_song or 0) != (data_record.official_song or 0): self.cache_needs_updating = True
			elif (best_record.song_id != data_record.song_id) and not ((data_record.song_id is None and best_record.song_id == MiscConstants.SONG_ID_ZERO) or (best_record.song_id is None and data_record.song_id == MiscConstants.SONG_ID_ZERO)): self.cache_needs_updating = True
			elif (best_record.level_version or 0) != (data_record.level_version or 0): self.cache_needs_updating = True
			elif (best_record.game_version or 0) != (data_record.game_version or 0): self.cache_needs_updating = True
			elif (best_record.length or 0) != (data_record.length or 0): self.cache_needs_updating = True
			elif (best_record.two_player or 0) != (data_record.two_player or 0): self.cache_needs_updating = True
			elif (best_record.objects_count or 0) != (data_record.objects_count or 0): self.cache_needs_updating = True
			elif (best_record.coins or 0) != (data_record.coins or 0): self.cache_needs_updating = True
			elif (best_record.requested_stars or 0) != (data_record.requested_stars or 0): self.cache_needs_updating = True
			elif (best_record.original or 0) != (data_record.original or 0): self.cache_needs_updating = True
   
			self.assign_level_string_cache(data_record.level_string)
		else:
			self.cache_needs_updating = True
			self.cache_level_string_available = False
		
		if self.cache_needs_updating == True and (self.cache_stars > 0 or self.cache_user_id == 16) and not self.is_deleted:
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

	def update_with_record(self, record, force=False):
		print(f"updating with record ({record.downloads} downloads)")

		changed = False
		check_level_string = False
		record_date = record.get_real_date()

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
			print(f"Setting data to record with {record.downloads} downloads")
			changed = True
			self.cache_level_name = record.level_name
			self.cache_submitted = record_date
			self.cache_downloads = record.downloads or 0
			self.cache_likes = (record.likes or 0) - (record.dislikes or 0)
			self.cache_rating_sum = record.rating_sum or 0
			self.cache_rating = record.rating or 0
			self.cache_demon = record.demon or 0
			self.cache_auto = record.auto or 0
			self.cache_demon_type = record.demon_type or 0
			self.cache_game_version = record.game_version or 0
			self.cache_stars = record.stars or 0
			self.cache_user_id = record.user_id or self.cache_user_id
			self.cache_account_id = record.account_id or self.cache_account_id
			self.cache_blank_name = (self.cache_level_name is None)
			check_level_string = True

			self.cache_length = record.length or 0
			self.cache_featured = record.feature_score or 0
			self.cache_epic = record.epic or 0
			self.cache_two_player = record.two_player or 0
			self.cache_original = record.original or 0
			self.cache_audiotrack = record.official_song or 0
			if record.song is not None:
				if record.song.cache_artist_id == 0:
					print("updating song record")
					record.song.revalidate_cache()
				self.cache_song_id = record.song.online_id
				self.cache_song_artist_id = record.song.cache_artist_id
			else:
				self.cache_song_id = 0
				self.cache_song_artist_id = 0

			self.assign_difficulty_from_record(record)

			if record.real_user_record is not None and record.real_user_record.username is not None and record.real_user_record.username != '' and record.real_user_record.username != '-' and record.real_user_record.user_id != 0 and record.real_user_record.user_id is not None:
				self.cache_username = record.real_user_record.username
				self.cache_user_id = record.real_user_record.user.online_id
				self.cache_account_id = record.real_user_record.account_id
	
			if self.cache_user_id == None or self.cache_user_id == 0:
				user = GDUser.user_for_account_id(record.account_id)
				if user:
					self.cache_user_id = user.online_id
					self.cache_account_id = user.cache_account_id
					print(f"Assigning detected user ID ({user.online_id})")

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
			self.update_search_available()
		
		self.cache_is_blank = self.is_blank()
		if changed and not force:
			self.save()

	def update_search_available(self):
		self.cache_search_available = (self.is_public == True and self.hide_from_search == False and self.is_blank() == False)

	def assign_difficulty_from_record(self, record):
		rating = record.rating or 0
		self.cache_filter_difficulty = 0

		if record.auto:
			self.cache_filter_difficulty = 1
		elif record.demon:
			if record.demon_type is not None:
				if int(record.demon_type) < 3: #hard demon
					self.cache_filter_difficulty = 10
				elif int(record.demon_type) < 5: #easy medium
					self.cache_filter_difficulty = 8 - 3 + int(record.demon_type)
				else:
					self.cache_filter_difficulty = 11 - 5 + int(record.demon_type)
			else:
				self.cache_filter_difficulty = 10
		elif rating > 4:
			# prior to 1.5 difficulties were rounded incorrectly
			main_difficulty = int(record.rating_sum or -1) / int(record.rating)
			if (record.game_version or 0) >= 6:
				self.cache_filter_difficulty = round(main_difficulty + 1)
			else:
				self.cache_filter_difficulty = math.floor(main_difficulty + 1)

	def recalculate_maximums(self):
		#print("ensuring first record id is set")
		#self.get_first_record_id()
	 
		print("recalculating maximums")
		base_set = self.levelrecord_set.filter(cache_is_dupe=False, is_invalid=False)
		maximums = base_set.aggregate(Max('stars'), Max('feature_score'), Max('epic'), Max('two_player'), Max('original'), Max('daily_id'), Max('game_version'), Min('game_version'))
		self.cache_max_stars = maximums['stars__max'] or 0
		#self.cache_max_filter_difficulty = models.IntegerField(default=0, db_index=True)
		self.cache_max_featured = maximums['feature_score__max'] or 0
		self.cache_max_epic = maximums['epic__max'] or 0
		self.cache_max_two_player = maximums['two_player__max'] or 0
		self.cache_max_original = maximums['original__max'] or 0
		self.cache_daily_id = maximums['daily_id__max'] or 0
		self.cache_min_game_version = maximums['game_version__min'] or 0
		self.cache_max_game_version = maximums['game_version__max'] or 0
		print("set maximums, not saved")

		if self.cache_max_stars > 0:
			print("recalculating minimums")
			minimums = base_set.filter(stars__gt=0).aggregate(Min('stars'))
			self.cache_min_stars = minimums['stars__min'] or 0
			print("set minimums, not saved")
		else:
			self.cache_min_stars = 0

		if self.cache_user_id is None or self.cache_user_id == 0:
			print("recalculating user id")
			user_id_set = base_set.aggregate(Max('user_id'))
			self.cache_user_id = user_id_set['user_id__max']
			print("set user id, not saved")
   
		if self.cache_account_id is None or self.cache_account_id == 0:
			print("recalculating account id")
			account_id_set = base_set.aggregate(Max('account_id'))
			self.cache_account_id = account_id_set['account_id__max']
			print("set account id, not saved")

		if self.cache_daily_id is not None and self.cache_daily_date is None:
			print("setting daily date")
			best_daily_record = base_set.filter(daily_id=self.cache_daily_id, record_type=LevelRecordType.DOWNLOAD).order_by('downloads')[:1]
			if len(best_daily_record) > 0:
				self.cache_daily_date = best_daily_record[0].get_real_date()
				print("set daily date, not saved")

		self.cache_rating_changed = (self.cache_stars != self.cache_max_stars) or (self.cache_min_stars != self.cache_stars) or (self.cache_min_stars != self.cache_max_stars)

	def dedup_records(self):
		"""This ensures there is only one record of each level version with cache_is_dupe set to False. The record with the highest amount of downloads is also kept."""
		#print("deduplicating records")

		record_strings = set()
		records_to_update = set()
		highest_downloads = 0
		highest_downloads_record = None
		highest_downloads_with_levelstring = 0
		highest_downloads_with_levelstring_record = None

		for record in self.levelrecord_set.filter(cache_is_dupe=False).order_by('downloads'):
			record.upgrade_data()
			#name, rating_sum, ratings, demon, auto, stars, version, real_user_record, game_version, levelstring
			current_record_string = f"{record.level_name or 0}, {record.rating or 0}, {record.rating_sum or 0}, {record.auto or 0}, {record.demon or 0}, {record.stars or 0}, {record.demon_type or 0}, {record.level_version or 0}, {record.username or 0}, {record.user_id or 0}, {record.account_id or 0}, {record.game_version or 0}, {record.level_string_id or 0}, {record.coins or 0}, {record.description or 0}, {record.song_id or 0}, {record.official_song or 0}, {record.feature_score or 0}, {record.epic or 0}, {record.password or 0}, {record.two_player or 0}, {record.objects_count or 0}, {record.extra_string or 0}, {record.original or 0}, {record.daily_id or 0}, {record.timestamp or 0}, {record.song_ids}, {record.sfx_ids}"
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


			#print(f"{record} - {current_record_string} - {record.cache_is_dupe}")

		#print("deduplicating records - updating db")
		if highest_downloads_record in records_to_update: records_to_update.remove(highest_downloads_record)
		if highest_downloads_with_levelstring_record in records_to_update: records_to_update.remove(highest_downloads_with_levelstring_record)
		self.levelrecord_set.bulk_update(records_to_update, ['cache_is_dupe'], batch_size=1000)
		print("deduplicating records done")

	def revalidate_cache(self):
		self.cache_needs_revalidation = False
		self.dedup_records()

		self.recalculate_maximums()

		best_record = self.levelrecord_set.filter(cache_is_dupe=False, is_invalid=False).exclude( Q(level_name=None) ).order_by('-downloads')

		best_record_download = best_record.filter(Q(record_type=LevelRecordType.DOWNLOAD) | Q(record_type=LevelRecordType.GET))[:1]
		if len(best_record_download) > 0: best_record = best_record_download
		else: best_record = best_record[:1]

		if len(best_record) < 1:
			self.make_blank()
			return

		best_record = best_record[0]
		self.best_record = best_record

		self.update_with_record(best_record, True)

		self.verify_needs_updating()
		self.update_is_public()

		self.save()

	def update_is_public(self):
		if self.is_public:
			return
		# records = LevelRecord.objects.filter( Q(level__cache_user_id__in=user_whitelist) 
		# | Q(level__cache_stars__gt=0) | Q(level__cache_downloads__gte=1000) | Q(level__online_id__lt=MiscConstants.FIRST_2_1_LEVEL) 
		# | Q(record_type=LevelRecordType.GET) 
		# | ( Q(record_type=LevelRecordType.DOWNLOAD) & Q(server_response__created__gte="2021-11-24 02:10:00+00:00") & Q(server_response__created__lte="2023-12-20 01:27:21+00:00") ) )
		if self.cache_stars > 0 or self.cache_downloads >= 1000 or self.online_id < MiscConstants.FIRST_2_1_LEVEL:
			self.change_is_public(True)
			return

		if self.levelrecord_set.filter(record_type=LevelRecordType.GET).exists():
			self.change_is_public(True)
			return
		
		if self.levelrecord_set.filter(record_type=LevelRecordType.DOWNLOAD, server_response__created__gte="2021-11-24 02:10:00+00:00", server_response__created__lte="2023-12-20 01:27:21+00:00").exists():
			self.change_is_public(True)
			return

	def change_is_public(self, is_public):
		old_is_public = self.is_public
		self.is_public = is_public
		if old_is_public != self.is_public:
			self.update_search_available()
			self.levelrecord_set.update(cache_is_public=is_public)


	def get_serialized_base(self):
		if isinstance(self.cache_submitted, str): submitted_date = timezone.datetime.fromisoformat(self.cache_submitted)
		else: submitted_date = self.cache_submitted

		response = {
			'online_id': int(self.online_id),
			'comment': self.comment,
			'is_public': bool(self.is_public),
			'is_deleted': bool(self.is_deleted),
			'cache_level_name': self.cache_level_name,
			'cache_submitted': self.cache_submitted,
			'cache_submitted_timestamp': int(submitted_date.timestamp()) if submitted_date else None,
			'cache_downloads': int(self.cache_downloads),
			'cache_likes': int(self.cache_likes),
			#'cache_rating_sum': int(self.cache_rating_sum),
			#'cache_rating': int(self.cache_rating),
			#'cache_demon': bool(self.cache_demon),
			#'cache_auto': bool(self.cache_auto),
			#'cache_demon_type': int(self.cache_demon_type) if self.cache_demon_type else None,
			'cache_stars': int(self.cache_stars),
			'cache_username': self.cache_username,
			'cache_level_string_available': bool(self.cache_level_string_available),
			'cache_user_id': int(self.cache_user_id) if self.cache_user_id else 0,
			'cache_account_id': int(self.cache_account_id) if self.cache_account_id else 0,
			'cache_daily_id': int(self.cache_daily_id),
			'is_test_daily': bool(self.is_test_daily),
			'cache_daily_date': self.cache_daily_date,
			'cache_needs_updating': bool(self.cache_needs_updating) or bool(self.cache_needs_updating2),
			'cache_available_versions': int(self.cache_available_versions),
			'cache_search_available': bool(self.cache_search_available),
			#'cache_main_difficulty': int(self.cache_main_difficulty),
			'cache_min_stars': int(self.cache_min_stars),
			'cache_max_stars': int(self.cache_max_stars),
			'cache_rating_changed': bool(self.cache_rating_changed),
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
			'cache_min_game_version': int(self.cache_min_game_version),
			'cache_max_game_version': int(self.cache_max_game_version),
			'cache_game_version': int(self.cache_game_version),
			'cache_audiotrack': int(self.cache_audiotrack),
			'cache_song_id': int(self.cache_song_id),
			'cache_song_artist_id': int(self.cache_song_artist_id),
			'cache_needs_revalidation': bool(self.cache_needs_revalidation),
			'cache_file_size': int(self.cache_file_size) if self.cache_file_size is not None else None,
			'cache_decompressed_file_size': int(self.cache_decompressed_file_size) if self.cache_decompressed_file_size is not None else None,
			'cache_object_count': int(self.cache_object_count) if self.cache_object_count is not None else None,
		}
		return response

	def get_serialized_base_json(self):
		level_dict = self.get_serialized_base()
		level_dict['cache_submitted'] = str(level_dict['cache_submitted'])
		level_dict['cache_daily_date'] = str(level_dict['cache_daily_date'])
		return level_dict
	
	def get_best_record(self):
		if self.best_record is not None: return self.best_record
		
		all_levels = self.levelrecord_set.filter(is_invalid=False).order_by('-downloads')[:1]
		if len(all_levels) < 1:
			return None
		self.best_record = all_levels[0]
		self.save()
		return self.best_record
	
	def get_first_record(self):
		if self.first_record is not None: return self.first_record
  
		# more optimized route that is less reliable
		all_levels = self.levelrecord_set.order_by('id')[:10]
		for level in all_levels:
			if level.level_version is not None and level.game_version is not None and level.level_name is not None and level.downloads is not None:
				self.first_record = level
				self.save()
				return self.first_record
		
		# reliable fallback that can take minutes
		all_levels = self.levelrecord_set.exclude(level_version=None, game_version=None, level_name=None, downloads=None).order_by('id')[:1]
		if len(all_levels) < 1:
			return None
		self.first_record = all_levels[0]
		self.save()
		return self.first_record
	
	def get_first_record_id(self):
		if self.first_record_id is not None: return self.first_record_id
		record = self.get_first_record()
		return record.pk if record else None

	def save(self, *args, **kwargs):
		if "update_fields" in kwargs and kwargs["update_fields"] is not None:
			kwargs["update_fields"].append("cache_needs_search_update")

		self.cache_needs_search_update = True

		super(Level, self).save(*args, **kwargs)
  
class CommentDateEstimation(models.Model):
	range_id = models.IntegerField()
	level_id = models.IntegerField(db_index=True) # only for correction if range_id gets set wrong incorrectly
	comment_id = models.IntegerField(db_index=True)

	type = models.IntegerField(choices=CommentEstimationType.choices, default=CommentEstimationType.LEVEL)

	submitted = models.DateTimeField(default=timezone.now, db_index=True)

	created = models.DateTimeField(db_index=True)
	relative_upload_date = models.CharField(blank=True, null=True, max_length=255)
 
	estimation = models.DateTimeField(blank=True, null=True, db_index=True)

	def calculate(self):
		if not self.relative_upload_date: return
  
		if "second" in self.relative_upload_date:
			seconds = int(self.relative_upload_date.split(' ')[0])
			self.estimation = self.created - timedelta(seconds=seconds)
		elif "minute" in self.relative_upload_date:
			minutes = int(self.relative_upload_date.split(' ')[0])
			self.estimation = self.created - timedelta(minutes=minutes)
		elif "hour" in self.relative_upload_date:
			hours = int(self.relative_upload_date.split(' ')[0])
			self.estimation = self.created - timedelta(hours=hours)
		elif "day" in self.relative_upload_date:
			days = int(self.relative_upload_date.split(' ')[0])
			self.estimation = self.created - timedelta(days=days)
		elif "week" in self.relative_upload_date:
			weeks = int(self.relative_upload_date.split(' ')[0])
			self.estimation = self.created - timedelta(days=7*weeks)
		elif "month" in self.relative_upload_date:
			months = int(self.relative_upload_date.split(' ')[0])
			self.estimation = self.created - timedelta(days=30*months)
		elif "year" in self.relative_upload_date:
			years = int(self.relative_upload_date.split(' ')[0])
			self.estimation = self.created - timedelta(days=365*years)
		else:
			return

		if self.type == CommentEstimationType.LEVEL:
			self.range_id = utils.comment_range_for_level(self.level_id)
		elif self.type == CommentEstimationType.ACCOUNT:
			self.range_id = utils.comment_range_for_account(int(self.level_id))
		else:
			self.range_id = 0

		self.save()

	def get_serialized_base(self):
		response = {
			'created': self.created,
			'relative_upload_date': self.relative_upload_date,
			'estimation': self.estimation,
			'online_id': self.comment_id,
			'level_id': self.level_id
		}
		return response

	class Meta:
		indexes = [
			models.Index(fields=['range_id', 'type', '-estimation', 'comment_id'], name='type_range_est_desc_idx'),
			models.Index(fields=['range_id', 'type', 'estimation', 'comment_id'], name='type_range_est_comment_idx'),

			#models.Index(fields=['range_id', 'type', '-comment_id'], name='type_range_comment_desc_idx'),
			models.Index(fields=['range_id', 'type', 'comment_id'], name='type_range_comment_asc_idx'),
		]

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
		if not self.cache_online_id: self.save()

		response = {
			'created': self.created,
			'relative_upload_date': self.relative_upload_date,
			'estimation': self.estimation,
			'online_id': self.cache_online_id
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
	object_count = models.IntegerField(blank=True, null=True, db_index=True)

	def get_serialized_base(self):
		return {
			'sha256': self.sha256,
			'decompressed_sha256': self.get_decompressed_sha256(),
			'file_size': self.get_file_size(),
			'decompressed_file_size': self.decompressed_file_size,
			'object_count': self.get_object_count(),
		}

	def get_file_path(self):
		data_path = utils.get_data_path()
		directory = f"{data_path}/LevelString/{self.sha256[:2]}"
		if not os.path.exists(directory):
			os.mkdir(directory)
		return f"{directory}/{self.sha256}"

	def write_string(self, level_string):
		import base64

		self.requires_base64 = False
		if level_string[:2] == b'eJ' or level_string[:2] == b'H4':
			try:
				level_string = base64.b64decode(level_string, altchars='-_')
				self.requires_base64 = True
			except:
				#unable to decode, store levelstring as is
				print("unable to decode levelstring")

		f = open(self.get_file_path(), "wb")
		f.write(level_string)
		f.close()
		self.calculate_file_size()

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

		if content is None: return None

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
		content = self.load_file_content()
		if content is None: return None

		self.file_size = len(content)
		if self.calculate_decompressed_string():
			self.decompressed_file_size = len(self.calculate_decompressed_string())
		self.save()
		return self.file_size

	def get_file_size(self):
		if not self.file_size:
			return self.calculate_file_size()

		return self.file_size

	def calculate_object_count(self):
		content = self.calculate_decompressed_string()
		if content is None: return None

		self.object_count = content.count(b';')
		if len(content) > 0 and content[-1] == 59: self.object_count -= 1
		self.save()
		return self.object_count

	def get_object_count(self):
		if not self.object_count:
			return self.calculate_object_count()
		return self.object_count


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
	is_invalid = models.BooleanField(default=False, db_index=True)

	cache_is_public = models.BooleanField(default=False, db_index=True)
	cache_is_dupe = models.BooleanField(default=False, db_index=True)
	cache_real_date = models.DateTimeField(blank=True, null=True, db_index=True)

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
	timestamp = models.IntegerField(blank=True, null=True) #57
	song_ids = models.TextField(blank=True, null=True) #52 #k104
	sfx_ids = models.TextField(blank=True, null=True) #53 #k105
	level_size = models.IntegerField(blank=True, null=True) #k39
	editor_tainted = models.BooleanField(blank=True, null=True, db_index=True) #k15 + k21 combined

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

		record_date = self.get_real_date()
		
		user_object = utils.get_user_object(self.user_id)
		user_record = utils.create_user_record(user_object, self.account_id, self.username, record_date)
		if user_object is not None: user_object.update_with_record(user_record)

		self.real_user_record = user_record
		self.save()

	def get_serialized_base(self):
		self.upgrade_data()
		response = self.__dict__.copy()

		if '_prefetched_objects_cache' in response: del response['_prefetched_objects_cache']
		if '_state' in response: del response['_state']
		del response['unprocessed_data']
		#del response['username']
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
		response['level_string_info'] = self.level_string.get_serialized_base() if self.level_string is not None else None

		return response

	def get_serialized_full(self):
		response = self.get_serialized_base()
		response['real_user_record'] = None if self.real_user_record is None else self.real_user_record.get_serialized_base()
		response['cached_user_info'] = None if self.real_user_record is None else self.real_user_record.user.get_serialized_base()
		response['song'] = None if self.song is None else self.song.get_serialized_base()
		response['response_get_type'] = self.server_response.get_type if self.server_response is not None else None
		response['response_comment'] = self.server_response.comment if self.server_response is not None else None
		response['manual_submission_id'] = self.manual_submission.pk if self.manual_submission is not None else None
		response['real_date'] = self.get_real_date()
  
		if self.account_id is not None and self.real_user_record is None:
			user = GDUser.user_for_account_id(self.account_id)
			if user:
				response['accountid_user'] = user.get_serialized_base()
  
		return response
	
	def get_serialized_sources(self):
		return {
			'save_files': [save_file.get_serialized_base() for save_file in self.save_file.all()],
			'server_responses': [self.server_response.get_serialized_base()] if self.server_response else [],
			'manual_submissions': [self.manual_submission.get_serialized_base()] if self.manual_submission else [],
		}

	def upgrade_data(self):
		changed = False

		#2.200 additions
		if '57' in self.unprocessed_data and self.unprocessed_data['57'] != "":
			self.timestamp = int(self.unprocessed_data['57'])
			del self.unprocessed_data['57']
			changed = True
		elif '57' in self.unprocessed_data and self.unprocessed_data['57'] == "":
			del self.unprocessed_data['57']
			changed = True
		if '52' in self.unprocessed_data:
			self.song_ids = self.unprocessed_data['52']
			del self.unprocessed_data['52']
			changed = True
		if '53' in self.unprocessed_data:
			self.sfx_ids = self.unprocessed_data['53']
			del self.unprocessed_data['53']
			changed = True
		if 'k95' in self.unprocessed_data: 
			self.timestamp = int(self.unprocessed_data['k95'])
			del self.unprocessed_data['k95']
			changed = True
		if 'k104' in self.unprocessed_data: 
			self.song_ids = self.unprocessed_data['k104']
			del self.unprocessed_data['k104']
			changed = True
		if 'k105' in self.unprocessed_data: 
			self.sfx_ids = self.unprocessed_data['k105']
			del self.unprocessed_data['k105']
			changed = True

		#gdhistory changes
		if self.real_user_record_id is None and self.user_id is not None:
			self.create_user()
			changed = False #saved in create_user
   
		#1.7 1.8 level size
		if 'k39' in self.unprocessed_data:
			self.level_size = self.unprocessed_data['k39']
			del self.unprocessed_data['k39']
			changed = True

		#saving
		if changed:
			self.save()

	def calculate_real_date(self):
		if self.server_response: return self.server_response.created
		if self.manual_submission: return self.manual_submission.created
		if self.save_file.count() > 0: return self.save_file.order_by('created')[:1][0].created
		return None

	def get_real_date(self):
		if self.cache_real_date is not None: return self.cache_real_date

		self.cache_real_date = self.calculate_real_date()
		self.save()
		return self.cache_real_date

	def is_blank(self):
		return self.level_version is None and self.game_version is None and self.level_name is None and self.downloads is None

	class Meta:
		indexes = [
			models.Index(fields=['level', 'cache_is_dupe'], name='level_dupe'),
			models.Index(fields=['level', 'cache_is_dupe', 'is_invalid'], name='level_dupe_invalid')
		]

class LevelList(models.Model):
	online_id = models.IntegerField(db_index=True)

class LevelListRecord(models.Model):
	level_list = models.ForeignKey(
		LevelList,
		on_delete=models.CASCADE,
		db_index=True,
	)
	levels = models.ManyToManyField(
		Level,
	)
	server_response = models.ForeignKey(
		ServerResponse,
		on_delete=models.CASCADE,
		blank=True, null=True,
		db_index=True,
	)
	unprocessed_data = models.JSONField()

	def assign_levels(self, level_string):
		from .utils import get_level_object

		if self.pk is None:
			self.save()

		level_ids = level_string.split(',')
		for level_id in level_ids:
			self.levels.add(get_level_object(level_id))
		self.save()