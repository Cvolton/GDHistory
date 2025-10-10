from collections import defaultdict
from history.models import CommentDateEstimation

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

class Command(BaseCommand):
    help = 'Removes badly dated comment estimates'
 
    def handle(self, *args, **options):
        estimates = CommentDateEstimation.objects.all().order_by(
            "type", "range_id", "estimation", "comment_id"
        )

        grouped = defaultdict(list)
        for estimate in estimates:
            grouped[(estimate.type, estimate.range_id)].append(estimate)

        for (etype, rid), group in grouped.items():
            for i, estimate in enumerate(group):
                invalids = [
                    invalid for invalid in group[i+1:]
                    if invalid.estimation > estimate.estimation and invalid.comment_id < estimate.comment_id
                ]

                if invalids:
                    print(f"Checking estimate: {estimate}: {etype}, {rid}, {estimate.estimation}, {estimate.comment_id}")
                    for invalid in invalids:
                        print(
                            f"- Found invalid estimate: {invalid} "
                            f"for range {rid} with estimation {invalid.estimation} "
                            f"and comment_id {invalid.comment_id}"
                        )
                    
                    ids = [inv.id for inv in invalids]
                    deleted, _ = CommentDateEstimation.objects.filter(id__in=ids).delete()

