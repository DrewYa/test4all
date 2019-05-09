from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(User)
admin.site.register(TestTag)
admin.site.register(Test)
admin.site.register(QuestionTag)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(AssociateAnswer)
