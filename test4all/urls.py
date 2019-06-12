"""test4all URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from ttests import views

urlpatterns = [
	path('admin/login/', views.login),		# go to custoum login page
	path('admin/logout/', views.logout),	# go to custom logout page
	path('admin/', admin.site.urls),
	path('', include('ttests.urls')),
	path('results/', include('tresults.urls')),
]


# для отображения загруженных статических файлов
from . import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# а так можно реализовать собственные вьюшки для обработки ошибок
# 404, 500, 403 и др.
# (осторожно, устарело) https://evileg.com/ru/post/9/
# в своем приложении пишем вьюшки для обработки, например:
# def e_handler404(request):
# 	context = RequestContext(request)
# 	response = render_to_response('error404.html', context)
# 	response.status_code = 404
# 	return response
#
# def e_handler500(request):
# 	context = RequestContext(request)
# 	response = render_to_response('error500.html', context)
# 	response.status_code = 500
# 	return response

#   и импортируем их сюда
# from ttests.views import e_handler_404, e_handler_500
# handler_404 = e_handler_404
# handler_500 = e_handler_500

# есть способ попроще:
# просто создаем файл для соотствующего кода ошибки в формате:
# <код>.html  (например 404.html)
# и кидаем его в папку templates в ее корень
# а во вьюшке где нужно вызвать соотв. ошибку пишем конструкцию:
# from django.http import Http404
# ...
# try:
# 	код, который может вызывать ошибку
# except:
# 	Http404
