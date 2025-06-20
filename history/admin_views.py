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
    tasks.revalidate_cache_all.delay()
        
    return render(request, 'error_success.html', {'error': "good"})