import unittest
from app.models import User, Permission, Role, AnonymousUser
from app import create_app, db

class UserModelTestCase(unittest.TestCase):
	
	#  Setup is recognised by unittest object as first task to be push b4 
	#  anyother task
	def setUp(self):
		print('\nsetting up for test.....')
		self.app = create_app('testing')
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.create_all()

	#  Tear down is recognised by unittest object as the last task after 
	#  each test as been pushed
	def tearDown(self):
		print('\ntearDown.....')
		db.session.remove()
		db.drop_all()
		self.app_context.pop()


	def test_password_setter(self):
		u = User(password = 'cat')
		self.assertTrue(u.password_hash is not None)

	def test_no_password_getter(self):
		u = User(password = 'cat')
		with self.assertRaises(AttributeError):
			u.password

	def test_password_verification(self):
		u = User(password = 'cat')
		self.assertTrue(u.verify_password('cat'))
		self.assertFalse(u.verify_password('dog'))

	def test_password_salts_are_random(self):
		u = User(password='cat')
		u2 = User(password='cat')
		self.assertTrue(u.password_hash != u2.password_hash)

	def test_roles_and_permissions(self):
		Role.insert_roles()
		u = User(email='john@example.com', password='cat')
		self.assertTrue(u.can(Permission.WRITE_ARTICLES))
		self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

	def test_anonymous_user(self):
		u = AnonymousUser()
		self.assertFalse(u.can(Permission.FOLLOW))


