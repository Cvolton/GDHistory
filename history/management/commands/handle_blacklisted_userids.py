import history.ccUtils
from history.models import Level
from django.contrib.auth.models import User

import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    help = 'Removes all blacklisted user IDs from public search'

    def handle(self, *args, **options):
        data_path = history.utils.get_data_path()
        if not os.path.exists(f"{data_path}/blacklisted_userids.txt"):
            print("No blacklisted_userids.txt file found")
            return
        with open(f"{data_path}/blacklisted_userids.txt", "r") as f:
            blacklisted_userids = f.read().splitlines()
        for userid in blacklisted_userids:
            try:
                levels = Level.objects.filter(cache_user_id=int(userid.strip()), hide_from_search=False)
                for level in levels:
                    print(f"Removing {level.online_id} from public search")
                    level.hide_from_search = True
                    level.cache_needs_revalidation = True
                    level.save()
            except User.DoesNotExist:
                print(f"User {userid} not found")
            except Exception as e:
                print(f"Error: {e}")
