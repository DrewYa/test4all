from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
	def __init__(self, *args, **kwargs):
		super(UserCreationForm, self).__init__(*args, **kwargs)
		self.fields['username'].widget.attrs = {'class': 'form-control'}
		self.fields['username'].help_text = ''
		self.fields['password1'].widget.attrs = {'class': 'form-control'}
		self.fields['password2'].widget.attrs = {'class': 'form-control'}
		self.fields['password2'].help_text = ''
