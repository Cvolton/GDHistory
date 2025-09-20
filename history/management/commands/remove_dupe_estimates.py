from history.models import CommentDateEstimation

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
    help = 'Removes duplicate comment estimates'
 
    def handle(self, *args, **options):
        estimates_object = {}
        estimates = CommentDateEstimation.objects.all()
        for estimate in estimates:
            estimates_object.setdefault((estimate.range_id, estimate.level_id, estimate.comment_id, estimate.type), []).append(estimate)
            
        estimates_object = {k: v for k, v in estimates_object.items() if len(v) > 1}
        
        for key, dupe_estimates in estimates_object.items():
            print(f"Found {len(dupe_estimates)} duplicate estimates for range {key[0]}, level {key[1]}, comment {key[2]}, type {key[3]}")
            dupe_estimates.sort(key=lambda x: x.estimation)
            for estimate in dupe_estimates:
                print(f" - Relative upload date: {estimate.relative_upload_date}, estimate: {estimate.estimation}")
            for estimate in dupe_estimates[1:]:
                estimate.delete()