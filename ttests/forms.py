from django import forms
from .models import TestTag
from django.core.exceptions import ValidationError

'''
# 1-ый вариант создания формы "полностью вручную"
class TestTagForm(forms.Form):
	title = forms.CharField(max_length=50)
	slug = forms.SlugField(max_length=50)

	# виджеты позволяют настроить отображение формы (или ее полей)
	# обновляем отображение полей:  в атрибуте class html-тега input
	# выставляем значение form-control (это бутстраповский класс)
	title.widgets.attrs.update({'class': 'form-control'})
	slug.widgets.attrs.update({'class': 'form-control'})

	# у django есть методы clean_<field> для отдельных полей и м. clean
	# для всей формы, который запускает clean м. и м. валидации полей
	# после чего данные из полей заносятся в словарь cleaned_data
	# иначе возбуждается искл. ValidationError
	# именно этот механизм позволяет избежать "неочищенных" данных, которые
	# могут выполнять sql-инъекции

	# clean_<field>
	# м. который обрабатывает поле,  а в словарь cleaned_data попадают
	# только те поля, значения которых прошли проверку (валидацию)
	def clean_slug(self):
		# приводим значение slug к строчным символам
		new_slug = self.cleaned_data['slug'].lower()

		# не понимаю почему проверка на 'create'
		if new_slug == 'create':
			raise ValidationError('Slug may not be "Create"')
		# если такой слаг уже существет
		# ! а в моем случае такой слаг будет существовать если сущетсвует
		# такое название тега
		if TestTag.objects.filter(slug__iexact=new_slug).count():
			raise ValidationError('Slug {} already exists'.format(new_slug))

		return new_slug

	# в этом методе мы реализовали функционал чтобы каждый раз создавался
	# новый объект (запись).  Функционал для изменения объекта мы не описали.
	def save(self):
		new_test_tag = TestTag.objects.create(
			title=self.cleaned_data['title'],
			slug=self.cleaned_data['slug']
		)
		return new_test_tag
'''

# 2-ой вариант создания формы "на основе модели"
class TestTagForm(forms.ModelForm):
	class Meta:
		model = TestTag
		# fields = "__all__"
		# поля, которые будут видны пользователю
		fields = ['title', 'slug']
		# виджеты позволяют настроить отображение формы (или ее полей)
		# обновляем отображение полей:  в атрибуте class html-тега input
		# выставляем значение form-control (это бутстраповский класс)
		widgets = {
			'title': forms.TextInput(attrs={'class': 'form-control'}),
			'slug': forms.TextInput(attrs={'class': 'form-control'}),
		}

	# м. который обрабатывает поле,  а в словарь cleaned_data попадают
	# только те поля, значения которых прошли проверку (валидацию)
	def clean_slug(self):
		# приводим значение slug к строчным символам
		new_slug = self.cleaned_data['slug'].lower()

		# не понимаю почему проверка на 'create'
		if new_slug == 'create':
			raise ValidationError('Slug may not be "Create"')
		# если такой слаг уже существет
		# ! а в моем случае такой слаг будет существовать если сущетсвует
		# такое название тега
		if TestTag.objects.filter(slug__iexact=new_slug).count():
			raise ValidationError('Slug {} already exists'.format(new_slug))

		return new_slug

	def clean_title(self):
		new_title = self.cleaned_data['title'].lower()
		if TestTag.objects.filter(title__iexact=new_title).count():
			raise ValidationError('Title {} already exist'.form(new_title))
		return new_title

	# м. .save() не прописываем, т.к. у модели есть свой метод save()

	# https://youtu.be/ygBff4Vsfyk?t=659


'''
# urls.py
...
	path('tags/create', views.TestTagCreate.as_view(),
	 		name='test_tag_create_ulr')


# вьюшка для обработки этой формы будет выглядеть так:
...
from .forms import TestTagForm

class TestTagCreate(View):
	def get(self, request):
		form = TestTagForm()
		return render(request, 'ttests/test_tag_create.html',
		 			context={'form': form})

	def post(self, request):
		# создаем экземпляр класса TestTagForm с наполненными данными
		# т.е. свзязанную форму (форму с данными, которые ввел пользователь),
		# проводим валидацию данных
		# (метод is_valid) если валидно - создаем соотв. запись,
		# если не валидно - возбуждаем исключение
		bound_form = TestTagForm(request.POST)
		if bound_form.is_valid():
			# bound_form.save()
			new_test_tag = bound_form.save()
			redirect(new_test_tag)
		return render(request, 'ttests/test_tag_create.html',
		 			context={'form': bound_form})



шаблон  test_tag_create.html
{% extends 'ttests/base.html' %}

{% block content %}
	<form action="{% url 'test_tag_create_ulr' %}" method="post">
		{% csrf_token %}

		{% for field in form %}
			<div class="form-group">
				{% if field.errors %}
					<div class="alert alert-danger">
						{{ feild.erros}}
					</div>
				{% endif %}

				{{ field.label }}
				{{ field }}
			</div>
		{% endfor %}

		{% comment %}
		{{ form.title }}
		{{ form.slug }}
		{% endcomment %}

		<button type="submit" class="btn btn-primary">создать тег</button>

	</form>

{% endblock %}

'''



# ======================================================
"""
from django import forms
from .models import Question

class QuestionForm(form.ModelForm):
	class Meta:
		model = Question
		# exclude = ['pole_kotoroe_nuzhno_iscluchit', '...']

	widgets = {
		# 'test': forms.  ....
		'text': forms.TextArea(attrs={
			'class':'fb_form', 'placeholder':'текст вопроса' }),
		'point': forms.IntegerField(attrs={ .... }),
	}
"""

# https://ru.stackoverflow.com/questions/625920/Как-сделать-валидацию-формы-в-django-на-основе-модели

# from djangocms_admin_style import
# from djangosecure import

# -------------------

from django.contrib.auth.forms import (UserCreationForm, User,
									UsernameField, SetPasswordForm)
# UserCreationForm,AuthenticationForm,PasswordChangeForm,
# UserChangeForm,PasswordResetForm,SetPasswordForm,
# AdminPasswordChangeForm,User,ReadOnlyPasswordHashWidget

class CustomUserCreationForm(UserCreationForm):
	def __init__(self, *args, **kwargs):
		super(UserCreationForm, self).__init__(*args, **kwargs)
		self.fields['username'].widget.attrs = {'class': 'form-control'}
		self.fields['username'].help_text = ''
		self.fields['password1'].widget.attrs = {'class': 'form-control'}
		self.fields['password2'].widget.attrs = {'class': 'form-control'}
		self.fields['password2'].help_text = ''

	# class Meta:
		# 	model = User
		# fields = ("username", "password1", 'password2')
		# 	# field_classes = {
		# 	# 	'username': UsernameField,
		# 	# 	'password1': SetPasswordForm,
		# 	# 	'password2': SetPasswordForm,
		# 	# }
		# 	widgets = {
		# 		'username': forms.TextInput(attrs={'class': 'form-control'}),
		# 		'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
		# 		'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
		# 		'password': forms.PasswordInput(attrs={'class': 'form-control'}),
		# 	}


# http://kmv-it.ru/blog/django-registraciya/


# https://www.youtube.com/watch?v=6Qp7ikZrzjY
