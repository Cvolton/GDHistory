from history.models import Level, GDUserGroup, GDUser

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
    help = 'Generates GDUserGroups'
    
    def handle(self, *args, **options):
        levels = Level.objects.filter(online_id__lte=3000000)
        print("Loading levels...")
        for level in levels:
            # print(f"Handling level {level.online_id}...")
            ids = set(level.levelrecord_set.filter(cache_is_dupe=False).values('user_id').distinct().exclude(user_id=None).values_list('user_id', flat=True))
            ids = ids - set([21297937, 5774280, 0, 6133124])
            if len(ids) > 1:
                ids = GDUser.objects.filter(online_id__in=ids).values_list('pk', flat=True)
                print(ids)
                group = GDUserGroup.objects.filter(users__in=ids)
                if group.exists():
                    group_first = group.first()
                    if len(group) > 1:
                        print(f"Multiple groups found: {[g.comment for g in group]}")
                        # move users to first group
                        for g in group:
                            if g.pk != group_first.pk:
                                group_first.users.add(*g.users.all())
                                group_first.save()
                                g.delete()
                    print(f"Group already exists: {group.first().comment}")
                    group_first.users.set(ids, clear=False)
                    group_first.save()
                else:
                    group = GDUserGroup.objects.create(comment=f"Group for level {level.online_id}")
                    group.users.set(ids, clear=False)
                    group.save()
                    print(f"Created group {group.comment}")