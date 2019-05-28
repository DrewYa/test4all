from django.core import signing
from ..settings import SECRET_KEY

def set_quest_answ_sequence(obj=None, key=SECRET_KEY):
	if not key:
		key = 'some-secret-key'
	return signing.dumps(obj, key)

def read_quest_answ_sequence(encode_obj, key=SECRET_KEY):
	if not key:
		key = 'some-secret-key'
	return signing.loads(encode_obj, key)


# ---------------------------------------------------------------
вердикт таков, что   request.get_signed_cookie  использует конструкцию:
from django.core import signing

# устанавливает значение (секретный ключ - на основе секретного ключа проекта)
val = signing.dumps(obj, str_secret_key)

# а затем извлекает так:
origin_val = signing.loads(val, str_secret_key)


только сохраняет значения не в куки (как я хочу), а в таблицу DjangoSession в БД

# -------------------------------------------------------------------


{'csrftoken': 'LszHqUkgQ4jFKSq6HhWYXhSHYRB6g0QiM23oASana62kblY8wUwlU8bqyH46IPf3', 'sessionid': 'y0kagegzs0xbrpk87ukj2i5twtxtpy1s'}


['__class__', '__contains__', '__delattr__', '__delitem__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getitem__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__iter__', '__le__', '__len__', '__lt__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setitem__', '__sizeof__', '__str__', '__subclasshook__', 'clear', 'copy', 'fromkeys', 'get', 'items', 'keys', 'pop', 'popitem', 'setdefault', 'update', 'values']


{'csrftoken': 'LszHqUkgQ4jFKSq6HhWYXhSHYRB6g0QiM23oASana62kblY8wUwlU8bqyH46IPf3', 'sessionid': 'y0kagegzs0xbrpk87ukj2i5twtxtpy1s', 'answ_the_questions': '{7: {583: 1, 584: 2, 585: 3, 586: 4}}'}


True


<bound method HttpRequest.get_signed_cookie of <WSGIRequest: GET '/6'>>


['__call__', '__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__func__', '__ge__', '__get__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__self__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__']



Help on method get_signed_cookie in module django.http.request:

get_signed_cookie(key, default=<object object at 0x0000017C894CA4D0>, salt='', max_age=None) method of django.core.handlers.wsgi.WSGIRequest instance
    Attempt to return a signed cookie. If the signature fails or the
    cookie has expired, raise an exception, unless the `default` argument
    is provided,  in which case return that value.

None



<django.contrib.sessions.backends.db.SessionStore object at 0x0000017C8B321AC8>


{7: {583: 1, 584: 2, 585: 3, 586: 4}}
Drew


[12/May/2019 13:24:45] "GET /6 HTTP/1.1" 200 6198




# ------------

def test_detail(request, id):
	# try:
	# 	test = Test.objects.filter( Q(id=id) & Q(is_published=True) )[0]
	# except IndexError: # Test.DoesNotExist
	# 	raise Http404
	test = get_object_or_404(Test, Q(id=id) & Q(is_published=True) )

	print(request.COOKIES, '\n\n')		# COOKIES это словарь
	print(dir(request.COOKIES), '\n\n')
	request.COOKIES['answ_the_questions'] = str({7:{583:1, 584:2, 585:3, 586:4}})
	print(request.COOKIES, '\n\n')

	print(request.csrf_processing_done, '\n\n')

	# пытается вернуть подписанные куки; если сигнатуры испорчены
	# или куки истекли по времени, вызывает ошибку
	# django.core.signing.BadSignature
	# если установлено значение default, то возвращает его,
	# а не вызывает ошибку
	# get_signed_cookie(key, default=<object>, salt='', max_age=None)
	print(request.get_signed_cookie, '\n\n')
	# таким способом мы не установим куки у пользователя, а лишь добавим
	# значения в уже полученный от пользователя ответ
	print(dir(request.get_signed_cookie), '\n\n')
	print(help(request.get_signed_cookie), '\n\n')

	# django.contrib.sessions.backends.db.SessionStore object
	print(request.session, '\n\n')
	request.session['bla'] = str({7:{583:1, 584:2, 585:3, 586:4}})
	print(request.session.get('bla', None))
	# print(request.upload_handlers, '\n\n')
	print(request.user, '\n\n')


	context = {
	'test': test,
	'title': 'Детальное описание теста'
	}
	return render(request, 'ttests/test_detail.html', context)

==============================================================
------------------------------------
https://djbook.ru/rel1.9/ref/request-response.html#django.http.HttpRequest.get_signed_cookie

https://djbook.ru/rel1.9/topics/signing.html

	# пытается вернуть подписанные куки; если сигнатуры испорчены
	# или куки истекли по времени, вызывает ошибку
	# django.core.signing.BadSignature
	# если установлено значение default, то возвращает его,
	# а не вызывает ошибку
	# get_signed_cookie(key, default=<object>, salt='', max_age=None)
	print(request.get_signed_cookie, '\n\n')

	необязательный аргумент salt может быть использован для защиты от
	brute force атак.
	Если передан аргумент max_age, время подписи куков будет проверяться
	чтобы убедиться, что куки не старше max_age секунд

например

>>> request.get_signed_cookie('name')
'Tony'
>>> request.get_signed_cookie('name', salt='name-salt')
'Tony' # assuming cookie was set using the same salt
>>> request.get_signed_cookie('non-existing-cookie')
...
KeyError: 'non-existing-cookie'
>>> request.get_signed_cookie('non-existing-cookie', False)
False
>>> request.get_signed_cookie('cookie-that-was-tampered-with')
...
BadSignature: ...
>>> request.get_signed_cookie('name', max_age=60)
...
SignatureExpired: Signature age 1677.3839159 > 60 seconds
>>> request.get_signed_cookie('name', False, max_age=60)
False

----------------------------------------
объект HttpRequest создается Django при запросе пользователя
В объекте HttpRequest, атрибуты GET и POST являются
экземплярами класса django.http.QueryDict

QueryDict из request.POST и request.GET – неизменяемы.
Чтобы получить изменяемую версию, используйте .copy()

о других методах и возможностях тут:
https://djbook.ru/rel1.9/ref/request-response.html#querydict-objects



объект  HttpResponse  создаем мы сами, и этот объект мы отправляем пользователю
в качестве ответа. Т.е. любая вьюшка должна его возвращать
Класс HttpResponse находится в модуле django.http

https://djbook.ru/rel1.9/ref/request-response.html#httpresponse-objects

Если необходимо отдавать данные из итератора в потоке,
используйте экземпляр StreamingHttpResponse.

для установления параметров, можно использовать его как словарь:
HttpResponse['key'] = value

Указываем браузеру воспринимать ответ как вложенный файл. Для этого используйте
аргумент content_type и установите заголовок Content-Disposition.
Например, вот так вы можете вернуть таблицу Microsoft Excel:
>>> response = HttpResponse(my_data, content_type='application/vnd.ms-excel')
>>> response['Content-Disposition'] = 'attachment; filename="foo.xls"'
Заголовок Content-Disposition никак не относится к Django, но очень легко
забыть синтаксис, поэтому мы добавили пример.

атрибуты:
.content  - байтовое представление
.charset  - кодировка в которой будет закодирован ответ
.status_code  - http код ответа
	https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10
.reason_phrase
.streaming 	- обычно False - указывает middleware, что этот ответ потоковый
	и его нужно обрабатывать не так, как обычные запросы
.closed  - True если ответ был закрыт

методы:
.__init__(content='', content_type=None, status=200, reason=None, charset=None)
	Создает экземпляр HttpResponse с переданным содержимым и MIME-типом
	content должен быть строкой или итератором (возвращающим строки)
	content_type - MIME-тип, возможно с кодировкой, используется в
		HTTPзаголовке Content-Type. По умолчанию  “text/html; charset=utf-8”
	reason – описание HTTP ответа. Если не указано, будет исп. стандартное значение.
.has_header(header)  	Возвр. True или False, поиск по загол. регистронезависимый

# https://djbook.ru/rel1.9/ref/request-response.html#django.http.HttpResponse.set_cookie
# https://docs.python.org/3/library/http.cookies.html#http.cookies.Morsel
.set_cookie(key, value='', max_age=None, expires=None, path='/',
 			domain=None, secure=None, httponly=False) # secure=False

Устанавливает cookie. Аргументы соответствуют аргументам для конструктора
объекта Morsel из стандартных библиотек Python.
	max_age  должен содержать количество секунд или None (по-умолчанию),
	если cookie должна существовать до закрытия браузера. Если expires не
	указан, он будет вычислен.

	path - позволяет указать, по какому пути браузер должен возвращать куки с этим
	ключом. По умолчанию '/'. Означает, что браузер вернут куки по этому пути и
	всем нижележащим.
	Т.е. если установить путь '/test/6/' то бразуер будет возвращать это значение кук
	по путям "/test/6/", "/test/6/testing/", "/test/6/testing/result" и все вообще
	все что после "/test/6/..."

	key - имя файла куки

	value - значение файла куки

	expires - должен быть строкой в формате "Wdy, DD-Mon-YY HH:MM:SS GMT" или
	объект datetime.datetime в UTC. Если expires объект datetime, значение
	max_age будет вычислено.
	[
	from datetime import datetime, timedelta
	# куки которые истекут на следующий день
	next_day_from_utcnow = datetime.utcnow() + timedelta(days=1)
	это указываем в  expires = next_day_from_utcnow
	]

	Используйте  domain  если хотите установить междоменные cookie. Например,
	domain=".lawrence.com" установит cookie доступные для доменов www.lawrence.com,
	blogs.lawrence.com и calendars.lawrence.com. Иначе, cookie будут доступны
	только для текущего домена.

	Используйте httponly=True, если хотите ограничит доступ клиентского
	JavaScript к этим cookie. Работает не во всех клиентах, но все же
	HTTPOnly – это флаг добавляемый в HTTP заголовок Set-Cookie ответа.
	Он не является частью стандарта RFC 2109, и поддерживается не всеми
	браузерами. Однако, если он поддерживается, это может быть полезным для
	уменьшения риска, что клиентский скрипт получит доступа к защищенным
	данным cookie.

# https://djbook.ru/rel1.9/ref/request-response.html#django.http.HttpResponse.set_signed_cookie
.set_signed_cookie(key, value, salt='', max_age=None, expires=None,
				path='/', domain=None, secure=None, httponly=True)

----------------------------------------

что за атрибуты:
request._set_post
._get_scheme
._initialize_handlers
._load_post_and_files
._mark_post_parse_error
._messages
._read_started
._set_post
._upload_handlers
.is_secure			возвращает True, если запрос был безопасные (https)
.is_ajax	https://djbook.ru/rel1.9/ref/request-response.html#django.http.HttpRequest.is_ajax
.parse_file_upload
.scheme
.session
.upload_handlers

print('remote addr', request.META['REMOTE_ADDR'])
print('remote host', request.META['REMOTE_HOST'])
print('remote user', request.META.get('REMOTE_USER'))
print('server name', request.META['SERVER_NAME'])
print('server port', request.META['SERVER_PORT'])


кстати, метод   .get_signed_cookie есть у объекта HttpRequest,
а м. .set_signed_cookie  смотри в HttpResponse.set_signed_cookie
[[[[[ -----------------
видимо это нужно делать вручную (нет, это не нужно делать вручную!)
from django.core import signing
val = signing.dumps(<obj>, key=None, salt=<salt>,  serializer=django.core.signing.JSONSerializer, compress=False)

# т.е. signing() преобзразует объект к json представлению и кодирует его

сериализатор JSONSerializer - это обертка над
django.core.signing. Поэтому он может сериализовать только простые
типы данных (в т.ч. кортежи и списки, словари) [это мне подходит]
! json поддерживает только строки в качестве ключей

! ключи словаря сессии зарезервированы для использования django

примеры https://djbook.ru/rel1.9/topics/http/sessions.html#examples

[
есть еще сериализатор  serializers.PickleSerializer
Поддерживает произвольные объекты Python, но может привести к
несанкционированному исполнению чужого кода на сервере в случае,
если значение параметра конфигурации SECRET_KEY станет известно
злоумышленнику.

можно написать свой сериализатор или подогнать свои данные под
JSONSerializer или PickleSerializer
]
-------------------- ]]]]]
# ===================================

# question_list_testing = {test_id: {question_id: 1, question2_id:0, ...}}
# пользователь уже ответил на вопрос c id 89 и теста с id 23
question_list_testing = {'23': {'89': 1, '90': 0, '91': 0}}

question_id = <смотрим id текущего вопроса>
test_id = <смотрим id текущего теста>
answered = question_list_testing[test_id][question_id]
if answered:
	# пользователь уже отвечал на этот
else:
	# обрабатываем ответ пользователя, записываем его в куки (или БД)
	# и записываем в question_list_testing  0 чтобы пользователь
	# не смог повторно ответить на вопрос (если этот функционал нужен)

# -------------------------------------
================================================


def view1(request):
	# ...
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
	response = render(request, 'ttests/template1.html')
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



def view2(request):
	# ...
	# #########
	print('\n\ncookies: ', request.COOKIES, '\n\n')
	sec_val = request.get_signed_cookie(key='sec_tsting', default=None )
	val = signing.loads(sec_val, key='secret key', salt='some salt')
	print('sec val from cookie: ', val, '\n\n')
	# ########
	sec_val = request.COOKIES.get('sec_testing2', None)
	val = signing.loads(sec_val, key='secret key', salt='some salt')
	print('значение из шифрованных, подписанных кук:\n', val)
	# #######

	return render(request, 'ttests/template2.html')

================================================================
