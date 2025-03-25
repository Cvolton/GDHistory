from history import utils
from history.models import Level
from django.contrib.auth.models import User

import os
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Removes all blacklisted user IDs from public search'

    def handle(self, *args, **options):
        blacklisted_userids = utils.get_blacklisted_userids(True)
        for userid in blacklisted_userids:
            try:
                levels = Level.objects.filter(cache_user_id=userid, hide_from_search=False)
                for level in levels:
                    print(f"Removing {level.online_id} from public search")
                    level.hide_from_search = True
                    level.cache_needs_revalidation = True
                    level.save()
            except User.DoesNotExist:
                print(f"User {userid} not found")
            except Exception as e:
                print(f"Error: {e}")
