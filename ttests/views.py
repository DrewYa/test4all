from django.shortcuts import render
from django.shortcuts import get_object_or_404

from django.urls import reverse

from .models import Test, TestTag, Question

# from django.db.models import F

# Create your views here.

'''
test_detail_url
test_list_url
test_by_tag_url
tag_list_url
'''

def test_list(request): # v
	# if request.method
	test_list = Test.objects.order_by('title')[:20]
	context = {
		'test_list' : test_list,
		'title' : 'Тесты',
		}
	return render(request, 'ttests/test_list.html', context)

def test_detail(request, id):
	test = Test.objects.get(id=id)
	context = {
		'test': test,
		'title': 'Детальное описание теста'
	}
	return render(request, 'ttests/test_detail.html', context)

def tag_list(request):
	tag_list = TestTag.objects.order_by('title')[:]
	context = {
		'tag_list': tag_list,
		'title': 'Тэги',
	}
	return render(request, 'ttests/tag_list.html', context)

def test_by_tag(request, slug): # v
	# test_list = TestTag.tests.filter(test__iexact=tag_title)
	test_list = Test.objects.filter(tags__slug=slug)
	context = {
		'test_list': test_list,
		'title': 'Поиск тестов по тегу'
	}
	# return render(request, 'ttests/test_by_tag.html', context)
	return render(request, 'ttests/test_list.html', context)
