from django.contrib import admin
from .models import HistoryUser, SaveFile, GetGJLevelsResponse, Level, LevelRecord

# Register your models here.
admin.site.register(HistoryUser)
admin.site.register(SaveFile)
admin.site.register(GetGJLevelsResponse)
admin.site.register(Level)
admin.site.register(LevelRecord)