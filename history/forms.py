from django import forms

class UploadFileForm(forms.Form):
	file = forms.FileField(label='Upload save file')
	time = forms.CharField(label='Enter a time', max_length=10)

class SearchForm(forms.Form):
	q = forms.CharField(label='Search')
	p = forms.IntegerField(label='Page', required=False)