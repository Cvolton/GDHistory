from history.models import ManualSubmission

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Revalidates user cache'

	def handle(self, *args, **options):
		manuals = ManualSubmission.objects.all()
		manual_count = manuals.count()
		for i,manual in enumerate(manuals):
			print(f"{i} / {manual_count} - Updating {manual.id}")
			manual.get_full_level_count()

		print("Done")