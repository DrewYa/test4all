import json
import random
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, get_list_or_404
from django.urls import reverse
from django.http import Http404
from django.views.generic import View
from django.core import signing
from django.db.models import Q, Count # , F

# from django.contrib.auth import login, authenticate, logout
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .forms import CustomUserCreationForm

from test4all.settings import SECRET_KEY ###

from tresults.models import Testing, TestingAssocAnswer, TestingAnswer, TestingResult
from .models import Test, TestTag, Question,   User
from ttests.utils import place_score, place_json_score, add_to_simple_users_group

FINISH_TEST_AFTER_LAST_QUESTION = True
COOKIES_ENCRYPT_KEY_FOR_VALUES = 'secret key' # for secda
SALT_TO_ENCRYPT_VALUES_DICT_QUESTIONS_ID = None # for secda
SIGNING_KEY_FOR_INDEX_ASSOC_ANSWERS = None #sign_idx_asa
SALT_TO_SINGING = None
SALT_TO_SIGNING = None

'''
еще сделать:
* в детальном описании к тесту - количество вопросов, если пользователь
* запись пользовательских ответов во время тестирования
* просмотр подробных результов тестирования
* таймер обратного отсчета до завершения теста и автозавершение тестирования,
  при истечении времени на тестирование
* больше AJAX-запросов (для экономии трафика и скорости ответа)

* очищать ненужные куки
* пагинацию при выдаче списка всех тестов
* страницу, где пользователь может посмотреть какие тесты он прошел
  (наверно можно сделать на основе вьюшке test list)
* страницу с описанием, как пользоваться сайтом
* добавление к вопросу либо ассоциативных ответов, либо обычных (а не как сейчас)
* если пользователь не добавил ни одного варианта ответа (никакого вида),
  то при тестировании пропускать этот вопрос (redirect на следующий вопрос)
* модель пользователей на основе django auth
* регистрация новых пользователей
* требование авторизации для доступа к опр. страницам
* просмотр пользователями только тех сущностей всех моделей, которые создали они,
  а не все имеющиеся, кроме тегов тестов
* уникальный для каждого теста теги вопросов
* приведение наименований тегов теста к нижнему регистру и проверка на
  уникальность наименований (и слагов)
* отображение загруженных картинок (для теста или вопроса)
* поле, где хранится путь до папки пользователя
  (где будут сохр. все загруженные им файлы)
* оптимизация всех запросов к БД
  (где-то можно обойтись использованием values или values_list,
   где-то сделать aggregate/annotate, где-то
  где-то применить select_related или prefetch_related, only или defer и т.д. )
* более умную систему для показа рекомендаций из тегов вопросов
* усовершенствовать поиск по тестам

v * минимальный балл может быть нулевым и это должно нормально отрабатываться
'''

# Create your views here.

class TestList(View):
	def get(self, request):
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


# если для теста не определено вопросов, то не показывать его пользователям
# для прохождения
class TestDetail(View):
	# @login_required
	def get(self, request, id):
		test = get_object_or_404(Test, Q(id=id) & Q(is_published=True) )
		# ### сюда бы тоже добавить фильтраци чтобы показывать
		# только тесты, у которых больше 1 вопроса

		user_id = 3
		tresults = test.testing_results.filter(user__id=user_id).count()

		context = {
		'test': test,
		'is_exist_results': tresults,
		'title': 'Детальное описание теста'
		}
		return render(request, 'ttests/test_detail.html', context)


	def post(self, request, id):
		test = Test.objects.get(id=id)
		list_questions_id = test.get_all_q_id()			# оптимизировать метод

		# если для теста не определено вопросов
		if not list_questions_id:
			return redirect(test)

		# перемешиваем вопросы
		if test.is_shuffle_q:
			random.shuffle(list_questions_id)

		# выставляем кол-во вопросов тестируемому
		list_questions_id = list_questions_id[:test.count_q_to_answer()]

		# см словарь с вопросами:  это будет нулевой вопрос
		next_q_number = 0
		response = redirect(reverse('ttests:testing_url',
									kwargs={'q_number': next_q_number}))
		response.set_cookie(key='test_id', value=id)

		# устанавливаем в куки словарь из списка вопросов для тестирования
		# допустим    list_questions_id = [23, 28, 38, 29, 40]
		# тогда это превратится в {'0': 23, '1': 28, '2': 38, '3': 29, '4': 40}
		d = dict([ (str(num), item) for num, item in enumerate(list_questions_id) ])
		secd = signing.dumps(d, key='secret key')
		response.set_cookie(key='testing_q_dict', value=secd)

		# фиксируем время начала тестирования и записываем в куки
		# datetime.utcnow
		time_start = datetime.now()
		start_ = time_start.timestamp()
		response.set_signed_cookie(key='t_start', value=start_, salt='s29fhs')

		print('словарь вопросов  ', d)
		return response


# а может лучше сделать, чтобы все вопросы выдавались разом?
# тогда и куки по сути не нужны будут и вообще удобнее как в плане
# разработки, так и прохождения теста...
class AnswerTheQuestion(View):					  		# testing_url
	def get(self, request, q_number):
		q_number = str(q_number)
		# номера вопросов
		secd = request.COOKIES.get('testing_q_dict', None)
		# если такой куки нет - redirect на стр. с объяснением важности кук
		if not secd:
			return redirect(reverse('ttests:note_cookies_important_url'))

		d = signing.loads(secd, key='secret key')
		# если пользователь ввел в url number вопроса, который не сущ.; прим: 1900
		# отриц. знач. в url не будут восприниматься как числа, это будет строка
		# и будет возвращаться ошибка 404
		if q_number not in d:
			# if FINISH_TEST_AFTER_LAST_QUESTION and int(q_number) == len(d):
			# 	return redirect(reverse('tresults:processing_results_url'))
			### len_d = len(d); # if int(q_number) >= len_d:
			return redirect(reverse('ttests:testing_url',
										kwargs={'q_number': len(d)-1}))

		# на случай если автор во время прохождения удалит из теста вопрос
		current_q_id = d[q_number]
		try:
			q = Question.objects.get(id=current_q_id)
		except Question.DoesNotExist:
			test_id = request.COOKIES.get('test_id', '')
			return redirect(reverse('ttests:test_detail_url', kwargs={'id':test_id}))

		# переделать чтобы вместо сущностей доставались только значения из них
		# id, text, is_right,   id, right_side, left_side
		a = q.answers.all() 						# оптимизировать ( values )
		asa = q.associate_answers.all().order_by('id')# оптимизировать ( values )

		# перемешиваем варианты ответов
		list_answers = []
		list_assoc_answers = []
		r_list_assoc_answers = [] #
		l_list_assoc_answers = [] #
		sign_idx_asa = None
		if a and a.count() > 1:
			idx_a = list(range( a.count() ))
			random.shuffle(idx_a)
			for i in range(len(idx_a)):
				list_answers.append(a[idx_a[i]])
			# в словарь context:   'answers' : list_answers,
			# print('shuffle idx:  ', idx_a)
			# print('list_answers  ', list_answers)
		# убрать проверку на наличие asa в шаблоне
		elif asa:
			# d_asa_q = dict( [(i, None) for i in ids_asa ] )
			# лист индексов ассоц. ответов упорядоченных по id
			idx_asa = list(range( asa.count() ))
			# перемешиваем
			random.shuffle(idx_asa)
			# порядок в котором будет выводиться правая часть запишем в куки
			sign_idx_asa = signing.dumps(obj=idx_asa[:], key='i29gh394g')
			for i in range(len(idx_asa)):
				r_list_assoc_answers.append(asa[idx_asa[i]])

			l_list_assoc_answers = r_list_assoc_answers[:]
			random.shuffle( l_list_assoc_answers )
			print('shuffle idx_asa  ', idx_asa)
			print('\nr_list_assoc_answers  ', r_list_assoc_answers )
			print('\nl_list_assoc_answers  ', l_list_assoc_answers )

		context = {
			# вопросы закоментить, либо убрать из шаблона и сделать здесь
			'q' : q,
			'answers' : list_answers or a,
			'r_associate_answers' : r_list_assoc_answers,
			'l_associate_answers' : l_list_assoc_answers,
			'title': 'тестирование...',
		}
		response = render(request, 'ttests/question.html', context)
		if sign_idx_asa:
			response.set_cookie(key='asa_rn', value=sign_idx_asa)
		print('словарь вопросов  ', d)
		return response


	def post(self, request, q_number):
		# куки с id'шниками вопросов
		secd = request.COOKIES.get('testing_q_dict')
		# если куки нет - redirect на страницу про куки
		if not secd:
			return redirect(reverse('ttests:note_cookies_important_url'))
		d = signing.loads(secd, key='secret key')
		# если пользователь послал POST на несуществующий номер вопроса
		# можно не делать, т.к. поставили это условие на GET-запрос
		try:  current_q_id = d[str(q_number)]
		except KeyError:  raise Http404

		# по умолчанию при ответе на вопрос, переходим на следующий вопрос
		next_q_number = q_number + 1
		if FINISH_TEST_AFTER_LAST_QUESTION and next_q_number == len(d):
			response = redirect(reverse('tresults:processing_results_url'))
		# если больше чем вопросов, показываем последний вопрос
		else:
			if next_q_number > len(d):
				next_q_number = q_number
			response = redirect(
				reverse('ttests:testing_url', kwargs={'q_number': next_q_number}))


		# считываем ответ пользователя
		a_u_o_text = request.POST.get('usr_o_answer')		# собтвенный
		a_u_s_id = request.POST.get('usr_s_answer')			# одиночный
		a_u_m_ids = request.POST.getlist('usr_m_answer')	# множественный
		# list of str
		a_u_a_ids = request.POST.getlist('usr_a_answer')	# ассоц.доделать!


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
		# на случай если автор во время прохождения удалит из теста вопрос
		try:
			question = Question.objects.get(id=current_q_id)
		except Question.DoesNotExist:
			test_id = request.COOKIES.get('test_id', '')
			return redirect(reverse('ttests:test_detail_url', kwargs={'id':test_id}))
		max_point = question.point

		count_answers = question.count_answers()
		count_is_right_answers = question.count_is_right_answers()
		count_associate_answers = question.count_associate_answers()
		user_point = 0
		# автор забыл выставить правильный ответ или вовсе добавить ответы
		# вопрос не будет учтен
		if (count_answers == 0 or count_is_right_answers == 0) and \
									count_associate_answers == 0:
			max_point = user_point = 0

		# это вопрос с самостоятельным ответом
		elif count_answers == 1:
			a_u_o_text = a_u_o_text.strip()
			if question.answers.filter(Q(is_right=True) & Q(text__iexact=a_u_o_text)):
				user_point = max_point

		elif count_answers > 1:
			# вопрос с одиночным ответом
			if count_is_right_answers == 1:
				if a_u_s_id:
					a_u_s_id = int(a_u_s_id)
					if question.answers.get(is_right=True).id == a_u_s_id:
						user_point = max_point

			# вопрос с множественным ответом
			else:
				a_u_m_ids = [int(i) for i in a_u_m_ids]
				right_answers = question.answers.filter(is_right=True)
				count_right_a = right_answers.filter(id__in=a_u_m_ids).count()
				count_wrong_a = len(a_u_m_ids) - count_right_a
				k = count_right_a - count_wrong_a
				if k < 0: k = 0
				ratio = k / right_answers.count()
				user_point = max_point * ratio
				# делаем 2 цифры после запятой
				user_point = round(user_point, 2)
				print('a_u_m_ids  ', a_u_m_ids)
				# print('count_right_a:  ', count_right_a)
	#####################################################################
		# если у вопроса нет обычных ответов, но есть ассоциативные
		elif count_associate_answers:
			# как ответил пользователь (не заполненные прав. части замещаются 0)
			a_u_a_ids = [ int(i) if i else 0    for i in a_u_a_ids ]
			print('a_u_a_ids\t', a_u_a_ids)

			# если все элементы == 0, то пользователь не отвечал на вопрос
			if sum(a_u_a_ids) != 0:
				correct_sequence_asa = []
				count_right_a = 0

				# в какой последовательн. вопросы выданы пользователю (прав.часть)
				sign_idx_asa = request.COOKIES.get('asa_rn')
				shuffled_idx_asa = signing.loads(sign_idx_asa, key='i29gh394g')

				print('shuffled_idx_asa\t', shuffled_idx_asa)

				# получаем правильную последовательность id-шников
				for item in shuffled_idx_asa:
					correct_sequence_asa.append( a_u_a_ids[item] )

				print('correct_sequence_asa\t', correct_sequence_asa)
				print(type(correct_sequence_asa), type(correct_sequence_asa[0]))

				# теперь сопоставляем
				assoc_ans = question.associate_answers.all().order_by('id')
				for i in range( len(correct_sequence_asa) ):
					if correct_sequence_asa[i] != 0: # 0 - если правая часть None
						print('correct_sequence_asa[i] {}  (!=  0)'.format(
									correct_sequence_asa[i]))
						print(assoc_ans[i].id, correct_sequence_asa[i])

						if assoc_ans[i].id == correct_sequence_asa[i]:
							count_right_a += 1
							print('count_right_a:\t', count_right_a)

					else:
						print('{}  ==  0 '.format(correct_sequence_asa[i]))
						# pass

				ratio = count_right_a / question.count_right_not_none()
				user_point = max_point * ratio
				user_point = round(user_point, 2)
				print('count_right_a (total):\t', count_right_a)
				print('ratio:\t', ratio)
				print('user_point:\t', user_point)
	#####################################################################

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


		score = place_score(user_point, max_point)
		testing, created = Testing.objects.update_or_create(
				user=user, test=test, question=question,
				defaults={'score': score}  )

		response.set_cookie(key='testing_a_dict', value=secda)
		return response

# @login_required(login_url=reverse('ttests:login_url'))
# @login_required()
def test_results(request, id):
	return redirect(reverse('tresults:test_results_url',kwargs={'test_id': id}))

def login(request):
	context = {}
	if request.method == 'POST':
		username = request.POST.get('usernameoremail', '')
		password = request.POST.get('userpassword', '')
		user = auth.authenticate(password=password, username=username)
		if user is not None:
			if user.is_active:
				print('user verified and authenticated successfully')
				auth.login(request, user=user)
				return redirect(reverse('ttests:test_list_url'))
			else:
				# почему-то не работает
				print('password is valid, but account was been disabled')
				context['msg'] = 'ваш профиль был отключен'
		else:
			print('the username or password were incorrect, try to again')
			context['msg'] = 'неверное имя или пароль'
	return render(request, 'ttests/login.html', context)

def logout(request):
	# user = auth.get_user(request)
	auth.logout(request)
	return redirect(reverse('ttests:test_list_url'))

def register(request):
	context = { 'form' : CustomUserCreationForm() }
	if request.method == 'POST':
		newuser_form = CustomUserCreationForm(request.POST)
		if newuser_form.is_valid():
			newuser_form.save()
			user = auth.authenticate(
							username=newuser_form.cleaned_data['username'],
							password=newuser_form.cleaned_data['password2'])
			add_to_simple_users_group(user)
			auth.login(request, user)
			return redirect(reverse('ttests:test_list_url'))
		else:
			context['form'] = newuser_form
	return render(request, 'ttests/register.html', context)


# ------------------------------------------------------------------

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

# =================================================================

# для создания сложных вопросов, нужна агрегация
# https://docs.djangoproject.com/en/2.0/topics/db/aggregation/#filtering-on-annotations
