from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
	email = forms.EmailField(required=True, label="Email")
	first_name = forms.CharField(required=False, label="Prénom", max_length=30)
	last_name = forms.CharField(required=False, label="Nom", max_length=150)

	class Meta:
		model = User
		fields = ("username", "email", "first_name", "last_name", "password1", "password2")

	def save(self, commit=True):
		user = super().save(commit=False)
		user.email = self.cleaned_data.get('email')
		user.first_name = self.cleaned_data.get('first_name', '')
		user.last_name = self.cleaned_data.get('last_name', '')
		if commit:
			user.save()
		return user


class SimpleProfileForm(forms.Form):
	first_name = forms.CharField(label="Prénom", max_length=30, required=True)
	last_name = forms.CharField(label="Nom", max_length=150, required=True)
	SEXE_CHOICES = (
		('M', 'Masculin'),
		('F', 'Féminin'),
		('O', 'Autre'),
	)
	sex = forms.ChoiceField(label="Sexe", choices=SEXE_CHOICES, required=True)
	city = forms.CharField(label="Ville", max_length=100, required=True)


