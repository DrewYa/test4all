from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Testing(models.Model):	# прохождение теста
	class Meta:
		verbose_name = 'Подробный результат тестирования'
		verbose_name_plural = 'Подробные результаты тестирования'
		managed = True
	# потом удалить поля user и test, т.к. эти поля уже есть у TestingResult,
	# связанной с этой моделью
	user = models.ForeignKey(to=User, on_delete=models.CASCADE,
				related_name='testings',
				verbose_name='тестируемый')
	test = models.ForeignKey(to='ttests.Test', on_delete=models.SET_NULL,
				null=True, related_name='testings',
				verbose_name='тест')
	question = models.ForeignKey(to='ttests.Question',
				null=True, on_delete=models.SET_NULL, related_name='testings',
				verbose_name='вопрос')
	score = models.CharField(max_length=27,
				verbose_name='балл',
				help_text='в формате набранный балл / максимальный балл')
	testing_result = models.ForeignKey('TestingResult', on_delete=models.SET_NULL,
				null=True, related_name='testings')

	# def __repr__(self):
	# 	return 'u: {}, t.id: {}, q.id: {}'.format(
	# 								self.user.id, self.test.id, self.question.id)

class TestingAssocAnswer(models.Model):
	class Meta:
		verbose_name = 'Ассоциативный ответ пользователя'
		verbose_name_plural = 'Ассоциативные ответы пользователя'
		managed = True

	testing = models.ForeignKey(to='Testing', on_delete=models.CASCADE,
				related_name='associate_answers')
	answer_left_id = models.IntegerField()
	answer_right_id = models.IntegerField()

class TestingAnswer(models.Model):
	class Meta:
		verbose_name = 'Ответ пользователя'
		verbose_name_plural = 'Ответы пользователя'
		managed = True

	testing = models.ForeignKey(to='Testing', on_delete=models.CASCADE,
				related_name='answers')
	answer_id = models.IntegerField(null=True, blank=True)
	answer_text = models.TextField(null=True, blank=True)


class TestingResult(models.Model):		# краткие результаты тестирования
	class Meta:
		verbose_name = ' Результат тестирования'
		verbose_name_plural = ' Результаты тестирования'
		managed = True

	user = models.ForeignKey(to=User, on_delete=models.CASCADE,
				related_name='testing_results',
				verbose_name='тестируемый')
	test = models.ForeignKey(to='ttests.Test', on_delete=models.SET_NULL,
				null=True, related_name='testing_results',
				verbose_name='тест')
	result = models.PositiveSmallIntegerField(verbose_name='итоговый балл') # 0 - 100 (%)
	date_complition = models.DateTimeField(db_index=True,
				verbose_name='завершение тестирования')
	date_start = models.DateTimeField(db_index=True,
				verbose_name='начало тестирования')
	questions_tags = models.ManyToManyField(to='ttests.QuestionTag',
				related_name='testings_results', blank=True,
				verbose_name='теги вопросов',
				help_text='рекомендации из этих тегов будут показаны пользователю')

	def __repr__(self):
		return 't.id: {}, u.id: {}, id: {}'.format(self.test.id, self.user.id, self.id)

# ------------------------------------------------------------

# по поводу Meta.managed = True
# https://djbook.ru/rel1.9/ref/models/options.html#django.db.models.Options.managed
