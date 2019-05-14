from django.urls import path
from . import views

urlpatterns = [
	path('<int:id>', views.test_detail, name='test_detail_url'), #
	# path('', views.test_list, name='test_list_url'),
	path('', views.TestList.as_view(), name='test_list_url' ),
	path('tags/<str:slug>', views.test_by_tag, name='test_by_tag_url'),
	path('tags/', views.tag_list, name='tag_list_url'),
	# скорее всего нужно убрать потом функционал, чтобы можно было обращаться
	# к тесту введя его id в url
	path('testing/<int:question_id>',
		views.AnswerTheQuestion.as_view(), name='testing_url'),

	path('show_static', views.show_static_img),
	path('get_value', views.get_value_from_form),
]

app_name = 'ttests'
