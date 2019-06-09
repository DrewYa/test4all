from django.core.exceptions import ValidationError

def min_length_1(value):
	'''Проверка на то, что минимальное значение должно быть 1'''
	if value < 1:
		raise ValidationError('Минимальное значение должно быть 1')

def validate_even(value):
	'''Проверка на четность числа.'''
	if value % 2 != 0:
		raise ValidationError('{} is not an even number'.format(value))

def validate_one_type_answer(question):
	if question.answers.count != 0 and question.associate_answers.count != 0:
		raise ValidationError('Вопрос не может быть одновременно вопросом на\
		 	сопоставление и вопросом на саомстоятельный / одиночный /\
			множественный ответ.')
