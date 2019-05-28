from django.shortcuts import render, redirect
from django.http.response import Http404
from django.views.generic import View
from django.core import signing
from django.urls import reverse

from datetime import datetime
# from test4all.settings import TIME_ZONE

# from .models import TestingResult

from .utils import fill_empty_q_and_processing_results, time_testing
# Create your views here.


# возможно придется использовать сигнал, который позволяет выполнить действия
# перед отправкой запроса пользователю


def processing_results(request):
	'''\
	Принимает только post-запросы с куками, куда записывались рузельтаты
	во время прохождения теста; парсит эти результаты и заносит в БД. После
	чего перенаправляет на страницу результатов тестирования.
	'''

	test_id = request.COOKIES.get('test_id')
	secd_q_id = request.COOKIES.get('testing_q_dict')

	if test_id and not secd_q_id:
		return redirect(reverse('ttests:test_detail_url',
		 						kwargs={'id': test_id}))
		# вместо этого сделать редирект на страницу с описанием
		# теста и сделать там кнопку "посмотреть результаты"
	if not test_id:
		return redirect('/')

	user_id = 3

	test_id = int(test_id)
	list_q_id = list( signing.loads(secd_q_id, 'secret key').items() )
	list_q_id = [ int(item[1]) for item in list_q_id ]
	print('list_q_id   ', list_q_id)

	# обрабатываем результаты тестирования
	time_start = request.get_signed_cookie(key='t_start', salt='s29fhs',
											default=None)
	if time_start:
		time_start_ = datetime.fromtimestamp( float(time_start) )
	time_complition = datetime.now()

	result = fill_empty_q_and_processing_results(user=user_id,
	 			test=test_id, questions=list_q_id,
				start=time_start_, complition=time_complition)
	test_time = time_testing(start=time_start_, complition=time_complition)
	print(test_time)

	context = {
		'title': 'Результаты тестирования',
		'result': result,
		'test_time': test_time,
		# 'questions_tags' : ...
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
