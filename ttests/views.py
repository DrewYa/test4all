from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, get_list_or_404

from django.urls import reverse

from .models import Test, TestTag, Question,   User

from django.http import Http404
from django.db.models import Q, Count
# from django.db.models import F

from test4all.settings import SECRET_KEY ###

from django.views.generic import View

from datetime import datetime, timedelta
from django.core import signing

import json
import random

from tresults.models import Testing, TestingAssocAnswer, TestingAnswer, TestingResult
# Testing : user, test, question, score (json)
# Answer :  testing, answer_id, answer_text
# AssocAnswer :  testing, answer_left_id, answer_right_id
# TestingResult : user, test, result, date_coml, date_start, questions_tags

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


def tag_list(request):
	tag_list = TestTag.objects.order_by('title')[:]
	# ### сюда бы тоже добавить фильтраци чтобы показывать только тесты,
	# у которых больше 1 вопроса

	context = {
		'tag_list': tag_list,
		'title': 'Тэги',
	}
	return render(request, 'ttests/tag_list.html', context)

def test_by_tag(request, slug):
	# test_list = TestTag.tests.filter(test__iexact=tag_title)
	test_list = Test.objects.filter( Q(tags__slug=slug) & Q(is_published=True) )
	context = {
		'test_list': test_list,
		'title': 'Поиск тестов по тегу'
	}
	# return render(request, 'ttests/test_by_tag.html', context)
	return render(request, 'ttests/test_list.html', context)

def note_cookies_important(request):
	context = {'title': 'Важно!'}
	return render(request, 'ttests/note_cookies_important.html', context)

# вьюшка чисто для просмотра автором теста как выглядит вопрос при тестировании
def show_question(request, question_id): # , author_id
	# пока не использую - сначала нужно сделать нормальную модель для пользователей
	# q = get_object_or_404(Question, Q(id=question_id) & Q(test__author=author_id))
	q = get_object_or_404(Question, id=question_id)
	a = q.answers.all()
	asa = q.associate_answers.all()

	# если у вопроса есть и обыч. и ассоц. ответы, то выведутся обычные
	context = {
		'q': q,
		'answers': a,
		'associate_answers': asa,
		'title': 'тестирование...'
	}
	return render(request, 'ttests/question.html', context)


class TestDetail(View):
	def get(self, request, id):
		test = get_object_or_404(Test, Q(id=id) & Q(is_published=True) )
		# ### сюда бы тоже добавить фильтраци чтобы показывать
		# только тесты, у которых больше 1 вопроса

		# добавить кнопку "показать результаты" последнего
		# тестирования, если пользователь уже проходил этот тест

		context = {
		'test': test,
		'title': 'Детальное описание теста'
		}
		return render(request, 'ttests/test_detail.html', context)


	def post(self, request, id):
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

		# см словарь с вопросами:  это будет нулевой вопрос
		next_q_number = 0
		response = redirect(reverse('ttests:testing_url',
									kwargs={'q_number': next_q_number}))

		# допустим    list_questions_id = [23, 28, 38, 29, 40]
		# тогда это превратится в {'0': 23, '1': 28, '2': 38, '3': 29, '4': 40}
		d = dict([ (str(num), item) for num, item in enumerate(list_questions_id) ])
		print('словарь вопросов  ', d)

		secd = signing.dumps(d, key='secret key')
		response.set_cookie(key='testing_q_dict', value=secd)

		response.set_cookie(key='test_id', value=id)

		# в таблицу ResultTesting должно записаться время начала
		# тестирования    datetime.utcnow
		time_start = datetime.now()
		start_ = time_start.timestamp()
		response.set_signed_cookie(key='t_start', value=start_, salt='s29fhs')

		return response
		# redirect(reverse('ttests:testing_url', kwargs={'question_id': next_q} ))
		#########




# а может лучше сделать, чтобы все вопросы выдавались разом?
# тогда и куки по сути не нужны будут и вообще удобнее как в плане
# разработки, так и прохождения теста...
class AnswerTheQuestion(View):					  ### testing_url
	def get(self, request, q_number):		### версия со словарем в куках
		secd = request.COOKIES.get('testing_q_dict', None) # номера вопросов
		if not secd: # если такой куки нет
			# стр. с объяснениями, что куки были удалены или не поддерживаются
			return redirect(reverse('ttests:note_cookies_important_url'))
		d = signing.loads(secd, key='secret key')
		# если пользователь ввел в url number вопроса, который не сущ. например 1900
		# ВАЖНО! отриц. значю в url не будут восприниматься как числа,это будет строка
		if str(q_number) not in d:
			len_d = len(d)
			if q_number >= len_d:
				return redirect(reverse('ttests:testing_url',
										kwargs={'q_number': len_d-1}))
		current_q_id = d[str(q_number)]
		# на случай если автор во время прохождения удалит из теста вопрос
		q = get_object_or_404(Question, id=current_q_id)

		# переделать чтобы вместо сущчностей доставались только значения из них
		# id, text, is_right,   id, right_side, left_side
		a = q.answers.all() ##
		asa = q.associate_answers.all().order_by('id') ##

		# перемешиваем варианты ответов
		list_answers = []
		list_assoc_answers = []
		r_list_assoc_answers = [] #
		l_list_assoc_answers = [] #
		sign_idx_asa = None
		if a and a.count() > 1:
			idx_a = list(range( a.count() ))
			random.shuffle(idx_a)
			# print('shuffle idx:  ', idx_a)
			for i in range(len(idx_a)):
				list_answers.append(a[idx_a[i]])
			# в словарь context:   'answers' : list_answers,
			# print('list_answers  ', list_answers)
		# убрать проверку на наличие asa в шаблоне
		elif asa:
			# лист индексов ассоц. ответов упорядоченных по id
			idx_asa = list(range( asa.count() ))
			# d_asa_q = dict( [(i, None) for i in ids_asa ] )
			# перемешиваем
			random.shuffle(idx_asa)
			# порядок в котором будет выводиться правая часть запишем в куки
			sign_idx_asa = signing.dumps(obj=idx_asa[:], key='i29gh394g')
			print('shuffle idx_asa  ', idx_asa)
			for i in range(len(idx_asa)):
				# list_assoc_answers.append(asa[idx_asa[i]])
				r_list_assoc_answers.append(asa[idx_asa[i]])

			l_list_assoc_answers = r_list_assoc_answers[:]
			random.shuffle( l_list_assoc_answers )
			print('\nr_list_assoc_answers  ', r_list_assoc_answers )
			print('\nl_list_assoc_answers  ', l_list_assoc_answers )
			# list_assoc_answers = r_list_assoc_answers

		context = {
			'q' : q,
			# вопросы закоментить, либо убрать из шаблона
			# и сделать здесь
			'answers' : list_answers or a,
			# 'associate_answers' : list_assoc_answers,
			'r_associate_answers' : r_list_assoc_answers,
			'l_associate_answers' : l_list_assoc_answers,
			'title': 'тестирование...',
		}
		response = render(request, 'ttests/question.html', context)
		if sign_idx_asa:
			response.set_cookie(key='asa_rn', value=sign_idx_asa)
		return response


	def post(self, request, q_number): 		### версия со словарем в куках
		secd = request.COOKIES.get('testing_q_dict')
		if not secd: # если такой куки нет
			# стр. с объяснениями, что куки были удалены или не поддерживаются
			return redirect(reverse('ttests:note_cookies_important_url'))
		d = signing.loads(secd, key='secret key')
		# вообще это условие можно не делать, т.к. мы его поставили на GET-запрос
		# а значит пользователь просто не сможет получить документ для того, чтобы
		# его потом отправить POST-запросом. Но пусть будет
		try:
			# понадобится в качестве ключа для словаря в куках, куда будет
			# записываться ответ пользователя
			current_q_id = d[str(q_number)]
		except KeyError:
			Http404
		# делаем остальное уже после того, как проверим, что такой
		# number вопроса есть в словаре "вопросов-id_вопросов"
		next_q_number = q_number + 1
		if next_q_number < 0:
			# показываем нулевой вопрос
			next_q_number = 0
		# # по умолчанию при ответе на вопрос, будет выдан следующий вопрос
		# elif next_q_number < len(d):
		# 	# переходим на следующий вопрос
		# 	next_q_number = q_number + 1
		elif next_q_number > len(d):
			# если больше чем вопросов, показываем этот же (последний) вопрос
			next_q_number = q_number
		# else: # если q_number == len(d)
		# 	# показываем этот же (последний) вопрос
		# 	# думаю, чтобы завершить тестирование пользователю нужно будет
		# 	# самому нажать на кнопку "завершить тестирование"
		# 	next_q_number = q_number

		response = redirect(reverse('ttests:testing_url',
									kwargs={'q_number': next_q_number}))

		# считываем ответ пользователя
		a_u_o_text = request.POST.get('usr_o_answer') # собтвенный
		a_u_s_id = request.POST.get('usr_s_answer') # одиночный
		a_u_m_ids = request.POST.getlist('usr_m_answer') # множественный
		a_u_a_ids = request.POST.getlist('usr_a_answer') #ассоц.доделать!


		# записываем полученные данные в куки
		# (пока идет тестирования все ответы сохраняем в куки)
		secda = request.POST.get('testing_a_dict')
		if secda:
			da = signing.loads(secda, key='secret key')
		else:
			da = {}

		# установка кук в словарь  ...
		# if a_u_o_text:
		# 	da[current_q_id] = {'o': {}}
		# 	da[current_q_id]['o'][answer_id] = a_u_o_text # значение - строка
		# elif a_u_s_id:
		# 	da[current_q_id] = {'s': {}}
		# 	for item_id in a_u_s_id:
		# 		da[current_q_id]['s'][item_id]

		# пока напрямую буду заносить результаты
		test_id = int( request.COOKIES.get('test_id') )
		test = Test.objects.get(id=test_id)
		user = User.objects.get(id=3)
		question = Question.objects.get(id=current_q_id)
		max_point = question.point

		count_answers = question.count_answers()
		count_is_right_answers = question.count_is_right_answers()
		count_associate_answers = question.count_associate_answers()
		user_point = 0
		# автор забыл выставить правильный ответ или вовсе добавить ответы
		if (count_answers == 0 or count_is_right_answers == 0) and \
									count_associate_answers == 0:
			# будет вопрос не будет учтен
			max_point = user_point = 0

		elif count_answers == 1:
			# это вопрос с самостоятельным ответом
			a_u_o_text = a_u_o_text.strip()
			if question.answers.filter(Q(is_right=True) & Q(text__iexact=a_u_o_text)):
				user_point = max_point

		elif count_answers > 1:
			if count_is_right_answers == 1:
				# вопрос с одиночным ответом
				if a_u_s_id:
					a_u_s_id = int(a_u_s_id)
					if question.answers.get(is_right=True).id == a_u_s_id:
						user_point = max_point

			else:
				# вопрос с множественным ответом
				a_u_m_ids = [int(i) for i in a_u_m_ids]
				print('a_u_m_ids  ', a_u_m_ids)
				right_answers = question.answers.filter(is_right=True)
				count_right_a = right_answers.filter(id__in=a_u_m_ids).count()
				count_wrong_a = len(a_u_m_ids) - count_right_a
				k = count_right_a - count_wrong_a
				if k < 0: k = 0
				# print('count_right_a:  ', count_right_a)
				ratio = k / right_answers.count()
				user_point = max_point * ratio
				# делаем 2 цифры после запятой
				user_point = user_point * 100 // 1 / 100
#########################################################################
		elif count_associate_answers:
			# если у вопроса нет обычных ответов, но есть ассоциативные
			# как ответил пользователь
			print('a_u_a_ids (before)  ', a_u_a_ids) # list of str

			a_u_a_ids = [int(i) if i else 0    for i in a_u_a_ids]
			print('a_u_a_ids (after)   ', a_u_a_ids)
			# далее сделать проверку: если все элементы == 0 (т.е. пользователь
			# не отвечал на вопрос), то код по обработке ответа ниже не выполнять
			if sum(a_u_a_ids) != 0:

				# в какой последовательности вопросы выданы пользователю
				# (прав.часть)
				sign_idx_asa = request.COOKIES.get('asa_rn')
				shuffled_idx_asa = signing.loads(sign_idx_asa, key='i29gh394g')
				print('shuffled_idx_asa   ', shuffled_idx_asa)

				# получили правильную последовательность id-шников
				correct_sequence_asa = []
				for item in shuffled_idx_asa:
					correct_sequence_asa.append( a_u_a_ids[item] )
				print('correct_sequence_asa   ', correct_sequence_asa, end="\t")
				print(type(correct_sequence_asa), type(correct_sequence_asa[0]))

				count_right_a = 0
				# теперь сопоставляем
				assoc_ans = question.associate_answers.all().order_by('id')
				for i in range( len(correct_sequence_asa) ):
					if correct_sequence_asa[i] != 0: # 0 - если правая часть None
						print('correct_sequence_asa[i] {}  (!=  0)'.format(
									correct_sequence_asa[i]))
						print(assoc_ans[i].id, correct_sequence_asa[i])

						if assoc_ans[i].id == correct_sequence_asa[i]:
							count_right_a += 1
							print('count_right_a  ', count_right_a)

					else:
						print('{}  ==  0 '.format(correct_sequence_asa[i]))
						pass

				print('count_right_a  ', count_right_a)
				ratio = count_right_a / question.count_right_not_none()
				user_point = max_point * ratio; print('user_point  ', user_point)
				user_point = user_point * 100 // 1 / 100
				print('user_point  ', user_point)
				print('ratio  ', ratio)
#####################################################################33

			# если пользователь не выбрал вариант ответа или ответ поле для
			# ввода не появляллось в случае если right_side == None
			# aid_7 = request.POST.get('7')
			# aid_8 = request.POST.get('8')
			# aid_9 = request.POST.get('9')
			# aid_10 = request.POST.get('10')
			# aid_11 = request.POST.get('11')
			# print(request.POST)
			# print('aids   ', aid_7, aid_8, aid_9, aid_10, aid_11 )
			#
			# asa = question.associate_answers.all()
			# for item in range(count_associate_answers):
			# 	# значит right_side не None
			# 	if str( item.id ) in request.POST:
			# 		pass


		score = json.dumps( {max_point: user_point} )
		testing, is_not_exist = Testing.objects.update_or_create(
				user=user, test=test, question=question,
				defaults={'score': score}  )

		response.set_cookie(key='testing_a_dict', value=secda)
		return response


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

# для создания сложных вопросов, нужна агрегация
# https://docs.djangoproject.com/en/2.0/topics/db/aggregation/#filtering-on-annotations


'''
from django.core.paginator import Paginator

tests = Test.objects.all()
paginator = Paginator(test, 2) # по 2 теста на страницу

dir(paginator)
['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_check_object_list_is_ordered', '_get_page', 'allow_empty_first_page', 'count', 'get_page', 'num_pages', 'object_list', 'orphans', 'page', 'page_range', 'per_page', 'validate_number']

page1 = paginator.get_page(1)

dir(page1)
['__abstractmethods__', '__class__', '__contains__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__reversed__', '__setattr__', '__sizeof__', '__slots__', '__str__', '__subclasshook__', '__weakref__', '_abc_cache', '_abc_negative_cache', '_abc_negative_cache_version', '_abc_registry', 'count', 'end_index', 'has_next', 'has_other_pages', 'has_previous', 'index', 'next_page_number', 'number', 'object_list', 'paginator', 'previous_page_number', 'start_index']

page1.object_list  # 2 первых теста из всех тестов

https://www.youtube.com/watch?v=RpUf503bFc8&list=PLlWXhlUMyooaDkd39pknA1-Olj54HtpjX&index=14
'''
