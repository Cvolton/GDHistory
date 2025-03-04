from history.models import LevelString

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Calculates file size and other missing detadata in level strings'

	def handle(self, *args, **options):
		song_count = 10000
		songs = LevelString.objects.filter(file_size=None)[:10000]
		#song_count = songs.count()
		i = 0
		for song in songs:
			print(f"{i} / {song_count} - Updating {song.pk}")
			song.get_serialized_base()
			i += 1

		print("Done")