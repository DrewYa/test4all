

# из urls
	# скорее всего нужно убрать потом функционал, чтобы можно было обращаться
	# к тесту введя его id в url или как-то еще
	# path('testing/<int:question_id>', views.AnswerTheQuestion.as_view(),
	#  		name='testing_url'),


class AnswerTheQuestion(View):					  ### testing_url
	def get(self, request, question_id):
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

		print(request.COOKIES)

		response = render(request, 'ttests/question.html', context)
		return response


	def post(self, request, question_id):
		# значение одиночного вопроса с одиночным ответом
		a_u_o_id = request.POST.get('usr_o_answer') # собтвенный
		a_u_s_text = request.POST.get('usr_s_answer') # одиночный
		a_u_m_ids = request.POST.getlist('usr_m_answer') # множественный

		a_u_a_id = request.POST.getlist('usr_a_answer') # ассоц.  доделать!


		# print(request.COOKIES)
		val = request.COOKIES.get('testing_q')
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

		return redirect(reverse('ttests:testing_url', kwargs={'question_id': next_q} ))




# с последней версии (когда вместо question_id) сделал question_number
class AnswerTheQuestion(View):					  ### testing_url
	def get(self, request, q_number):		### версия со словарем в куках
		secd = request.COOKIES.get('testing_q_dict', None)
		if not secd: # если такой куки нет
			# стр. с объяснениями, что куки были удалены или не поддерживаются
			return redirect(reverse('ttests:note_cookies_important_url'))
		d = signing.loads(secd, key='secret key')
		# если пользователь ввел вручную в url number вопроса, которые не сущ.
		# например -1 или -10 или 1900.
		# ВАЖНО! отрицательные значения в url не будут восприниматься как числа,
		# это будет уже строка из дефиса и цифр
		if str(q_number) not in d:
			len_d = len(d)
			if q_number >= len_d:
				return redirect(reverse('ttests:testing_url',
										kwargs={'q_number': len_d-1}))
		current_q_id = d[str(q_number)]
		# на случай если автор во время прохождения удалит из теста вопрос
		q = get_object_or_404(Question, id=current_q_id)
		a = q.answers.all() ##
		asa = q.associate_answers.all() ##

		context = {
			'q' : q,
			# вопросы закоментить, либо убрать из шаблона
			# и сделать здесь
			'answers' : a,
			'associate_answers' : asa,
			'title': 'тестирование...'
		}

		return render(request, 'ttests/question.html', context)

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
		a_u_a_id = request.POST.getlist('usr_a_answer') # ассоц.  доделать!

		# записываем полученные данные в куки
		# (пока идет тестирования все ответы сохраняем в куки)
		secda = request.POST.get('testing_a_dict')
		if secda:
			da = signing.loads(secda, key='secret key')
		else:
			da = {}

		# установка кук в словарь

		if a_u_o_text:
			da[current_q_id] = {'o': {}}
			da[current_q_id]['o'][answer_id] = a_u_o_text # значение - строка
		elif a_u_s_id:
			da[current_q_id] = {'s': {}}
			for item_id in a_u_s_id:
				da[current_q_id]['s'][item_id]


		response.set_cookie(key='testing_a_dict', value=secda)

		return response




# def finish_testing(request):
# 	context = {
#
# 	}	# результаты тестирования
#
# 	return render(request, 'ttests/finish_testing.html', context)
