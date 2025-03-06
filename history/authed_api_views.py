from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from history.models import LevelRecord

import math
import meilisearch
import sys

@csrf_exempt
@login_required
def record_source_info(request, record_id):
	try:
		levelrecord = LevelRecord.objects.get(id=record_id)
	except:
		return JsonResponse({'success': False}, status=404)
	
	return JsonResponse(levelrecord.get_serialized_sources())