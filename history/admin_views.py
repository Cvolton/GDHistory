import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test

from datetime import datetime

from history import jsonUtils

from .models import Level, LevelRecord, SaveFile, HistoryUser, ManualSubmission, GDUserGroup
from .forms import UploadFileForm, SearchForm, UploadSubmissionForm
from . import ccUtils, tasks, utils, meili_utils

import math
import plistlib
import meilisearch
import random
import re
from os import sys

@user_passes_test(lambda u: u.is_superuser)
def index(request):
	context = {
		'meili_stats': meili_utils.admin_stats(),
        'cache_needs_revalidation': Level.objects.filter(cache_needs_revalidation=True).count(),
        'cache_needs_search_update': Level.objects.filter(cache_needs_search_update=True).count(),
	}

	return render(request, 'admin/index.html', context)

@user_passes_test(lambda u: u.is_superuser)
def revalidate_all(request):
    max_level_id = Level.objects.order_by('-pk').first().pk if Level.objects.exists() else 0
    batch_size = 100000
    for i in range(0, math.ceil(max_level_id / batch_size)):
        start = i * batch_size
        end = (i + 1) * batch_size

        levels_to_revalidate = Level.objects.filter(pk__gt=start, pk__lt=end)
        if not levels_to_revalidate.exists():
            continue
        levels_to_revalidate.update(cache_needs_revalidation=True)
        print(f"Forced revalidation for levels from {start} to {end}")
        
    return render(request, 'error_success.html', {'error': "good"})