from django.db import models

# Create your models here.

class Testing(models.Model):	# прохождение теста
	class Meta:
		verbose_name = 'Подробный результат тестирования'
		verbose_name_plural = 'Подробные результаты тестирования'
		managed = True

	user = models.ForeignKey(to='ttests.User', on_delete=models.CASCADE,
				related_name='testings')
	test = models.ForeignKey(to='ttests.Test', on_delete=models.SET_NULL,
				null=True, related_name='testings')
	question = models.ForeignKey(to='ttests.Question',
				null=True, on_delete=models.SET_NULL, related_name='testings')
	score = models.CharField(max_length=27) # json

	# def __repr__(self):
	# 	return 'пользователь: {}, тест {}'.format( self.user, self.test)

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
		verbose_name = 'Краткий результат тестирования'
		verbose_name_plural = 'Краткие результаты тестирования'
		managed = True

	user = models.ForeignKey(to='ttests.User', on_delete=models.CASCADE,
				related_name='testing_results')
	test = models.ForeignKey(to='ttests.Test', on_delete=models.SET_NULL,
				null=True, related_name='testing_results')
	result = models.PositiveSmallIntegerField() # 0 - 100 (%)
	date_complition = models.DateTimeField(db_index=True)
	date_start = models.DateTimeField(db_index=True)
	# все-таки связь многие-ко-многим  (у одного результата может быть много
	# тегов, а у один тег может быть применен к многим результатам)
	questions_tags = models.ForeignKey(to='ttests.QuestionTag',
				null=True, on_delete=models.SET_NULL,
				related_name='testing_results')
