from history.models import LevelRecord, SongRecord, SaveFile
import history.ccUtils

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Processes unprocessed save files'

	def handle(self, *args, **options):
		save_files = SaveFile.objects.filter(is_processed=False)

		print("Processing save files")
		for file in save_files:
			#TODO: handle failures properly
			try:
				history.ccUtils.process_save_file(file.pk)
			except Exception as e: print(e)