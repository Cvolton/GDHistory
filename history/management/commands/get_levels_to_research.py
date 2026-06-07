from history.models import Level

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, Max
from history import utils

class Command(BaseCommand):
	help = ''

	def handle(self, *args, **options):
		current_id = 0
		ids = []
		#get max level id
		max_level_id = Level.objects.aggregate(max_id=Max('id'))['max_id']
		while current_id < max_level_id:
			next_id = current_id + 100000
			print(f'[{100 * current_id / max_level_id:.2f}%] Checking levels with id between {current_id} and {next_id}...')
			levels = Level.objects.filter(is_deleted=False, is_public=False, id__gte=current_id, id__lte=next_id)
			current_id = next_id
			ids.extend([level.online_id for level in levels])
		with open(f"{utils.get_data_path()}/levels_to_research.txt", 'w') as f:
			f.write('\n'.join(str(id) for id in ids))