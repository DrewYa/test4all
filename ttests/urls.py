from django.urls import path
from . import views

urlpatterns = [
	path('<int:id>', views.TestDetail.as_view(), name='test_detail_url'), #
	# path('', views.test_list, name='test_list_url'),
	path('', views.TestList.as_view(), name='test_list_url' ),
	path('tags/<str:slug>', views.test_by_tag, name='test_by_tag_url'),
	path('tags/', views.tag_list, name='tag_list_url'),
	# чтобы посмотреть как выглядит вопрос из админки
	path('show_question/<int:question_id>', views.show_question,
	 		name='show_question_url'),
	# скорее всего нужно убрать потом функционал, чтобы можно было обращаться
	# к тесту введя его id в url или как-то еще
	# path('testing/<int:question_id>', views.AnswerTheQuestion.as_view(),
	#  		name='testing_url'),
	path('testing/<int:q_number>', views.AnswerTheQuestion.as_view(),
	 		name='testing_url'),
	path('finish_testing', views.finish_testing, name='finish_testing_url'),
	path('note-cookies-important', views.note_cookies_important,
			name='note_cookies_important_url'),

	path('show_static', views.show_static_img),
	path('get_value', views.get_value_from_form),
]

app_name = 'ttests'
