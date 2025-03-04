from history.models import LevelString

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Calculates object counts in level strings'

	def handle(self, *args, **options):
		song_count = 100000
		songs = LevelString.objects.filter(object_count=None).order_by('-decompressed_file_size')[:song_count]
		#song_count = songs.count()
		i = 0
		for song in songs:
			print(f"{i} / {song_count} - Updating {song.pk}")
			song.calculate_object_count()
			i += 1

		print("Done")