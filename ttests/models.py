import os

from django.db import models
from django.db.models import Q
from django.shortcuts import reverse
from django.contrib.auth.models import User

from django.core.exceptions import ValidationError

from .validators import min_length_1
from .utils import list_from_dict_values

# Create your models here.

class TestTag(models.Model):
	class Meta:
		verbose_name = 'Тег теста'
		verbose_name_plural = 'Теги теста'
		ordering = ('title',)
		managed = True # позволяет удал. табл из БД

	title = models.CharField(max_length=50, unique=True,
							verbose_name='название')
	slug = models.SlugField(max_length=50, unique=True,
							verbose_name='ссылка',   blank=True)

	def get_absolute_url(self):
		return reverse('ttests:test_by_tag_url', kwargs={'slug': self.slug})

	def count_published_test(self):
		return self.tests.filter(is_published=True).count()

	def __str__(self):
		return self.title


class Test(models.Model):
	'''
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
		verbose_name = ' Тест'
		verbose_name_plural = ' Тесты'
		# ordering = ('title',)
		managed = True

	def user_directory_path(self, filename):
		# MEDIA_ROOT/user_<id>/<filename>
		return 'user_{0}/{1}'.format(self.author.id, filename)

	title = models.CharField(max_length=140, verbose_name='название теста')
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
	author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
					related_name='tests' )
	tags = models.ManyToManyField(to='TestTag', related_name='tests', blank=True,
					verbose_name='теги для теста',
					help_text='Это позволит быстрее найти тест среди других.')
	create_date = models.DateTimeField(auto_now=False, auto_now_add=True,
	 				db_index=True, verbose_name='дата создания')
	update_date = models.DateTimeField(auto_now=True, auto_now_add=False,
	 				db_index=True, verbose_name='последнее редактирование')
	testing_time = models.DurationField(null=True, blank=True,
					verbose_name='время тестирования',
					help_text='в формате ЧЧ:ММ:СС')
	show_q_number = models.PositiveSmallIntegerField(null=True, blank=True,
					verbose_name='количество вопросов',
					help_text='пользователю будет показано столько вопросов.\
					В действительности тест может иметь больше вопросов',
					validators=[min_length_1])
	is_shuffle_q = models.BooleanField(default=False,
					verbose_name='перемешать вопросы?',
					help_text='вопросы будут идти не по порядку')
	only_fully_correct = models.BooleanField(default=False,
					verbose_name='только 100% верные ответы',
					help_text='засчитывать только полностью верные ответы\
					(для вопросов с множественными и ассоциативными ответами)\
					иначе будет вычислен балл для частично правильных ответов')
	# не создавать - будет браться из значения поля id для теста
	# slug = models.SlugField

	def get_absolute_url(self):
		return reverse('ttests:test_detail_url', kwargs={'id': self.id})

	def count_q_to_answer(self):
		s_q_n = self.show_q_number
		real_q_count = self.questions.count()
		if s_q_n is not None:
			if s_q_n < 1 and real_q_count > 0:  return 1
			elif s_q_n < 1 and real_q_count == 0:  return 0
			elif s_q_n <= real_q_count:  return s_q_n
		return real_q_count

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
							verbose_name='для вопроса', blank=True)
	# убрать поле из админки, сделать автоматическое заполнение
	# наверно с помощью "сигналов"
	# а вообще нужно ли оно? (если тест удалить, то его вопросы, а значит и теги
	# тоже. Делал для того, чтобы у каждого теста были уникальный набор тегов и
	# не было ситуации, что один и тот же тег применялся к разным тестам с вопросами)
	test = models.ForeignKey(to='Test', on_delete=models.CASCADE,
							related_name='questions_tags')

	def get_3_questions(self):
		q3 = list( self.questions.values('text')[:3] )
		dict_values = list_from_dict_values(q3, 'text')
		return dict_values.get('text', None)

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
	explanation = models.TextField(blank=True, max_length=1000,
							verbose_name='пояснение ответа')
	# штраф за неверно отвеченный ответ
	# fine = 	models.PositiveSmallIntegerField(blank=True, null=True,
	# 			help_text='сколько баллов будет вычтено за неправильный ответ')

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



# --------------- сигналы ----------------

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
