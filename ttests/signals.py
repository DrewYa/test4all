# https://djbook.ru/rel1.9/topics/signals.html
# from django.core.signals import ... # отправляются при нач. и оконч. http запроса
# from django.db.signals import
# отпрвл. до и после вызова м. save() модели; до и после вызоыва м.
# delete() модели и QuerySet'a; после изменения ManyToManyField в модели;
# начала и окончания http запроса
# from django.db.models.signals import

# во избежаение ложных срабатываний сигналов, лучше их писать не в models.py,
# а в отдельном модуле

### !! Этот файл пока не работает, его нужно специальным образом подключить ###


from django.db.models.signals import pre_save
from django.dispatch import receiver
from ttests.models import Question
from .models import TestTag

from django.core.exceptions import ValidationError

from django.utils.text import slugify
from transliterate import translit

@receiver(pre_save, sender=Question)
def handler_validate_one_type_answer(sender, kwargs={}):
	'''Будет вызывана при сохранении экземпляра модели Question.'''
	pass
	# если у вопроса пользователь добавил разные типы ответа
	# (ассоц и обыч) то вызывать ошибку валидации
	# "у вопроса должен быть только 1 какой-либо тип ответов"


# !!! здесь есть одна уязвимость - если пользовтель в title напишет один и
# тот же текст, но в разных регистрах (или отдельные буквы будут в разных),
# то текст добавится, но slug у них будет один и тот же!
def pre_save_test_tag_slug(sender, instance, *args, **kwargs):
	title = str(instance.title).lower()
	instance.title = title
	if TestTag.objects.get(title__iexact=title):
		raise ValidationError('такой тэг теста уже существует')
	if not instance.slug:
		print('title:   ', instance.title)
		# unicode_slug = unicode(slug)
		# reversed - чтобы ru -> en
		translit_title = translit(instance.title, reversed=True)
		slug = slugify(translit_title)
		print('slug:   ', slug)
		instance.slug = slug

pre_save.connect(receiver=pre_save_test_tag_slug, sender=TestTag)
# теперь если мы зайдем в модели TestTag у поля slug нужно указать blank=True


"""
также вместо того, чтобы делать slug на английском, возможен слаг на русском
это делается так:

slug = slugify('какой-то текст на русском', allow_unicode=True)

все! теперь в slug записался слаг на русском
>>> from django.utils.text import slugify
>>> help(slugify)
Help on function slugify in module django.utils.text:

slugify(value, allow_unicode=False)
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
>>>
>>> slugify('какой-то текст на русском')
'-'
>>> slugify('какой-то текст на русском', allow_unicode=True)
'какой-то-текст-на-русском'
"""
