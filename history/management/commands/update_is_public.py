from history.models import LevelRecord
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):
		"""Note that this expects gameVersion to be set correctly, which isn't guaranteed in the real world.
		There is at least one version of GD 2.1, which had gameVersion set to 20 for all uploaded levels.
		The amount of levels uploaded like this is so low, that this is	not an edge case worth handling."""
		records = LevelRecord.objects.filter(Q(record_type=LevelRecord.RecordType.GET) | Q(game_version__lte=20)).exclude(level__is_public=True).prefetch_related('level')
		record_count = records.count()
		i = 1
		for record in records:
			print(f"{i} / {record_count} - Updating {record.level.online_id}")
			record.level.is_public = True
			record.level.save()
			i += 1

		print("Done")