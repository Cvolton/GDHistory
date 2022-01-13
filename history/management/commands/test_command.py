from history.models import LevelRecord
from history.constants import MiscConstants
import history.utils
import json

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'is test'

	def handle(self, *args, **options):
		records = LevelRecord.objects.filter(game_version=20).prefetch_related('level').order_by('-level__online_id')[:10]
		record_count = records.count()
		i = 1
		for record in records:
			print(f"{i} / {record_count} - Updating {record.level.online_id}")
			i += 1

		print("Done")