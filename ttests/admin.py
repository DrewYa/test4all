from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(User)
admin.site.register(TestTag)		# Добавить slugify
# admin.site.register(Test)
# admin.site.register(QuestionTag)
# admin.site.register(Question)
# admin.site.register(Answer)#
# admin.site.register(AssociateAnswer)#

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
	search_fields = ('text',)
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
									'only_fully_correct' ]})
	]
	list_display = ('title', 'author', 'update_date', 'id')
	search_fields = ('title',)
	inlines = [QuestionStackedInline]
	# field_set = {}


class QuestionTagAdmin(admin.ModelAdmin):
	list_display = ('name', 'test') # add  get_3_questions
	search_fields = ('name',)

admin.site.register(Question, QuestionAdmin)
admin.site.register(Test, TestAdmin)
admin.site.register(QuestionTag, QuestionTagAdmin)


# admin.ModelAdmin.se
