from history.models import GDUser, LevelRecordType
import history.utils
import json
import math

from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):
		records = GDUser.objects.filter(gduserrecord__record_type=LevelRecordType.GET, gduserrecord__username=None).prefetch_related('gduserrecord_set').distinct()
		record_count = records.count()
		batch_size = 2500
		batch_count = math.ceil(record_count/2500)
		for i in range(0,batch_count):
			users_small = records[i*batch_size:(i+1)*batch_size]
			for user in users_small:
				record_list = user.gduserrecord_set.exclude( Q(username='-') | Q(username=None) ).order_by('-cache_created')
				non_player_record = record_list.exclude(username='Player')[:1]
				if len(non_player_record) > 0:
					print(f"{user.online_id} - {non_player_record[0].username}")
				else:
					record_list = record_list[:1]
					if len(record_list) > 0:
						print(f"{user.online_id} - {record_list[0].username}")

		print("Done")