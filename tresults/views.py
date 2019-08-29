from datetime import datetime

from django.shortcuts import render, redirect, get_list_or_404
from django.http.response import Http404
from django.views.generic import View
from django.core import signing
from django.urls import reverse
from django.contrib import auth

from ttests.utils import group_values_by_keys

from .models import TestingResult
from .utils import (fill_empty_q_and_processing_results,
					link_tresults_with_tags_questions,
					time_testing,)

# Create your views here.

def processing_results(request):
	'''
	Принимает только post-запросы с куками, куда записывались рузельтаты
	во время прохождения теста; парсит эти результаты и заносит в БД. После
	чего перенаправляет на страницу результатов тестирования.
	'''
	user = auth.get_user(request)
	test_id = request.COOKIES.get('test_id')
	secd_q_id = request.COOKIES.get('testing_q_dict')

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
	list_q_id = list(signing.loads(secd_q_id, 'secret key').items())
	list_q_id = [int(item[1]) for item in list_q_id]

	tresult = fill_empty_q_and_processing_results(user=user.id,
	 			test=test_id, questions=list_q_id,
				start=time_start, complition=time_complition)
	# tresult = TestingResult.objects.filter(user__id=user_id,
	# 			test__id=test_id).last()

	# записываем рузультату теста теги вопросов
	qtags = link_tresults_with_tags_questions(testing_result=tresult)

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
	response.delete_cookie('test_id') #
	response.delete_cookie('testing_q_dict')

	return response


def test_results(request, test_id):
	user = auth.get_user(request)
	# result = get_list_or_404(TestingResult,
	# 						user__id=user_id, test__id=test_id).last()
	tresult = TestingResult.objects.filter(
							user__id=user.id, test__id=test_id).last()
	if not tresult:
		raise Http404

	test_time = time_testing(start=tresult.date_start, complition=tresult.date_complition)

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
