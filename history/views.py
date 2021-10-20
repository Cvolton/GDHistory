from django.shortcuts import render
from django.http import HttpResponse

from . import ccUtils

def index(request):
	ccUtils.test()
	return HttpResponse("welcome")