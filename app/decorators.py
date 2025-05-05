from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission


def permission_required(permission):
	def decorator(f):
		@wraps(f)
		def decorated_function(*args, **kwargs):

			print('current user %s required permission --- %s'%\
				(
					'have' if current_user.can(permission) else 'does not have', 
					current_user.can(permission)
					)
				)

			if not current_user.can(permission):
				abort(403)
			return f(*args, **kwargs)
		return decorated_function
	return decorator

def admin_required(f):
	return permission_required(Permission.ADMINISTER)(f)

