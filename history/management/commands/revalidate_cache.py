from history.models import Level, Song

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Revalidates level cache'

	def recalculate_levels(self, levels):
		level_count = levels.count()
		for i in range(0,level_count):
			level = levels[0:1][0]
			print(f"{i} / {level_count} - Updating {level.online_id}")
			level.revalidate_cache()

	def recalculate_songs(self, songs):

		song_count = songs.count()
		for i in range(0,song_count):
			song = songs[i:i+1]
			song = song[0]
			print(f"{i} / {song_count} - Updating {song.online_id}")
			song.revalidate_cache()
			i += 1

	def handle(self, *args, **options):
		levels = Level.objects.filter(cache_needs_revalidation=True)#.prefetch_related('levelrecord_set__save_file').prefetch_related('levelrecord_set__level_string')
		self.recalculate_levels(levels)
		print("Done levels")
		songs = Song.objects.filter(cache_needs_revalidation=True)#.prefetch_related('songrecord_set__save_file')
		self.recalculate_songs(songs)
		print("Done songs")