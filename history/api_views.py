from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count, Min, Max, Q
from django.db.models.functions import Coalesce

from datetime import datetime

from .models import Level, LevelRecord, Song, SaveFile, ServerResponse, LevelString, HistoryUser
from .forms import UploadFileForm, SearchForm
from . import ccUtils, serverUtils, tasks, utils

import math
import plistlib

def index_counts(request):

	counts = {
		'level_count': Level.objects.filter(cache_search_available=True).count(),
		'song_count': Song.objects.count(),
		'save_count': SaveFile.objects.count(),
		'request_count': ServerResponse.objects.count(),
		'level_string_count': LevelString.objects.count(),
	}

	return JsonResponse(counts)
