import history.maintenance_utils

from django.core.management.base import BaseCommand, CommandError
from history.models import LevelDateEstimation, Level
from django.db.models import Q

class Command(BaseCommand):
	help = 'Exports server responses as JSON'

	def handle(self, *args, **options):
		to_fix = LevelDateEstimation.objects.exclude( Q(relative_upload_date=None) | Q(is_offset=True) )
		total = len(to_fix)
		for i,estimation in enumerate(to_fix):
			print(f"fixing {i}/{total} - {estimation.level.online_id} | {estimation.pk}")
			new_level = Level.objects.filter(online_id__lt=estimation.level.online_id, is_deleted=False).order_by('-online_id')[:1][0]
			print(f"old id: {estimation.level.online_id}, new id: {new_level.online_id}")
			estimation.level = new_level
			estimation.is_offset = True
			estimation.save()