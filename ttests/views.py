import json
import random
from datetime import datetime, timedelta

from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, get_list_or_404
from django.urls import reverse
from django.http import Http404
from django.core import signing
from django.views.generic import View
from django.db.models import Q, Count

from django.contrib import messages
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

# from test4all.settings import SECRET_KEY

from tresults.models import Testing, TestingAssocAnswer, TestingAnswer, TestingResult

from .models import Test, TestTag, Question, User
from .forms import CustomUserCreationForm
from .utils import place_score, add_to_simple_users_group
from .utils import make_superuser

FINISH_TEST_AFTER_LAST_QUESTION = True
COOKIES_ENCRYPT_KEY_FOR_VALUES = 'secret key'   # for secda
SALT_TO_ENCRYPT_VALUES_DICT_QUESTIONS_ID = None # for secda
SIGNING_KEY_FOR_INDEX_ASSOC_ANSWERS = None      # sign_idx_asa
SALT_TO_SIGNING = None
NAME_OF_ADMINISTRATOR = 'Administrator'

# Create your views here.

class TestList(View):
	def get(self, request):
		# test_list = Test.objects.order_by('title')[:20]
		# только опубликованные тесты
		test_list = Test.objects.filter(is_published=True).order_by('title')
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
	# сюда добавить фильтраци чтобы показывать только тесты,
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
	return render(request, 'ttests/test_list.html', context)

def note_cookies_important(request):
	context = {'title': 'Важно!'}
	return render(request, 'ttests/note_cookies_important.html', context)

def show_question(request, question_id):
	# q = get_object_or_404(Question, Q(id=question_id) & Q(test__author=author_id))
	q = get_object_or_404(Question, id=question_id)
	a = q.answers.all()
	asa = q.associate_answers.all()

	# если у вопроса и обыч. и ассоц. варианты ответы, то выведутся обычные
	context = {
		'q': q,
		'answers': a,
		'associate_answers': asa,
		'title': 'тестирование...'
	}
	return render(request, 'ttests/question.html', context)


# если для теста не определено вопросов, то не показывать его пользователям
# для прохождения
# @login_required # не работает
class TestDetail(View, User):
	def get(self, request, id):
		test = get_object_or_404(Test, Q(id=id) & Q(is_published=True) )
		# добавить фильтраци чтобы показывать
		# только тесты, у которых больше 1 вопроса
		user = auth.get_user(request)
		tresults = test.testing_results.filter(user__id=user.id).count()

		context = {
		'test': test,
		'is_exist_results': tresults,
		'title': 'Детальное описание теста'
		}
		return render(request, 'ttests/test_detail.html', context)

	def post(self, request, id):
		user = auth.get_user(request)
		if not user.is_authenticated:
			messages.info(request, 'вам необходимо авторизоваться', extra_tags="info")
			return redirect(reverse('ttests:login_url'))

		test = Test.objects.get(id=id)
		list_questions_id = test.get_all_q_id() # оптимизировать метод

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
		# прим:  list_questions_id = [23, 28, 38, 29, 40]
		# превратится в {'0': 23, '1': 28, '2': 38, '3': 29, '4': 40}
		d = dict([ (str(num), item) for num, item in enumerate(list_questions_id) ])
		secd = signing.dumps(d, key='secret key')
		response.set_cookie(key='testing_q_dict', value=secd)

		# фиксируем время начала тестирования и записываем в куки
		time_start = datetime.now()
		start_ = time_start.timestamp()
		response.set_signed_cookie(key='t_start', value=start_, salt='s29fhs')

		return response

# если делать, чтобы все вопросы выдавались разом, то куки не нужны;
# удобнее и в плане разработки и прохождения теста,
# но интерес был попробовать сделать так, что пока идет тестирование
# id всех вопросов и их порядок следования, а также id ответов
# сохранялись бы в куки
class AnswerTheQuestion(View):
	def get(self, request, q_number):
		q_number = str(q_number)
		secd = request.COOKIES.get('testing_q_dict', None) # порядок вопросов
		if not secd:
			return redirect(reverse('ttests:note_cookies_important_url'))

		d = signing.loads(secd, key='secret key')
		if q_number not in d:
			# if FINISH_TEST_AFTER_LAST_QUESTION and int(q_number) == len(d):
			# 	return redirect(reverse('tresults:processing_results_url'))
			### len_d = len(d); # if int(q_number) >= len_d:
			return redirect(reverse('ttests:testing_url',
										kwargs={'q_number': len(d)-1}))

		# если во время проведения тестирования вопрос будет удален
		current_q_id = d[q_number]
		try:
			q = Question.objects.get(id=current_q_id)
		except Question.DoesNotExist:
			test_id = request.COOKIES.get('test_id', '')
			return redirect(reverse('ttests:test_detail_url', kwargs={'id':test_id}))

		# переделать чтобы вместо сущностей доставались только значения из них
		# id, text, is_right,   id, right_side, left_side
		a = q.answers.all() 						# оптимизировать -> values
		asa = q.associate_answers.all().order_by('id') # оптимизировать -> values

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

		# вопросы убрать из шаблона и сделать здесь
		context = {
			'q' : q,
			'answers' : list_answers or a,
			'r_associate_answers' : r_list_assoc_answers,
			'l_associate_answers' : l_list_assoc_answers,
			'title': 'тестирование...',
		}
		response = render(request, 'ttests/question.html', context)
		if sign_idx_asa:
			response.set_cookie(key='asa_rn', value=sign_idx_asa)

		return response


	def post(self, request, q_number):
		secd = request.COOKIES.get('testing_q_dict') # куки с id вопросов
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
		else:
			if next_q_number > len(d):
				next_q_number = q_number
			response = redirect(
				reverse('ttests:testing_url', kwargs={'q_number': next_q_number}))

		# считываем ответ пользователя
		a_u_o_text = request.POST.get('usr_o_answer')
		a_u_s_id = request.POST.get('usr_s_answer')
		a_u_m_ids = request.POST.getlist('usr_m_answer')
		a_u_a_ids = request.POST.getlist('usr_a_answer') # list of str

		# записываем полученные данные в куки
		secda = request.POST.get('testing_a_dict')
		if secda:
			da = signing.loads(secda, key='secret key')
		else:
			da = {}

		# установка кук в словарь  ...

		# пока напрямую буду заносить результаты
		test_id = int( request.COOKIES.get('test_id') )
		test = Test.objects.get(id=test_id)
		user = auth.get_user(request)
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
		# если у вопроса не ответов/нет правильного - вопрос не будет учтен
		if (count_answers == 0 or count_is_right_answers == 0) and \
									count_associate_answers == 0:
			max_point = user_point = 0

		# это вопрос с самостоятельным ответом
		elif count_answers == 1:
			a_u_o_text = a_u_o_text.strip()
			if question.answers.filter(Q(is_right=True) & Q(text__iexact=a_u_o_text)):
				user_point = max_point

		# вопрос с одиночным ответом
		elif count_answers > 1:
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
				user_point = round(max_point * ratio, 2)

		# если у вопроса нет обычных ответов, но есть ассоциативные
		elif count_associate_answers:
			# ответы пользователя (не заполненные прав. части замещаются 0)
			a_u_a_ids = [int(i) if i else 0  for i in a_u_a_ids]

			# если все элементы == 0, то пользователь не отвечал на вопрос
			if sum(a_u_a_ids) != 0:
				correct_sequence_asa = []
				count_right_a = 0

				# в какой последовательн. вопросы выданы пользователю (прав.часть)
				sign_idx_asa = request.COOKIES.get('asa_rn')
				shuffled_idx_asa = signing.loads(sign_idx_asa, key='i29gh394g')

				# получаем правильную последовательность id-шников
				for item in shuffled_idx_asa:
					correct_sequence_asa.append( a_u_a_ids[item] )

				# теперь сопоставляем
				assoc_ans = question.associate_answers.all().order_by('id')
				for i in range( len(correct_sequence_asa) ):
					if correct_sequence_asa[i] != 0 \
					and assoc_ans[i].id == correct_sequence_asa[i]:
						count_right_a += 1

				ratio = count_right_a / question.count_right_not_none()
				user_point = max_point * ratio
				user_point = round(user_point, 2)

		score = place_score(user_point, max_point)
		testing, created = Testing.objects.update_or_create(
							user=user, test=test, question=question,
							defaults={'score': score})
		testing.score = score
		testing.save()

		response.set_cookie(key='testing_a_dict', value=secda)
		return response

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
			context['msg'] = 'неверная пара имени и пароля'
	return render(request, 'ttests/login.html', context)

def logout(request):
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
			# регистрация администратора
			if newuser_form.cleaned_data['username'] == NAME_OF_ADMINISTRATOR:
				make_superuser(user)
				user.save()
			else:
				add_to_simple_users_group(user)
			auth.login(request, user)
			return redirect(reverse('ttests:test_list_url'))
		else:
			context['form'] = newuser_form
	return render(request, 'ttests/register.html', context)
