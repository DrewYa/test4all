from django.contrib import admin

# Register your models here.

from .models import *

# обязательные поля
TEST_MANDATORY_TEXT = None# '<h4> Заполните эти поля </h4>'
TEST_OPTIONAL_TEXT = '<p style="color: red">Эти поля можно заполнить \
при последующем редактировании теста</p>'
QUESTION_OPTIONAL_TEXT = None


# интерфейс администратора представлен экземпляром этого объекта
# по умолч. экемпл. находится в   django.contrib.admin.site
# и можно зарегистрировать свои модели в нем используя подкласс AdminModel
# from django.contrib.admin.sites import AdminSite
# from django.contrib.admin import AdminSite
# AdminSite = admin.sites.AdminSite

# уникальное название экземпляра приложения при создании AdminSite
# myadminsite = AdminSite(name='...')
# при создании экземпляра AdminSite можно указать заголовок для админки
# myadminsite.site_header = 'Test4all' # вместо "Django administration"
# myadminsite.index_title = 'Test4all' # вместо "Django administration"
# myadminsite.site_title = 'Test4All' # добавится в тег <title>
# myadminsite.site_url = '/' # для ссылки "открыть сайт" можно убрать, если None

# AdminSite.index_template = ... # переопределить главный (стартовый) шаблон админки
# AdminSite.app_index_template = ... # переопределить главный (стартовый) шаблон
									# данного приложения в админке
# AdminSite.login()
# AdminSite.login_template = ... # переопределить шаблон входа
# AdminSite.login_form = ... 	# подкласс AuthenticationForm
# AdminSite.login_url
# AdminSite.logout_form = ... # шаблон станицы выхода
# AdminSite.password_change_template = ... # для страницы смены пароля
# AdminSite.password_change_done_template = ... # для стр. завершения смены парол.

# методы AdminSite
# https://djbook.ru/rel1.8/ref/contrib/admin/index.html#adminsite-methods




@admin.register(TestTag)
class TestTagAdmin(admin.ModelAdmin):
	model = TestTag
	fieldsets = [(None, {'fields': ['title']})]
	list_display = ('title', 'id', 'slug')
	search_fields = ['title']


class AnswerTabularInline(admin.TabularInline):
	model = Answer
	extra = 0 # видимо, сколько нужно заполнить обязательно
	min_num = 0 # сколько будет сразу показываться для заполнения
	can_delete = True

class AssociateAnswerTabularInline(admin.TabularInline):
	model = AssociateAnswer
	extra = 0
	min_num = 0
	can_delete = True

# вместо   admin.site.register(Question, QuestionAdmin)
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
	fieldsets = [
		(None,		{'fields': ['test', 'text', 'point' ]}),
		('Опционально', {'fields': ['mediafile', 'explanation' ],
						'description': QUESTION_OPTIONAL_TEXT})
	]
	list_display = ('text', 'test', ) # 'id'
	search_fields = ('text', 'test__title')
	inlines = [AnswerTabularInline, AssociateAnswerTabularInline]


class QuestionStackedInline(admin.StackedInline):
	model = Question
	extra = 0
	min_num = 0
	can_delete = True
	# max_num
	# exclude = ['text'] # поля, которые не будут показываться
	# или
	# fields = ['text'] # поля, которые должны показываться
	# readonly_fields = ['point'] # поля, которые нельзя будет исправить
	# raw_id_fields =   ??
	# formfield_overrides =  ??
	# fk_name = 'answers'

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
	fieldsets = [
		(None,			{'fields': ['author', 'title', ],
						'description': TEST_MANDATORY_TEXT }),
		('Опционально', {'fields': [ 'description',
									'is_published',
									'img_description',
									'testing_time',
									'show_q_number',
									'is_shuffle_q',
									'tags',
									'only_fully_correct' ],
						# 'classes': ['collapse']
						# 'classes': ['wide', 'collapse']
						'description': TEST_OPTIONAL_TEXT
						}
		)
	]
	list_display = ('title', 'update_date', 'create_date', 'author') #  'id'
	search_fields = ('title',)
	inlines = [QuestionStackedInline]
	list_filter = ['update_date', 'create_date']
	# list_display_links = (,)
	# field_set = {}

@admin.register(QuestionTag)
class QuestionTagAdmin(admin.ModelAdmin):
	list_display = ('name',  'test', 'get_3_questions') # add  get_3_questions
	search_fields = ('name',)
	# exclude = ['test']

# admin.site.register(Question, QuestionAdmin)
# admin.site.register(Test, TestAdmin)
# admin.site.register(QuestionTag, QuestionTagAdmin)
# admin.site.register(TestTag, TestTagAdmin) # убрать потом из админки вообще

# о том, как упорядочить в админке сущности
# https://toster.ru/q/559846

# admin.ModelAdmin.
