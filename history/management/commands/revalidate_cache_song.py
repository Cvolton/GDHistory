from history.models import Level, Song

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Revalidates level cache'

	def handle(self, *args, **options):
		songs = Song.objects.all().prefetch_related('songrecord_set__save_file')
		song_count = songs.count()
		for i in range(0,song_count):
			song = songs[i:i+1]
			song = song[0]
			print(f"{i} / {song_count} - Updating {song.online_id}")
			song.revalidate_cache()
			i += 1

		print("Done")