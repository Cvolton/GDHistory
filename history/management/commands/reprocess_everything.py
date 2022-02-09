from history.models import LevelRecord, SongRecord, SaveFile
import history.ccUtils

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Deletes all LevelRecords'

	def handle(self, *args, **options):
		print("Clearing level records")
		level_records = LevelRecord.objects.all().delete()

		print("Clearing song records")
		song_records = SongRecord.objects.all().delete()

		print("Flagging save files")
		save_files = SaveFile.objects.all()
		for file in save_files:
			file.is_processed = False
			file.save()

		print("Processing save files")
		for file in save_files:
			#TODO: handle failures properly
			try:
				history.ccUtils.process_save_file(file.pk)
			except Exception as e: print(e)