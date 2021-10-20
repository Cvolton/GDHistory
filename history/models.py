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
	saved = models.DateTimeField(default=datetime.now)
	comment = models.CharField(max_length=255)
	is_processed = models.BooleanField(default=False)
	#also raw save file with password stripped out stored on the side in a file

class GetGJLevelsResponse(models.Model):
	saved = models.DateTimeField(default=datetime.now)
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

	unprocessed_data = models.JSONField() #this field should only be used for archival purposes, do not pull data from this directly in production

	#also levelstring stored on the side
	#and raw server response for download type records stored on the side