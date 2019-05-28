from ttests.models import Test, Question, User
from .models import Testing, TestingResult
import json
from datetime import datetime

def time_testing(start=None, complition=None):
	'''\
	start - datetime.datetime, complition - datetime.datetime
	возвращает разницу в виде кортежа (hours, minutes, seconds)
	'''
	if start and complition:
		delta = complition - start # datetime.timedelta
		delta_sec = delta.total_seconds()
		hours = int( delta_sec // 3600 )
		minutes = int( (delta_sec - 3600 * hours) // 60 )
		seconds = round(delta_sec - hours * 3600 - minutes * 60)
		return hours, minutes, seconds
	return None

def fill_empty_q_and_processing_results(user=None, test=None, questions=None,
										start=None, complition=None):
	'''\
	принимает объект пользователя для кого будут заполнены результаты;
	тест, который проходит пользователь; список вопросов, на которые
	пользователю нужно ответить
	questions - list of ids (int); u - id of user (int); t - id of test(int)
	start - datetime.datetime, complition - datetime.datetime
	записывает нули в ответы, на которые не стал отвечать пользователь
	возвращает результат тестирования ( 0 - 100 )
	и время прохождения теста
	'''
	u = User.objects.get(id=user)
	t = Test.objects.get(id=test)
	questions = Question.objects.filter(id__in=questions) # QuerySet

	if complition:
		if start:
			TestingResult.objects.update_or_create(user=u, test=t,
				defaults={'date_start': start, 'date_complition': complition})
			print(start, complition) ###
		else:
			TestingResult.objects.update_or_create(user=u, test=t,
				defaults={'date_complition': complition})

	max_points = 0
	user_points = 0.0
	for q in questions:
		testing, created = Testing.objects.get_or_create(
							user=u, test=t, question=q)
		# если пользователь НЕ отвечал на вопрос, смотрим score у вопроса
		if created:
			# pass
			max_q_point = q.point
			user_point = 0
			score = json.dumps( {max_q_point: user_point} )
			testing.score = score
			testing.save()
			max_points += max_q_point
			# user_points += user_point

		# если пользователь уже отвечал на вопрос, вытаскиваем score
		elif not created:
			# pass
			score = json.loads(testing.score)
			val = list(score.items() )[0]
			max_points += int(val[0])
			user_points += float(val[1])

	result = round( user_points / max_points * 100 )
	TestingResult.objects.update_or_create(user=u, test=t,
							defaults={'result': result})
	return result
