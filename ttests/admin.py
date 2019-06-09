from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(User)
# admin.site.register(QuestionTag)
# admin.site.register(Question)


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

class QuestionAdmin(admin.ModelAdmin):
	fieldsets = [
		(None,		{'fields': ['test', 'text', 'point' ]}),
		('Опционально', {'fields': ['mediafile', 'explanation' ]})
	]
	list_display = ('text', 'test', 'id')
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
	# fk_name = ??

class TestAdmin(admin.ModelAdmin):
	fieldsets = [
		(None,	{'fields': ['author', 'title', ]}),
		('Опционально', {'fields': [ 'description',
									'is_published',
									'img_description',
									'testing_time',
									'show_q_number',
									'is_shuffle_q',
									'tags',
									'only_fully_correct' ],
						# 'classes': ['collapse']
						}
		)
	]
	list_display = ('title', 'update_date', 'create_date', 'author', 'id')
	search_fields = ('title',)
	inlines = [QuestionStackedInline]
	list_filter = ['update_date', 'create_date']
	# list_display_links = (,)
	# field_set = {}


class QuestionTagAdmin(admin.ModelAdmin):
	list_display = ('name',  'test', 'get_3_questions') # add  get_3_questions
	search_fields = ('name',)
	# exclude = ['test']

admin.site.register(Question, QuestionAdmin)
admin.site.register(Test, TestAdmin)
admin.site.register(QuestionTag, QuestionTagAdmin)
admin.site.register(TestTag, TestTagAdmin) # убрать потом из админки вообще

# о том, как упорядочить в админке сущности
# https://toster.ru/q/559846

# admin.ModelAdmin.
