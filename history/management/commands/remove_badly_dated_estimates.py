from history.models import CommentDateEstimation

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
    help = 'Removes badly dated comment estimates'
 
    def handle(self, *args, **options):
        estimates_object = {}
        estimates = CommentDateEstimation.objects.all()
        for estimate in estimates:
            invalids = CommentDateEstimation.objects.filter(type=estimate.type, range_id=estimate.range_id, estimation__gt=estimate.estimation, comment_id__lt=estimate.comment_id)
            if invalids.exists():
                print(f"Checking estimate: {estimate}: {estimate.type}, {estimate.range_id}, {estimate.estimation}, {estimate.comment_id}")
            for invalid in invalids:
                print(f"- Found invalid estimate: {invalid} for range {invalid.range_id} with estimation {invalid.estimation} and comment_id {invalid.comment_id}")