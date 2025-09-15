from django import forms

class UploadFileForm(forms.Form):
	file = forms.FileField(label='Upload save file')
	time = forms.CharField(label='Enter a time', max_length=10)

class UploadSubmissionForm(forms.Form):
	file = forms.FileField(label='Upload submission file')

class SearchForm(forms.Form):
	q = forms.CharField(label='Search', required=False)
	p = forms.IntegerField(label='Page', required=False)
	userID = forms.CharField(label='User ID', required=False)
	deleted = forms.BooleanField(label='Deleted only', required=False)
	undeleted = forms.BooleanField(label='Not deleted', required=False)
	playable = forms.BooleanField(label='Data available', required=False)
	unplayable = forms.BooleanField(label='Data unavailable', required=False)
	rated = forms.BooleanField(label='Star only', required=False)
	unrated = forms.BooleanField(label='No Star', required=False)
	difficulty = forms.IntegerField(label='Difficulty', required=False)
	length = forms.IntegerField(label='Length', required=False)
	rerated = forms.BooleanField(label='Re-rated', required=False)
	wasrated = forms.BooleanField(label='Was rated', required=False)
	wasnotrated = forms.BooleanField(label='Was not rated', required=False)
	featured = forms.BooleanField(label='Featured', required=False)
	unfeatured = forms.BooleanField(label='Not featured', required=False)
	negativefeatured = forms.BooleanField(label='Negative featured', required=False)
	daily = forms.BooleanField(label='Was daily', required=False)
	twoPlayer = forms.BooleanField(label='Two player', required=False)
	original = forms.IntegerField(label='Original', required=False)
	minGameVersion = forms.IntegerField(label='Min Game Version', required=False)
	maxGameVersion = forms.IntegerField(label='Max Game Version', required=False)
	gameVersion = forms.IntegerField(label='Game Version', required=False)
	audioTrack = forms.IntegerField(label='Audio Track', required=False)
	songID = forms.IntegerField(label='Song ID', required=False)
	songArtistID = forms.IntegerField(label='Song Artist ID', required=False)
	exactName = forms.CharField(label='Exact Name', required=False)
	s = forms.CharField(label='Sort', required=False)

class LevelForm(forms.Form):
	blanks = forms.BooleanField(label='Show blanks', required=False)
	dupes = forms.BooleanField(label='Show dupes', required=False)

class ApiLevelForm(forms.Form):
	start_from = forms.IntegerField(label='Record ID to start from', required=False)
	count = forms.IntegerField(label='Record count', required=False)

class AdvancedSearchForm(forms.Form):
	query = forms.CharField(label='Query', required=False)
	limit = forms.IntegerField(label='Limit', required=False)
	offset = forms.IntegerField(label='Offset', required=False)
	sort = forms.CharField(label='Sort', required=False)
	filter = forms.CharField(label='Filter', required=False)
	matching_strategy = forms.CharField(label='Matching Strategy', required=False)
 
class ForceUsernameForm(forms.Form):
	level_id = forms.IntegerField(label='Level Record ID', required=True, help_text='Enter the ID of the level record to force the username for.')