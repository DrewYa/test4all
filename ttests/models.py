from django.db import models
from django.db.models import Q
from django.shortcuts import reverse
import os

# для валидации полей
from django.core.exceptions import ValidationError
# from .validators import validate_even

# ------------------

# https://djbook.ru/rel1.9/topics/signals.html
# from django.core.signals import .. # отправляются при нач. и оконч. http запроса
# from django.db.signals import
# отпрвл. до и после вызова м. save() модели; до и после вызоыва м.
# delete() модели и QuerySet'a; после изменения ManyToManyField в модели;
# начала и окончания http запроса
# from django.db.models.signals import

# ----------------

# Create your models here.


class User(models.Model):											## del model
	class Meta:
		managed = True
	name = models.CharField(max_length=100)
	# email
	# password_hash
	# about_me

	def  __str__(self):
		return self.name


class TestTag(models.Model):
	class Meta:
		verbose_name = 'Тег теста'
		verbose_name_plural = 'Теги теста'
		ordering = ('title',)
		managed = True # позволяет django удалять таблицу из БД

	title = models.CharField(max_length=50, unique=True,
							verbose_name='название')
	# убрать из админки, сделать автозаполняемым через slugify
	slug = models.SlugField(max_length=50, unique=True,
							verbose_name='ссылка',   blank=True)

	def get_absolute_url(self):
		return reverse('ttests:test_by_tag_url', kwargs={'slug': self.slug})

	def count_published_test(self):
		return self.tests.filter(is_published=True).count()

	# def clean(self):
	# 	if self.objects.get(title__iexact=self.title):
	# 		raise ValidationError('такой тег уже существует')

	# def save(self, force_insert=False, force_update=False):
	# 	self.title = self.title.lower()
	# 	super(TestTag, self).save(force_insert, force_update)
	# 	# self.full_clean(exclude=None, validate_unique=True)

	def __str__(self):
		return self.title


class Test(models.Model):
	'''\
	is_published - опубликован ли тест. После публикации автор не может изменять
	тест, может только удалить.
	update_date - показывает дату последнего обновления или дату дату публикации
	testing_time - максимальное отведенное время на прохождение теста
	show_q_number - сколько вопросов показывать тестируему из общего количества
	вопросов в тесте (по умолчанию все вопросы).
	is_shuffle_q - перемешать ли вопросы (вопросы будут показываться не в поряд-
	ке их составления автором)
	only_fully_correct - засчитывать только вопросы, на которые был дан 100%
	верный ответ (для множеств. и ассоц. ответов)

	'''
	class Meta:
		verbose_name = 'Тест'
		verbose_name_plural = 'Тесты'
		# ordering = ('title',)
		managed = True

	def user_directory_path(self, filename):
		# filename будет браться при загрузке файла "само"
		# запрашиваем у объекта пользователя, у которого запрашиваем id
		# file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
		# print(filename)
		return 'user_{0}/{1}'.format(self.author.id, filename)

	title = models.CharField(max_length=140, verbose_name='заголовок')
	description = models.TextField(max_length=3500, blank=True, null=True,
					verbose_name='описание',
					help_text='заполнять не обязательно, но это поможет\
					пользователям лучше понять тематику теста')
	img_description = models.ImageField(upload_to=user_directory_path,
	 				blank=True, null=True, verbose_name='картинка теста',
					help_text='картинка позволит быстрее найти тест')
	is_published = models.BooleanField(default=False, verbose_name='опубликовать?',
					help_text='после публикации тест станет доступен другим\
					пользователям для прохождения. После публикации\
					не желательно изменять тест (только удалять)')
	# убрать и добавить нормальную связь с пользователями
	author = models.ForeignKey('User', on_delete=models.SET_NULL, null=True,
					related_name='tests' )
	tags = models.ManyToManyField(to='TestTag', related_name='tests', blank=True,
					verbose_name='теги для теста',
					help_text='Это позволит быстрее найти тест среди других.')
	create_date = models.DateTimeField(auto_now=False, auto_now_add=True,
	 				db_index=True)
	update_date = models.DateTimeField(auto_now=True, auto_now_add=False,
	 				db_index=True)
	testing_time = models.DurationField(null=True, blank=True,
					verbose_name='время тестирования',
					help_text='в формате ЧЧ:ММ:СС')
	show_q_number = models.PositiveSmallIntegerField(null=True, blank=True,
					verbose_name='количество вопросов',
					help_text='пользователю будет показано столько вопросов.\
					В действительности тест может иметь больше вопросов')
	is_shuffle_q = models.BooleanField(default=False,
					verbose_name='перемешать вопросы?',
					help_text='вопросы будут идти не по порядку')
	only_fully_correct = models.BooleanField(default=False,
					verbose_name='только 100% верные ответы',
					help_text='засчитывать только полностью верные ответы\
					(для вопросов с множественными и ассоциативными ответами)\
					иначе будет вычислен балл для частично правильных ответов')
	#  не создавать - будет браться из значения поля id для теста
	# slug = models.SlugField

	def get_absolute_url(self):
		return reverse('ttests:test_detail_url', kwargs={'id': self.id})

	def count_q_to_answer(self):
		if self.show_q_number and \
		 		self.show_q_number <= self.questions.count():
			return self.show_q_number
		return self.questions.count()

	def get_all_q_id(self):
		dict_val = self.questions.values('id')
		return [ item['id'] for item in dict_val ]

	def __str__(self):
		if len(self.title) < 50:
			return self.title
		return '{}...'.format(self.title[:47])


class QuestionTag(models.Model):
	class Meta:
		verbose_name = 'Тег вопроса'
		verbose_name_plural = 'Теги вопроса'
		managed = True

	name = models.CharField(max_length=120, verbose_name='название')
	recommendation = models.TextField(max_length=2000, verbose_name='рекомендации',
							help_text='рекомендации будут выведены тестируемому\
							в конце теста, если он неправильно ответит на вопросы\
							с этим тегом')
	questions = models.ManyToManyField(to='Question', related_name='tags',
							verbose_name='для вопроса')
	# убрать поле из админки, сделать автоматическое заполнение
	# наверно с помощью "сигналов"
	# а вообще нужно ли оно? (если тест удалить, то его вопросы, а значит и теги
	# тоже. Делал для того, чтобы у каждого теста были уникальный набор тегов и
	# не было ситуации, что один и тот же тег применялся к разным тестам с вопросами)
	test = models.ForeignKey(to='Test', on_delete=models.CASCADE,
							related_name='questions_tags')

	def __str__(self):
		if len(self.name) < 70:
			return self.name
		return '{}...'.format(self.name[:67])

class Question(models.Model):
	class Meta:
		verbose_name = 'Вопрос'
		verbose_name_plural = 'Вопросы'
		managed = True

	def user_directory_path(self, filename):
		# MEDIA_ROOT/user_<id>/test_<id>/<filename>
		return 'user_{0}/test_{1}/{2}'.format(
					self.test.author.id, self.test.id, filename)

	test = models.ForeignKey('Test', on_delete=models.CASCADE,
	 						related_name='questions', verbose_name='для теста')
	text = models.TextField(max_length=1500, verbose_name='текст вопроса')
	mediafile = models.ImageField(upload_to=user_directory_path, blank=True,
	 						null=True, verbose_name='картинка для вопроса')
	point = models.PositiveSmallIntegerField(default=1,
							verbose_name='баллы за верный ответ',)
							# validators=[validate_even])
	explanation = models.TextField(blank=True, max_length=1000,
							verbose_name='пояснение ответа')

	def count_answers(self):
		return self.answers.count()

	def count_is_right_answers(self):
		return self.answers.filter(is_right=True).count()

	def count_associate_answers(self):
		return self.associate_answers.count()

	def count_right_not_none(self):
		return self.associate_answers.exclude(right_side=None).count()

	# недостаточно хорошо работает
	def clean(self):
		if self.answers.count() != 0 and self.associate_answers.count() != 0:
			asa = self.associate_answers.all()
			asa.delete()
			raise ValidationError('Вопрос не может быть одновременно вопросом на\
			 	сопоставление и вопросом на саомстоятельный / одиночный /\
				множественный ответ.')
		# а еще нужно добавить проверку - установлен ли хотябы у одного ответа
		# флажок is_right
		# а если там ассоциативные ответы - установлен ли хотябы для одного из
		# них необязательная "right_side"


	# def ids_answers(self):
	# 	return self.answers

	# ###
	# def get_absolute_url(self):
	# 	return reverse('ttests:testing_url', kwargs={'question_id': self.id})
	def get_absolute_url(self):
		return reverse('ttests:show_question_url', kwargs={'question_id': self.id})

	def __str__(self):
		if len(self.text) < 70:
			return self.text
		return '{}...'.format(self.text[:67])


class Answer(models.Model):
	class Meta:
		verbose_name = 'Одиноч. / множеств. / самост. ответ'
		verbose_name_plural = 'Одиноч. / множеств. / самост. ответы'
		managed = True

	question = models.ForeignKey(to='Question', on_delete=models.CASCADE,
							related_name='answers', verbose_name='для вопроса')
							# validators=[validate_one_type_answer])
	text = models.CharField(max_length=300, verbose_name='текст ответа')
	is_right = models.BooleanField(default=False, verbose_name='это правильный ответ')

	def __str__(self):
		if len(self.text) < 70:
			return self.text
		return '{}...'.format(self.text[:67])


class AssociateAnswer(models.Model):
	class Meta:
		verbose_name = 'Ответ с сопоставлением частей'
		verbose_name_plural = 'Ответы с сопоставлением частей'
		managed = True

	question = models.ForeignKey(to='Question', on_delete=models.CASCADE,
							related_name='associate_answers',
							verbose_name='для вопроса')
	right_side = models.CharField(max_length=300, blank=True, null=True,
							verbose_name='правая часть',
							help_text='правая часть сопоставления может быть пустой')
	left_side = models.CharField(max_length=300, verbose_name='левая часть')

	def right_side_none(self):
		return False if self.right_side else True

	def __str__(self):
		if self.right_side:
			if len(self.right_side) < 35:
				r = self.right_side
			else:
				r = self.right_side[:32] + '..'
		else:
			r = '___'
		if len(self.left_side) < 30:
			l = self.left_side
		else:
			l = self.left_side[:27] + '..'
		return '{} <-> {}'.format(r, l)





# ----------- сигналы -------------

from django.db.models.signals import pre_save
from transliterate import translit
from django.utils.text import slugify

def pre_save_test_tag_slug(sender, instance, *args, **kwargs):
	# в этом случае заголовок будет приведен к нижнему регистру, но ошибки
	# валидации не вызовет
	instance.title = instance.title.lower()
	# это не прокатывает
	# if TestTag.objects.get(title__iexact=instance.title):
	# 	raise ValidationError('такой тэг теста уже существует')
	if not instance.slug:
		print('title:   ', instance.title)
		# reversed - чтобы ru -> en
		translit_title = translit(instance.title, reversed=True)
		slug = slugify(translit_title)
		print('slug:   ', slug)
		instance.slug = slug
	'''
	# работает, но вместо того, чтобы показать заново страницу с редактированием
	try:
		# тэга - показывает страницу с ошибками
		instance.full_clean(exclude=None, validate_unique=True)
	except ValidationError as e:
		raise ValidationError('sdddf')
	'''

pre_save.connect(receiver=pre_save_test_tag_slug, sender=TestTag)
# теперь если мы зайдем в модели TestTag у поля slug нужно указать blank=True


# def pre_save_question_tag(sender, instance, *args, **kwargs):
# 	if not instance.test:
# 		instance.test = instance.questions.all()[0].test.id
# pre_save.connect(reveiver=pre_save_question_tag, sender=QuestionTag)



# ===========================================================================
# модели ниже вставить в отдельное приложение, которое будет резализовывать
# логику по анализу результатов тестирования
'''
class Testing(models.Model):
	class Meta:
		pass

	user = models.ForeignKey  # on_delete=models.CASCADE
	test = models.ForeignKey(to='django.ttests.models.Test', on_delete=models.SET_NULL)
	question = models.ForeignKey  # on_delete=models.SET_NULL
	score = models.CharField

class TestingAssocAnswer(models.Model):
	class Meta:
		pass

	testing = models.ForeignKey(to='Testing', on_delete=models.CASCADE)
	answer_left_id = models.IntegerField
	answer_right_id = models.IntegerField

class TestingAnswer(models.Model):
	class Meta:
		pass

	testing = models.ForeignKey(to='Testing', on_delete=models.CASCADE)
	answer_id = models.IntegerField
	answer_text = models.TextField


class TestResult(models.Model):
	class Meta:
		pass

	user = models.ForeignKey  # on_delete=models.CASCADE
	test = models.ForeignKey  # on_delete=models.SET_NULL
	result = models.PositiveSmallIntegerField
	date_complition = models.DateTimeField  # db_index=True
	date_start = models.DateTimeField  # db_index=True
	questions_tags = models.ForeignKey(to='django.ttests.models.QuestionTag',
										on_delete=models.SET_NULL)
'''


# ======================================================================

# желательно вначале в качестве первой мигарции создать пустую миграцию
# https://djbook.ru/rel1.4/topics/migrations.html#data-migrations
# это делается с помощью команды
# python manage.py makemigrations --empty yourappname
# --------------------------------------------------------------------
# для создания сложных вопросов, нужна агрегация
# https://docs.djangoproject.com/en/2.0/topics/db/aggregation/#filtering-on-annotations
# --------------------------------------------------------------------------
'''
все же возможно сделать функцию для атрибута поля upload_to
подробнее тут https://djbook.ru/rel1.4/topics/migrations.html#historical-models
т.е. создаем ф. или м., который возвращает строку, в которой будет
содержится путь к файлу. В то же время, эти функции должны быть созданы
ДО миграции, и их нельзя будет удалять, пока миграции ссылаются на них.
ПРИМЕР
(! заметь, м. определен выше, чем его объект присваивается атрибуту upload_to)
class MyModel(models.Model):

def upload_to(self):
    return "something dynamic"

my_file = models.FileField(upload_to=upload_to)

для default можно тоже в качестве значения укзаать ссылку на ф.

------------------------------------------------------------------------

для полей можно переопределить ошибки валидации
https://djbook.ru/rel1.9/ref/models/fields.html#error-messages

также у каждого типа полей может быть атрибут validators со списком валидаторов
https://djbook.ru/rel1.9/ref/models/fields.html#validators

------------------------------------------------------------------------

https://djbook.ru/rel1.9/ref/validators.html#module-django.core.validators
Валидатор проверяет поле по каким-либо критериям, если проверка не прошла, то
вызывается ошибка ValidationError

свои валидаторы можно созадть так:
from django.core.validators import ValidationError

def validate_even(value):
    if value % 2 != 0:
        raise ValidationError('%s is not an even number' % value)

а к полю (полю любого типа) можно применить валидатор так:

from django.db import models

class MyModel(models.Model):
    even_field = models.IntegerField(validators=[validate_even])

кроме того, эти же валидаторы можно использовать для форм:

from django import forms

class MyForm(forms.Form):
    even_field = forms.IntegerField(validators=[validate_even])


[ надо попробовать с помощью валидаторов ограничить возможность для одного
вопроса создать и "обычные" ответы и ассоциативные ответы ]


-------------------------------------------------------------------------
https://djbook.ru/rel1.9/ref/models/fields.html#django.db.models.FileField.upload_to
https://docs.djangoproject.com/en/1.10/ref/models/fields/#filefield
Про поля FileField и ImageField, точнее их атрибут upload_to
Он позволяет указать каталог (который будет внутри каталога MEDIA_ROOT), а также
имя файла при его сохранении.

1 способ.  Указать в качестве значения строку. Также поддерживается
форматирование strftime(). Например:
class MyModel(models.Model):
    # file will be uploaded to MEDIA_ROOT/uploads
    upload = models.FileField(upload_to='uploads/')
    # or...
    # file will be saved to MEDIA_ROOT/uploads/2015/01/30
    upload = models.FileField(upload_to='uploads/%Y/%m/%d/')

2 способ.  Написать ф. или м. и в upload_to передать ссылку на этот м./ф.
он должен возвращать строку с путем для сохранения файла и необязательное имя
файла. Папки нужно отделять прямыми слешами ( / ).
Вызываемый объект должен принимать 2 обязательных аргумента (экземпляр модели
и имя файла):
instance - экземпляр модели, в которой определено поле FileField или ImageField.
(внимание! В большинстве случаев объект еще не будет сохранен в базу данных,
и при использовании AutoField, первичный ключ объекта может быть пустым)
filename - оригинальное имя файла (его можно не использовать в самой ф./м.)
Например:
def user_directory_path(instance, filename):
	# запрашиваем у объекта пользователя, у которого запрашиваем id
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'user_{0}/{1}'.format(instance.user.id, filename)

class MyModel(models.Model):
    upload = models.FileField(upload_to=user_directory_path)

------------------------

Как вывести файл, сохраненный с помощью FileField или ImageField:
допустим есть модель MyModel, а у нее есть поле mug_shot=ImageField(...)
тогда, можно получить URL к файлу в шаблоне используя:
{{ instance_of_MyModel.mug_shot.url }}

Если вам нужны название файла или его размер, используй атрибуты name и size
а также path
https://djbook.ru/rel1.9/topics/files.html
тут же есть пример как можно переименовать сохраненный файл и про
API django для работы с файлами
'''
