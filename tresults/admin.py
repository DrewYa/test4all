from django.contrib import admin

# Register your models here.

from .models import Testing, TestingAnswer, TestingAssocAnswer, TestingResult

class TestingAnswerTabularInline(admin.TabularInline):
	model = TestingAnswer
	extra = 0
	min_num = 0
	can_delete = True # False
	# readonly_fields = ['answer_id', 'answer_text']
	# max_num = 0

class TestingAssocAnswerTabularInline(admin.TabularInline):
	model = TestingAssocAnswer
	extra = 0
	min_num = 0
	can_delete = True # False
	# readonly_fields = ['answer_left_id', 'answer_right_id']
	# max_num = 0

# admin.TabularInline.formfield_overrides()
class TestingAdmin(admin.ModelAdmin):
	list_display = ('user', 'test', 'question', 'score', 'id')
	readonly_fields = ['user', 'test', 'question', 'score', 'id', 'testing_result']
	# search_fields = ('user',)
	inlines = [TestingAnswerTabularInline, TestingAssocAnswerTabularInline]

class TestingResultAdmin(admin.ModelAdmin):
	list_display = ('user', 'test', 'result', 'date_start', 'date_complition', 'id')
	# readonly_fields = ['user', 'test', 'result', 'date_start',
						# 'date_complition', 'questions_tags']
	readonly_fields = ['test', 'questions_tags', 'date_complition', 'date_start' ]
	search_fields = ('user',)


admin.site.register(Testing, TestingAdmin)
admin.site.register(TestingResult, TestingResultAdmin)
# admin.site.register(TestingAnswer)
# admin.site.register(TestingAssocAnswer)
