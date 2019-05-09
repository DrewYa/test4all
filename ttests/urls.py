from django.urls import path
from . import views

urlpatterns = [
	path('<int:id>', views.test_detail, name='test_detail_url'), #
	path('', views.test_list, name='test_list_url'),
	path('tags/<str:slug>', views.test_by_tag, name='test_by_tag_url'),
	path('tags/', views.tag_list, name='tag_list_url'),
]

app_name = 'ttests'
