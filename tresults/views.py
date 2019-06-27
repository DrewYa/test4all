from django.shortcuts import render, redirect, get_list_or_404
from django.http.response import Http404
from django.views.generic import View
from django.core import signing
from django.urls import reverse

from django.contrib import auth

from .models import TestingResult

from datetime import datetime

# from dateutil import parser as date_parser
# или
# from django.utils import dateparse; dateparse.parse_datetime(date_start)

# from test4all.settings import TIME_ZONE

from .utils import (fill_empty_q_and_processing_results,
					time_testing, link_tresults_with_tags_questions)
from ttests.utils import group_values_by_keys
# Create your views here.

# возможно придется использовать сигнал, который позволяет выполнить действия
# перед отправкой запроса пользователю


def processing_results(request):
	'''\
	Принимает только post-запросы с куками, куда записывались рузельтаты
	во время прохождения теста; парсит эти результаты и заносит в БД. После
	чего перенаправляет на страницу результатов тестирования.
	'''
	# user_id = 3 					########
	user = auth.get_user(request)

	test_id = request.COOKIES.get('test_id')
	secd_q_id = request.COOKIES.get('testing_q_dict')

	# переделать: сделать редирект на стр. с описанием теста
	if not test_id:
		return redirect('/')
	elif not secd_q_id:
		return redirect(reverse('ttests:test_detail_url', kwargs={'id': test_id}))

	# обрабатываем результаты тестирования
	time_complition = datetime.now()
	time_start = request.get_signed_cookie(key='t_start', salt='s29fhs', default=None)
	if time_start:
		time_start = datetime.fromtimestamp( float(time_start) )
	test_time = time_testing(start=time_start, complition=time_complition)

	test_id = int(test_id)
	list_q_id = list( signing.loads(secd_q_id, 'secret key').items() )
	list_q_id = [ int(item[1]) for item in list_q_id ]

	print('time start    ', time_start) # datetime.datetime
	print('time complit  ', time_complition) # datetime.datetime
	print('test time     ', test_time)
	print('list_q_id     ', list_q_id)

	tresult = fill_empty_q_and_processing_results(user=user.id,
	 			test=test_id, questions=list_q_id,
				start=time_start, complition=time_complition)
	# tresult = TestingResult.objects.filter(user__id=user_id,
	# 			test__id=test_id).last()


	# ###### здесь должна быть ф. обработки, чтобы этому TestingResult #####
	# ###### записались определенные QuestionTag'и  ########################
	qtags = link_tresults_with_tags_questions(testing_result=tresult)


	# вместо values исп. list_values - вернет кортеж из кортежей вместо словарей
	qtags = tresult.questions_tags.values('recommendation')
	recommendations = group_values_by_keys(list(qtags), 'recommendation')
	if recommendations:
		recommendations = recommendations.get('recommendation')

	context = {
		'title': 'Результаты тестирования',
		'tresult': tresult,
		'test_time': test_time,
		'recommendations': recommendations,
	}
	response = render(request, 'tresults/results.html', context)
	# response.delete_cookie('test_id')
	response.delete_cookie('testing_q_dict')
	# ...
	return response

	# if request.POST.get('testing_a_dict'):
	# 	secda = request.POST.get('testing_a_dict') # извлекаем словарь с q_id: {'type_answ': answ}
	# else:
	# 	raise Http404
	#
	# # нужно узнать какой пользователь проходит тест
	# # и с ним нужно сопоставить эти результаты тестирования
	# # и записать их в БД
	#
	# response = redirect( "" )
	#
	# return response



def test_results(request, test_id):
	# user_id = 3									######
	user = auth.get_user(request)
	# result = get_list_or_404(TestingResult,
	# 						user__id=user_id, test__id=test_id).last()
	tresult = TestingResult.objects.filter(
							user__id=user.id, test__id=test_id).last()
	if not tresult:
		raise Http404

	test_time = time_testing(start=tresult.date_start, # datetime
	 						complition=tresult.date_complition) # datetime

	qtags = tresult.questions_tags.values('recommendation')
	recommendations = group_values_by_keys(list(qtags), 'recommendation')
	if recommendations:
		recommendations = recommendations.get('recommendation')

	context = {
		'title': 'Результаты последнего тестирования',
		'tresult': tresult,
		'test_time': test_time,
		'recommendations': recommendations,
	}
	return render(request, 'tresults/results.html', context)



"""
# сначала старые, потом новые
TestingResult.objects.filter(Q(user=u), Q(test=t))

# сначала старые, потом новые
TestingResult.objects.filter(Q(user=u), Q(test=t)).order_by('date_complition')

# сначала новые (последние), потом старые
TestingResult.objects.filter(Q(user=u), Q(test=t)).order_by('-date_complition')

# или так (тоже самое - снач. новые, потом стар.) только по id
TestingResult.objects.filter(Q(user=u), Q(test=t)).order_by('-pk')
"""
