from django import forms

class UploadFileForm(forms.Form):
	file = forms.FileField(label='Upload save file')
	time = forms.CharField(label='Enter a time', max_length=10)