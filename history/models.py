from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _

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
	created = models.DateTimeField(default=datetime.now)
	comment = models.CharField(max_length=255)
	is_processed = models.BooleanField(default=False)
	#also raw save file with password stripped out stored on the side in a file

class GetGJLevelsResponse(models.Model):
	created = models.DateTimeField(default=datetime.now)
	unprocessed_post_parameters = models.JSONField()


class Level(models.Model):
	online_id = models.IntegerField(db_index=True)
	is_public = models.BooleanField(blank=True, null=True,) #this is to prevent leaking unlisted levels publicly

class LevelRecord(models.Model):

	class RecordType(models.TextChoices):
		GLM = 'glm', _('GLM')
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

	save_file = models.ForeignKey(
		SaveFile,
		on_delete=models.CASCADE,
		blank=True, null=True,
		db_index=True,
	)

	get_gj_levels_response = models.ForeignKey(
		GetGJLevelsResponse,
		on_delete=models.CASCADE,
		blank=True, null=True,
		db_index=True,
	)

	level_name = models.TextField(blank=True, null=True) #k2
	description = models.TextField(blank=True, null=True) #k3
	username = models.TextField(blank=True, null=True) #k5
	user_id = models.IntegerField(blank=True, null=True) #k6
	official_song = models.IntegerField(blank=True, null=True) #k8
	rating = models.IntegerField(blank=True, null=True) #k9
	rating_sum = models.IntegerField(blank=True, null=True) #k10
	downloads = models.IntegerField(blank=True, null=True) #k11
	level_version = models.IntegerField(blank=True, null=True) #k16
	game_version = models.IntegerField(blank=True, null=True) #k17
	likes = models.IntegerField(blank=True, null=True) #k22
	length = models.IntegerField(blank=True, null=True) #k23 #technically speaking this would be better as an ENUM but nothing actually guarantees that the value won't go out of bounds
	dislikes = models.IntegerField(blank=True, null=True) #k24
	demon = models.BooleanField(blank=True, null=True) #k25
	stars = models.IntegerField(blank=True, null=True) #k26
	feature_score = models.IntegerField(blank=True, null=True) #k27
	auto = models.BooleanField(blank=True, null=True) #k33
	password = models.IntegerField(blank=True, null=True) #k41
	two_player = models.BooleanField(blank=True, null=True) #k43
	custom_song = models.IntegerField(blank=True, null=True) #k41
	objects_count = models.IntegerField(blank=True, null=True) #k48
	account_id = models.IntegerField(blank=True, null=True) #k60
	coins = models.IntegerField(blank=True, null=True) #k64
	coins_verified = models.BooleanField(blank=True, null=True) #k65
	requested_stars = models.IntegerField(blank=True, null=True) #k66
	extra_string = models.IntegerField(blank=True, null=True) #k67 #also known as the capacity string
	daily_id = models.IntegerField(blank=True, null=True) #k74
	epic = models.BooleanField(blank=True, null=True) #k75
	demon_type = models.IntegerField(blank=True, null=True) #k76
	seconds_spent_editing = models.IntegerField(blank=True, null=True) #k80
	seconds_spent_editing_copies = models.IntegerField(blank=True, null=True) #k81

	level_string_available = models.BooleanField(default=False) #k4

	unprocessed_data = models.JSONField() #this field should only be used for archival purposes, do not pull data from this directly in production

	#also levelstring stored on the side
	#and raw server response for download type records stored on the side