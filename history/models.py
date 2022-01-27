from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _

from django.db.models import Min
from django.db.models.functions import Coalesce

from datetime import datetime

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
	submitted = models.DateTimeField(default=datetime.now)
	created = models.DateTimeField(default=datetime.now, db_index=True)
	comment = models.CharField(max_length=255)
	is_processed = models.BooleanField(default=False)

	player_name = models.TextField(blank=True, null=True)
	player_user_id = models.IntegerField(blank=True, null=True)
	player_account_id = models.IntegerField(blank=True, null=True)
	binary_version = models.IntegerField(blank=True, null=True)
	#also raw save file with password stripped out stored on the side in a file

class ServerResponse(models.Model):

	created = models.DateTimeField(default=datetime.now)
	unprocessed_post_parameters = models.JSONField()
	endpoint = models.CharField(max_length=32)

class Song(models.Model):
	online_id = models.IntegerField(unique=True)


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

	server_response = models.ForeignKey(
		ServerResponse,
		on_delete=models.CASCADE,
		blank=True, null=True,
		db_index=True,
	)

	song_name = models.TextField(blank=True, null=True)
	artist_id = models.IntegerField(null=True)
	artist_name = models.TextField(blank=True, null=True)
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

	cache_level_name = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_submitted = models.DateTimeField(blank=True, null=True, db_index=True)
	cache_downloads = models.IntegerField(blank=True, null=True, db_index=True)
	cache_likes = models.IntegerField(blank=True, null=True, db_index=True)
	cache_rating_sum = models.IntegerField(blank=True, null=True, db_index=True)
	cache_rating = models.IntegerField(blank=True, null=True, db_index=True)
	cache_demon_type = models.IntegerField(blank=True, null=True, db_index=True)
	cache_stars = models.IntegerField(blank=True, null=True, db_index=True)
	cache_username = models.CharField(blank=True, null=True, max_length=255, db_index=True)
	cache_level_string_available = models.BooleanField(blank=True, null=True, db_index=True)

	submitted = models.DateTimeField(default=datetime.now, db_index=True)

	def set_public(self, public):
		self.is_public = public
		self.save()

		self.levelrecord_set.update(cache_is_public=True)

	def revalidate_cache(self):
		best_record = self.levelrecord_set.annotate(oldest_created=Min('save_file__created'), real_date=Coalesce('oldest_created', 'server_response__created')).exclude(real_date=None).order_by('-downloads')[:1]
		if len(best_record) < 1:
			return

		best_record = best_record[0]
		self.cache_level_name = best_record.level_name
		self.cache_submitted = best_record.real_date
		self.cache_downloads = best_record.downloads
		self.cache_likes = best_record.likes
		self.cache_rating_sum = best_record.rating_sum
		self.cache_rating = best_record.rating
		self.cache_demon_type = best_record.demon_type
		self.cache_stars = best_record.stars
		
		level_string_count = self.levelrecord_set.exclude(level_string=None).count()
		self.cache_level_string_available = level_string_count > 0

		self.cache_username = best_record.username
		if best_record.username is None:
			best_record = self.levelrecord_set.exclude(username=None).order_by('-downloads')[:1]
			if len(best_record) < 1:
				self.cache_username = None
			else:
				self.cache_username = best_record[0].username

		self.save()

class LevelString(models.Model):
	sha256 = models.CharField(max_length=64, db_index=True)

class LevelRecord(models.Model):

	class RecordType(models.TextChoices):
		GLM_03 = 'glm_03', _('GLM_03')
		GLM_10 = 'glm_10', _('GLM_10')
		GLM_16 = 'glm_16', _('GLM_16')
		DOWNLOAD = 'download', _('downloadGJLevel')
		GET = 'get', _('getGJLevels')

	record_type = models.CharField(
		max_length=8,
		choices=RecordType.choices,
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

	submitted = models.DateTimeField(default=datetime.now, db_index=True)

	cache_is_public = models.BooleanField(blank=True, null=True, db_index=True)

	level_name = models.CharField(blank=True, null=True, max_length=255, db_index=True) #k2 #in the real world this can't be more than 20, unless you're dealing with private server save files
	description = models.TextField(blank=True, null=True) #k3
	username = models.CharField(blank=True, null=True, max_length=255, db_index=True) #k5 #in the real world <= 15
	user_id = models.IntegerField(blank=True, null=True) #k6
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
	custom_song = models.IntegerField(blank=True, null=True) #k41
	objects_count = models.IntegerField(blank=True, null=True) #k48
	account_id = models.IntegerField(blank=True, null=True) #k60
	coins = models.IntegerField(blank=True, null=True) #k64
	coins_verified = models.BooleanField(blank=True, null=True) #k65
	requested_stars = models.IntegerField(blank=True, null=True) #k66
	extra_string = models.TextField(blank=True, null=True) #k67 #also known as the capacity string
	daily_id = models.IntegerField(blank=True, null=True) #k74
	epic = models.BooleanField(blank=True, null=True) #k75
	demon_type = models.IntegerField(blank=True, null=True) #k76
	seconds_spent_editing = models.IntegerField(blank=True, null=True) #k80
	seconds_spent_editing_copies = models.IntegerField(blank=True, null=True) #k81
	relative_upload_date = models.CharField(blank=True, null=True, max_length=255) #28 #in the real world <= 10
	relative_update_date = models.CharField(blank=True, null=True, max_length=255) #29 #in the real world <= 10

	unprocessed_data = models.JSONField() #this field should only be used for archival purposes, do not pull data from this directly in production

	#also levelstring stored on the side
	#and raw server response for download type records stored on the side