from history.models import Level, Song

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Revalidates level cache'

	def handle(self, *args, **options):
		levels = Level.objects.all().prefetch_related('levelrecord_set__save_file').prefetch_related('levelrecord_set__level_string')
		level_count = levels.count()
		i = 1
		for level in levels:
			print(f"{i} / {level_count} - Updating {level.online_id}")
			level.revalidate_cache()
			i += 1

		songs = Song.objects.all().prefetch_related('songrecord_set__save_file')
		song_count = songs.count()
		i = 1
		for song in songs:
			print(f"{i} / {song_count} - Updating {song.online_id}")
			song.revalidate_cache()
			i += 1

		print("Done")