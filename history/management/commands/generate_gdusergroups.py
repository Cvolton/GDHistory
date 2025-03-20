from history.models import Level, GDUserGroup

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
    help = 'Generates GDUserGroups'
    
    def handle(self, *args, **options):
        levels = Level.objects.filter(online_id__lte=3000000)
        print("Loading levels...")
        for level in levels:
            # print(f"Handling level {level.online_id}...")
            ids = list(level.levelrecord_set.filter(cache_is_dupe=False).values('user_id').distinct().exclude(user_id=None).values_list('user_id', flat=True))
            if len(ids) > 1:
                print(ids)
                group = GDUserGroup.objects.filter(users__in=ids)
                if group.exists():
                    if len(group) > 1:
                        print(f"Multiple groups found: {[g.comment for g in group]}")
                        # move users to first group
                        group_first = group.first()
                        for g in group:
                            if g != group_first:
                                group_first.users.add(*g.users.all())
                                g.delete()
                    print(f"Group already exists: {group.first().comment}")
                    group.first().users.add(*ids)
                else:
                    group = GDUserGroup.objects.create(comment=f"Group for level {level.online_id}")
                    group.users.add(*ids)
                    print(f"Created group {group.comment}")