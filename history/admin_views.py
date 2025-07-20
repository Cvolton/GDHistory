import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test

from datetime import datetime

from history import jsonUtils

from .models import Level, LevelRecord, SaveFile, HistoryUser, ManualSubmission, GDUserGroup
from .forms import ForceUsernameForm, UploadFileForm, SearchForm, UploadSubmissionForm
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

@user_passes_test(lambda u: u.is_superuser)
def search_update_all(request):
    tasks.search_update_all.delay()
    
    return render(request, 'error_success.html', {'error': "good"})

@user_passes_test(lambda u: u.is_superuser)
def force_username(request):
    if request.method == 'POST':
        form = ForceUsernameForm(request.POST)
        if form.is_valid():
            level_id = form.cleaned_data['level_id']
            try:
                print(level_id)
                level_record = LevelRecord.objects.get(id=level_id)
                if level_record.real_user_record is None:
                    return render(request, 'error.html', {'error': "This level record does not have a real user record."})
                user = level_record.real_user_record.user
                user.forced_record = level_record.real_user_record
                user.save()
                user.revalidate_cache()

                Level.objects.filter(cache_user_id=user.online_id).update(cache_needs_revalidation=True)
            except LevelRecord.DoesNotExist:
                return render(request, 'error.html', {'error': "Level record not found."})
            return render(request, 'error_success.html', {'error': "Username forced successfully."})
    else:
        return render(request, 'error.html', {'error': "Invalid request method."})