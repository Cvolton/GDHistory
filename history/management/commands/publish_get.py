from history.models import Level, Song

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Publishes levels with get records'

	def handle(self, *args, **options):
		target_ids = list(
            LevelRecord.objects.filter(
                record_type="get",
                level__is_public=False
            )
            .values_list('level_id', flat=True)[:10000] 
        )

        if target_ids:
            print("- beginning update")
            Level.objects.filter(id__in=target_ids).update(is_public=True)
            print("-- update done")