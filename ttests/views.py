from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, get_list_or_404

from django.urls import reverse

from .models import Test, TestTag, Question

# from django.http import Http404
from django.db.models import Q, Count
# from django.db.models import F

from test4all.settings import SECRET_KEY ###

from django.views.generic import View

from datetime import datetime, timedelta
from django.core import signing

# import json
import random
# Create your views here.

'''
test_detail_url
test_list_url
test_by_tag_url
tag_list_url
'''

class TestList(View):
	def get(self, request):  ### test_list(request):
		# test_list = Test.objects.order_by('title')[:20]
		# только опубликованные тесты
		test_list = Test.objects.filter(is_published=True).order_by('title')[:20]
		# только опубликованные тесты, у которых есть хотя бы 1 вопрос
		# test_list = Test.objects.annotate(Count('questions'))
		# test_list = test_list.filter( Q(questions__count__gte=1) &
		# 								Q(is_published=True) )
		context = {
			'test_list' : test_list,
			'title' : 'Тесты',
			}
		return render(request, 'ttests/test_list.html', context)

	def post(self, request):
		title_part = request.POST.get('search', None)
		test_list = get_list_or_404(Test,
						Q(title__icontains=title_part) & Q(is_published=True) )
		context = {
			'test_list': test_list,
			'title' : 'Поиск по тестам'
		}
		return render(request, 'ttests/test_list.html', context)

class TestDetail(View):
	def get(self, request, id): # test_detail
		test = get_object_or_404(Test, Q(id=id) & Q(is_published=True) )
		# ### сюда бы тоже добавить фильтраци чтобы показывать только тесты,
		# у которых больше 1 вопроса

		# # #########
		# print('\n\ncookies: ', request.COOKIES, '\n\n')
		# sec_val = request.get_signed_cookie(key='sec_tsting', default=None )
		# val = signing.loads(sec_val, key='secret key', salt='some salt')
		# print('sec val from cookie: ', val, '\n\n')
		# # ########
		# sec_val = request.COOKIES.get('sec_testing2', None)
		# val = signing.loads(sec_val, key='secret key', salt='some salt')
		# print('значение из шифрованных, подписанных кук:\n', val)
		# # #######

		context = {
		'test': test,
		'title': 'Детальное описание теста'
		}
		return render(request, 'ttests/test_detail.html', context)


	def post(self, request, id):
		# --------- правильная часть -----------
		test = Test.objects.get(id=id)
		list_questions_id = test.get_all_q_id()

		if not list_questions_id: ###
			return redirect(test)
			# добавить вывод сообщения о том, что нет вопросов
			# или вообще не покаывазть этот тест для прохождения (запретить)

		if test.is_shuffle_q:	# перемешиваем вопросы
			random.shuffle(list_questions_id)
		# выставляем кол-во вопросов тестируемому
		show_q_number = test.show_q_number
		if show_q_number and show_q_number < len(list_questions_id):
			list_questions_id = list_questions_id[:show_q_number]

		next_q = Question.objects.get(id=list_questions_id[0])
		response = redirect(next_q)
		# --------------------------------------

		# # response.set_cookie(key='testing_q', value=list_questions_id) #path=..
		# dict_q_id = {}
		# for i in range(len(list_questions_id)):
		# 	dict_q_id[i] = list_questions_id[i] # хоть так dict_q_id[str(i)] = ...
		#
		# # response.set_signed_cookie(key='testing_q', value=l_q_id,
		# # 							path='/') #### /<test_id>/testing/
		#
		# d = signing.dumps(dict_q_id, key='secret key')
		# response.set_cookie(key='testing_q', value=d)
		#
		# return response

		# проба ---
		l = signing.dumps(list_questions_id, key='secret key')
		response.set_cookie(key='testing_q', value=l)
		return response


		# dict_question_id = request.get_signed_cookie('testing_q', default=None)
		# print('dict of q:   ', dict_question_id)
		# print('type:   ', type(dict_question_id))
		#
		# dict_question_id = json.loads(dict_question_id)
		# print('dict of q:   ', dict_question_id)
		# print('type:   ', type(dict_question_id))
		#
		# if not dict_question_id:
		# 	return redirect(reverse('test_detail_url'))
		# next_q = dict_question_id['0']
		# return redirect(int(next_q))



def tag_list(request):
	tag_list = TestTag.objects.order_by('title')[:]
	# ### сюда бы тоже добавить фильтраци чтобы показывать только тесты,
	# у которых больше 1 вопроса

	context = {
		'tag_list': tag_list,
		'title': 'Тэги',
	}
	return render(request, 'ttests/tag_list.html', context)

def test_by_tag(request, slug): # v
	# test_list = TestTag.tests.filter(test__iexact=tag_title)
	test_list = Test.objects.filter( Q(tags__slug=slug) & Q(is_published=True) )
	context = {
		'test_list': test_list,
		'title': 'Поиск тестов по тегу'
	}
	# return render(request, 'ttests/test_by_tag.html', context)
	return render(request, 'ttests/test_list.html', context)


# а может лучше сделать, чтобы все вопросы выдавались разом?
# тогда и куки по сути не нужны будут и вообще удобнее как в плане
# разработки, так и прохождения теста...
class AnswerTheQuestion(View):					# testing_url
	def get(self, request, question_id):
		q = get_object_or_404(Question, id=question_id)
		a = q.answers.all()
		asa = q.associate_answers.all()

		context = {
			'q': q,
			'answers': a,
			'associate_answers': asa,
			'title': 'тестирование...'
		}

		print(request.COOKIES)

		# last = request.COOKIE.get('testing', None)
		# if not last:
		# 	last = {}
		# last[str(question_id)] = 0 # изменить потом
		response = render(request, 'ttests/question.html', context)
		# response.set_cookie('testing', value=)

		return response

	def post(self, request, question_id):
		# значение одиночного вопроса с одиночным ответом
		last = request.COOKIES.get('testing')
		a_u_o_id = request.POST.get('usr_o_answer') # собтвенный
		a_u_s_text = request.POST.get('usr_s_answer') # одиночный
		a_u_m_ids = request.POST.getlist('usr_m_answer') # множественный


		print(request.COOKIES)
		val = request.COOKIES.get('testing_q')
		print('val:  ', val, type(val))
		list_q_id = signing.loads(val, key='secret key')


		cur_val_index = list_q_id.index(question_id)

		if cur_val_index < len(list_q_id) - 1:
			next_q = list_q_id[cur_val_index + 1]
		else:
			# переход на страницу завершения теста
			return redirect(reverse('ttests:finish_testing_url'))
			# next_q = list_q_id[cur_val_index]
		print('next q:   ', next_q)


		# записываем ответ польозвателя ...

		return redirect(reverse('ttests:testing_url', kwargs={'question_id': next_q} )) ###

def finish_testing(request):
	context = {

	}	# результаты

	return render(request, 'ttests/finish_testing.html', context)


# ================================
# вьюшка созданная с помощью форм
# from .forms import TestForm

def show_static_img(request):
	test = Test.objects.get(id=1)
	return render(request, 'ttests/_stat_file_show.html', context={'test':test})


def get_value_from_form(request):
	if request.method == "POST":
		print('\n\nsigle ans: ', request.POST.get('usr_s_answer') )
		print('own ans: ', request.POST.get('usr_o_answer') )
		print('multi ans: ', request.POST.getlist('usr_m_answer') )
		print('\n\n')
		# есть еще setlist(key, <list>)
		# а также appendlist(key, <item>) # добав. значения по ключу к имеющимся

		print("все из POST: ", request.POST)
		# print(dir(request.POST))

	# ---------- чтение кук ----------
	print('\n\nкуки: ', request.COOKIES)
	# ---- чтение подписанных кук -----
	print('подпис. куки: ',
			request.get_signed_cookie('tsting', default='no sig c'))
	# время жизни кук в браузере устанавливается при установке кук методом
	# response.set_signed_cookie по истечении времени, они удаляются браузером
	# если время не было установлено, то удаляются при закрытии браузера
	#   здесь же можно установить время, которое если пройдет с момента создания\
	# кук, то сервер будет считать их просроченными
	print('подпис. куки с не старше 30 сек: ',
			request.get_signed_cookie('tsting', max_age=30, default='истекли'))
	# ====== создание объекта ответа ========
	response = render(request, 'ttests/_value_in_form.html')
	# print('response:  ', response)
	# --------- установка кук --------
	testing_data = {32: {115:1, 116:0, 117:0, 119:0, 120:1, 121:0}}
	response.set_cookie(key='testing', value=testing_data, max_age=100, path='/6')
	response.set_cookie(key='testing_oneday', value=testing_data, path="/",
					expires=datetime.utcnow()+timedelta(days=1) )
	# response.set_cookie(key, value, max_age=None, expires=None, path="/",
	# 					domain=None, secure=False, httponly=False)
	# ---- установка подписанных кук -----
	response.set_signed_cookie(key='tsting', value=testing_data, path="/")

	# ############ получается, что эти куки подписываются дважды (без надобности)
	testing_security_data = signing.dumps(
						obj=testing_data ,key='secret key', salt='some salt')
	response.set_signed_cookie(key='sec_tsting', value=testing_security_data, )
	# ############ а вот эти зашифрованы и подписаны (то, что нужно)
	response.set_cookie(key='sec_testing2', value=testing_security_data, )
	# ############

	return response

# val = signing.dumps(<obj>, key=None, salt=<salt>,  serializer=django.core.signing.JSONSerializer, compress=False)

''''
# дважды подписанные зашифрованные куки
# signing.dumps() + set_signed_cookie()  =>  get_signed_cookie()
'sec_tsting': 'eyIzMiI6eyIxMTUiOjEsIjExNiI6MCwiMTE3IjowLCIxMTkiOjAsIjEyMCI6MSwiMTIxIjowfX0:1hQKS5:3G4ATNP157bp7WCNAySLkDX3hsM:1hQKS5:QgkqPCYg6ppVWdIk1Nma3DvD6Co'

sec val from cookie:
{'32': {'115': 1, '116': 0, '117': 0, '119': 0, '120': 1, '121': 0}}

# подписанные зашифрованные куки
# signing.dumps() + set_cookie()  =>  COOKIES.get()
'sec_testing2': 'eyIzMiI6eyIxMTUiOjEsIjExNiI6MCwiMTE3IjowLCIxMTkiOjAsIjEyMCI6MSwiMTIxIjowfX0:1hQKS5:3G4ATNP157bp7WCNAySLkDX3hsM'

значение из шифрованных, подписанных кук:
{'32': {'115': 1, '116': 0, '117': 0, '119': 0, '120': 1, '121': 0}}

и кстати, если заморочиться и прописать путь (path) в set_signed_cookie
то можно обойтись без id в  {'32': {'115': 1, '116': 0, ... }}
'''
