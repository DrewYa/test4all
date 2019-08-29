import json
from django.contrib.auth.models import Group, Permission, User


def extract_score(s=None):
	'''str :s: -> user_score (float), max_score (int)'''
	if not s: return None
	scores = s.split('/')
	return float(scores[0]), int(scores[1]) # user's, max

def place_score(user_score=None, max_score=None):
	'''str :ser_score:, str :max_score: -> str "user/max" '''
	if user_score is None or max_score is None:
		return None
	return '{}/{}'.format(user_score, max_score)

def list_from_dict_values(listdict, *args):
	newd = {}
	for key in args:
		l = [ item.get(key, None) for item in listdict ]
		if l:
			newd[key] = l
	return newd

def group_values_by_keys(ld=None, *args):
	'''
	:ld: - list of dict or single dict in format:
	[{key1: val, key2: val}, {key1: val, key2}, ... ]
	:args: - any keys that will try found in :ld:
	return dict in format {key1: [...], key2: [...], ...}
	as return values in the dict can be a single value or list of values
	'''
	if not ld: return None
	newd = {}
	if type(ld) is list:
		for key in args:
			if key in ld[0]:
				l = [ item.get(key, None) for item in ld ]
				if l: newd[key] = l
	elif type(ld) is dict:
		for key in args:
			if key in ld:
				newd[key] = ld[key]
	else:
		return None
	return newd

def add_to_simple_users_group(user=None):
	'''user have permission to create tests,
	but without access to the admin panel, he can't do it.
	'''
	if user is None: return False
	g, created = Group.objects.get_or_create( name='simple_users' )
	if created:
		g.save()
		need_perms = Permission.objects.exclude(codename__in=['add_group',
			'change_group', 'delete_group', 'view_group', 'add_permission',
			'change_permission', 'delete_permission', 'view_permission',
			'add_user', 'change_user', 'delete_user', 'view_user', 'add_user',
			'change_user', 'delete_user', 'view_user'])
		for perm in list(need_perms):
			g.permissions.add(perm)
	g.user_set.add(user)
	user.save()
	return True

def make_superuser(user=None):
	'''make the user a super user.'''
	if user is None: return False
	user.is_superuser = True
	# добавляем права на случай смены прав с суперпользователя на модератора
	all_perms = Permission.objects.all()
	for perm in list(all_perms):
		user.user_permissions.add(perm)
	user.is_staff = True
	user.save()
	return True

def make_user_only_to_pass_tests(user=None):
	'''users can't make tests, but they can resolve them.'''
	if user is None: return False
	user.is_staff = False
	user.save()
	return True

# def calculate_score_s
#
# def calculate_score_m
#
# def calculate_score_o
#
# def calculate_score_a
