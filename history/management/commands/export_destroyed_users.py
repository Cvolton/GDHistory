from history.models import GDUser, LevelRecordType, GDUserRecord
import history.utils
import json
import math

from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):
		users = {}
		data_path = history.utils.get_data_path()
		print("_begin")
		records = GDUser.objects.filter(gduserrecord__record_type=LevelRecordType.GET, gduserrecord__username=None).prefetch_related('gduserrecord_set').distinct()
		record_count = records.count()
		print(f"_count: {record_count}")
		batch_size = 2500
		batch_count = math.ceil(record_count/2500)
		for i in range(0,batch_count):
			print(f"_batch {i}")
			users_small = records[i*batch_size:(i+1)*batch_size]
			for user in users_small:
				print(f"_user {user.online_id}")
				record_list = GDUserRecord.objects.filter(user=user).exclude( Q(username='-') | Q(username=None) ).order_by('-cache_created')
				non_player_record = record_list.exclude(username='Player')[:1]
				if len(non_player_record) > 0:
					print(f"{user.online_id} - {non_player_record[0].username}")
					users[user.online_id] = non_player_record[0].username
				else:
					record_list = record_list[:1]
					if len(record_list) > 0:
						print(f"{user.online_id} - {record_list[0].username}")
						users[user.online_id] = record_list[0].username
		with open(f"{data_path}/Exports/DestroyedUsers.json", "w") as file_object:
			json.dump(users, file_object)

		print("Done")