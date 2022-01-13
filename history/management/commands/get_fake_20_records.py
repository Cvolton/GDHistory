from history.models import LevelRecord
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Gets 2.1 level records predenting to be 2.0'

	def handle(self, *args, **options):
		records = LevelRecord.objects.filter(game_version=20).prefetch_related('level')
		record_count = records.count()
		i = 1
		for record in records:
			if record.extra_string is None:
				continue

			batch_count = len(record.extra_string.split('_'))

			if batch_count > 16:
				print(f"{i} / {record_count} - {batch_count}: {record.level.online_id} ({record.pk}) - {record.level_name} by {record.username}")
			i += 1

		print("Done")