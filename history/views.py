from django.shortcuts import render
from django.http import HttpResponse

from .models import Level, LevelRecord
from . import ccUtils

def index(request):
	ccUtils.test()
	return HttpResponse("welcome")

def view_level(request, online_id=None):
	level_records = LevelRecord.objects.filter(level__online_id=online_id).prefetch_related('level')
	context = {'level_records': level_records}
	return render(request, 'level.html', context)