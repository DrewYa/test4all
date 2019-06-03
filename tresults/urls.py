from django.urls import path
from . import views

urlpatterns = [
	path('this', views.processing_results,
			name='processing_results_url'),
	# path('<int:test_id>/detail'),
	path('<int:test_id>', views.test_results, name='test_results_url'),
]

app_name = 'tresults'

# === какова структура? ===
"""
список всех тестов
	детальное описание теста
		протестироваться
		результат тестирования (краткий) (по окончании тестирования)
		+ рекомендации (по тегам вопросов)
		+ детальные результаты тестирования (если автор теста разрешит их
										просматривать данному пользователю)
	результат тестирования (краткий) (если прошел уже тест)
	+ рекомендации

для автора теста предоставить возможность просматривать результат теста из
админки (но убрать возможность изменять какое-либо поле в результатах)
"""