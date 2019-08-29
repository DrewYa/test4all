from django.urls import path
from . import views

urlpatterns = [
	path('this', views.processing_results, name='processing_results_url'),
	path('<int:test_id>', views.test_results, name='test_results_url'),
]

app_name = 'tresults'
