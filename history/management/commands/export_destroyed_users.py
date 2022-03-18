from history.models import GDUser, LevelRecordType
import history.utils
import json

from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):
		records = GDUser.objects.filter(gduserrecord__record_type=LevelRecordType.GET, gduserrecord__username=None).prefetch_related('gduserrecord_set').distinct()
		for user in records:
			record_list = user.gduserrecord_set.exclude( Q(username='-') | Q(username=None) ).order_by('-cache_created')
			non_player_record = record_list.exclude(username='Player')[:1]
			if len(non_player_record) > 0:
				print(f"{user.online_id} - {non_player_record[0].username}")
			else:
				record_list = record_list[:1]
				if len(record_list) > 0:
					print(f"{user.online_id} - {record_list[0].username}")

		print("Done")