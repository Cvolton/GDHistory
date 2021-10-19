from django.db import models

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

class Level(models.Model):
	online_id = models.IntegerField(db_index=True)
	is_public = models.BooleanField() #this is to prevent leaking unlisted levels publicly

class LevelRecord(models.Model):

	class RecordType(models.TextChoices):
		GLM = 'glm', _('GLM')
		DOWNLOAD = 'download', _('downloadGJLevel')
		GET = 'get', _('getGJLevels')

	record_type = models.CharField(
		max_length=8,
		choices=Source.choices,
	)

	level = models.ForeignKey(
		Level,
		on_delete=models.CASCADE,
		db_index=True,
	)

	unprocessed_data = models.TextField() #TODO: custom model field for this?

	#also levelstring stored on the side
	#and raw server response for download type records stored on the side