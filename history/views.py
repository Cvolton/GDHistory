from django.shortcuts import render
from django.http import HttpResponse

from .models import Level, LevelRecord
from . import ccUtils, serverUtils

def index(request):
	return render(request, 'index.html')

def view_level(request, online_id=None):
	level_records = LevelRecord.objects.filter(level__online_id=online_id).prefetch_related('level')
	context = {'level_records': level_records, 'online_id': online_id}

	serverUtils.download_level(online_id)

	return render(request, 'level.html', context)