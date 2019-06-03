from ttests.models import Test, Question, User, QuestionTag
from tresults.models import Testing, TestingResult
import json
from datetime import datetime
from re import compile as re_compile, findall as re_findall

# from django import utils
# from django.utils import dateparse

# def time_testing2(start=None, complition=None):
# 	'''	strart, complition - str in format  2019-05-28 20:05:10.829637+00:00'''
# 	start = start.split('.')[0]
# 	complition = complition.split('.')[0]
# 	start = datetime.strptime(complition, '%Y-%m-%d %H:%M:%S')
# 	complition = datetime.strptime(complition, '%Y-%m-%d %H:%M:%S')

from ttests.utils import (extract_json_score, place_json_score,
						extract_score, place_score,
						group_values_by_keys)

def convert_str_to_datetime(s=None):
	'''
	get s (str) in format "YYYY-mm-DD HH:MM:SS"+"other..."
	or obj datetime.datetime;    return datetime.datetime
	if s not str and not datetime.datetime then return None
	'''
	if type(s) is datetime:
		return s
	if type(s) is str:
		dt_from_s = datetime.strptime(s.split('.')[0], r'%Y-%m-%d %H:%M:%S')
		return dt_from_s
	else:
		return None
		# try:
		# 	dt_from_s = datetime.strptime(s.split('.')[0], r'%Y-%m-%d %H:%M:%S')
		# except ValueError:
		# 	# получ. tuple: дата_время, микросекунды, оклонение_относительно_utc
		# 	pattern = re_compile(
		# 	(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.(\d{6})(\+\d{2}:\d{2})') )
		# 	date_time, ms, time_zone = re_findall(pattern, s)[0]
		# 	dt_from_s = datetime.strptime(date_time, r'%Y-%m-%d %H:%M:%S')


def time_testing(start=None, complition=None):
	'''\
	start - datetime.datetime, complition - datetime.datetime
	возвращает разницу в виде кортежа (hours, minutes, seconds)
	возможен вариант, когда start и/или complition -
	str в формате 2019-05-28 20:05:10.829637+00:00
	'''
	if start and complition:
		start = convert_str_to_datetime(start)
		complition = convert_str_to_datetime(complition)
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

	list_testings = []
	max_points = 0
	user_points = 0.0
	for q in questions:
		testing, created = Testing.objects.get_or_create(
							user=u, test=t, question=q)
		list_testings.append(testing)
		# если пользователь НЕ отвечал на вопрос, смотрим score у вопроса
		if created:
			max_q_point = q.point
			user_point = 0
			# score = place_json_score(max_q_point, user_point)
			score = place_score(user_point, max_q_point)
			testing.score = score
			testing.save()
			max_points += max_q_point
			# user_points += user_point - не требуется

		# если пользователь уже отвечал на вопрос, вытаскиваем score
		elif not created:
			# max_q_point, user_point = extract_json_score(testing.score)
			user_point, max_q_point = extract_score(testing.score)
			max_points += max_q_point
			user_points += user_point

	print('list_testings ', list_testings)
	result = round( user_points / max_points * 100 )

	if complition and start:
		# вместо update_or_create использовать create
		tr, created = TestingResult.objects.update_or_create(user=u, test=t,
						defaults={'date_start': start,
								'date_complition': complition,
								'result': result})
	elif complition:
		tr, created = TestingResult.objects.update_or_create(user=u, test=t,
						defaults={'date_complition': complition,
								'result': result})
	else:
		tr, created = TestingResult.objects.update_or_create(user=u, test=t,
						defaults={'result': result})

	tr.testings.add(*list_testings)
	tr.save()
	return tr


# функции для обработки результатов и вывода тегов вопросов, на которые был
# дан неудовлетворительные ответы

def link_tresults_with_tags_questions(testing_result=None):
	"""
	obj TestingResult -> list of obj QuestionTag

	1) в функцию передается id результата тестирования, по которому нужно узнать
	ответы (подробные рез.)
	2) запрашиваем все подробные результаты (нужны их знач. score)
	3) выбираем вопросы, баллы за которые <= 57% от максимального
	4) запрашиваем все теги по этим вопросам (без повторений)
	5) для каждого тега:
	     смотрим сколько для тега определенов вопросов
	     смотрим сколько было дано плохих ответов
	     (правильность меньше 57% от макс балла)
	     считаем отношение кол-во_плохих_вопросов(ответов)/кол-во_вопросов
	       если для тега определено 1-2 вопроса, то порог для показа >= 50%
	       если определено 3-9 вопросов, то порог >= 37%
	       если 9-18, то порог >= 25%
	       иначе (если вопросов 19 и больше), то порог 23%
	          добавляем тег в список
	6) связываем список тегов с TestingResult
	7) возвращаем список тегов вопросов
	"""
	if not testing_result:
		return None

	tr = testing_result

	# tr.questions_tags.remove( ) - Требует именно объект(ы), а не QuerySet
	tr.questions_tags.clear() # отвязываем все связанные теги
	# не требуется:  clear, add, remove, create делают запрос и сразу сохраняют
	# tr.save()

	values_testings = tr.testings.values('id', 'score')
	group_values_tings = group_values_by_keys(list(values_testings), 'id', 'score')
	print ('values ', values_testings)
	print('converted ', group_values_tings)

	list_ids_bad_tings = []
	# получаем список id'шников подробных результатов, на которые пользователь
	# ответил плохо
	scores = group_values_tings.get('score')
	ids = group_values_tings.get('id')
	for i in range(len(scores)):
		usr, max = extract_score( scores[i] )
		try: k = usr / max
		except ZeroDivisionError: k = 1
		if k <= 0.57: # ratio of badness of answer
			list_ids_bad_tings.append(ids[i])

	# нет плохих ответов, дальше выполнять нет смысла
	if not list_ids_bad_tings:
		return None

	print(list_ids_bad_tings)

	# получаем список id'шников вопросов
	list_ids_bad_q = Question.objects.filter(
			testings__id__in=list_ids_bad_tings).values_list('id')
	if list_ids_bad_q:
		list_ids_bad_q = [ item[0] for item in list(list_ids_bad_q) ]

	# получаем список тегов по этим вопросам
	# prefetch_related позволяет уменьш. кол-во запросов, не знаю верно ли написал
	# https://djbook.ru/rel1.9/ref/models/querysets.html#prefetch-related
	tags = QuestionTag.objects.filter(
			questions__id__in=list_ids_bad_q).prefetch_related('questions')

	# если тегов не определено для вопросо - продолжать бессмысленно
	if not tags:
		return None

	list_needed_tags = []
	for tag in tags:
		count_q = tag.questions.count()
		count_bad_q = tag.questions.filter(id__in=list_ids_bad_q).count()
		# ratio of bad answer regarding the total count questions of tag
		ratio = count_bad_q / count_q
		if count_bad_q <= 2 and ratio >= 0.50:
			list_needed_tags.append(tag)
		elif count_bad_q <= 9 and ratio >= 0.37:
			list_needed_tags.append(tag)
		elif count_bad_q <= 18 and ratio >= 0.25:
			list_needed_tags.append(tag)
		elif count_bad_q > 18 and ratio >= 0.23:
			list_needed_tags.append(tag)
		print('count bad q ', count_bad_q, '  count_q  ', count_q)
		print('ratio  ', ratio)
		print('list tags  ', list_needed_tags)

	# связываем полученные теги с этим результатом тестирования
	tr.questions_tags.add( *list_needed_tags )
	# tr.save() # не требуется, т.к. add делает запрос и сразу сохраняет

	return list_needed_tags

# если уже после того как пользователь протестируется, автор решит добавить теги,
# нужно еще раз запустить эту ф., чтобы новые теги добавились
