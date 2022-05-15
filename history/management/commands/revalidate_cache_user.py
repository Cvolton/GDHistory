from history.models import GDUser

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
	help = 'Revalidates user cache'

	def handle(self, *args, **options):
		users = GDUser.objects.all().prefetch_related('gduserrecord_set')
		user_count = users.count()
		for i in range(0,user_count):
			user = users[i:i+1]
			user = user[0]
			print(f"{i} / {user_count} - Updating {user.online_id}")
			user.revalidate_cache()

		print("Done")