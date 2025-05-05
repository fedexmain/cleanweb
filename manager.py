import os
from app import create_app, db
from app.models import User, Role, Message, Notification, PackageType, Package
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from tests import test_user_model



app = create_app(os.getenv('CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
	#return a defualt variable dictionary to the shell
	return dict(app=app, db=db, User=User, Role=Role, Message=Message, 
		Notification=Notification, PackageType=PackageType, Package=Package)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("test", test_user_model)
manager.add_command('db', MigrateCommand)



@manager.command
def test():
	"""Run the unit tests."""
	import unittest
	tests = unittest.TestLoader().discover('tests')
	unittest.TextTestRunner(verbosity=2).run(tests)

@manager.command
def runserver():
	"""Run the server via external port."""
	try:
		app.run(debug=True)
	except Exception as e:
		print(e)
		
@manager.command
def runserver_on_random_port():
	import random
	"""Run the server via random port."""
	port=int(''.join(random.choices('56789', k=4)))
	print(f'\n\nPort: {port}\n\n')
	try:
		app.run(port=port, debug=True)
	except Exception as e:
		print(e)
		print('\a\a\aPlease debug error and try again!')

@manager.command
def runserver_on_p_wifi_port():
	"""Run the server via external port."""
	try:
		app.run(host='192.168.43.1', port=5000, debug=True)
	except Exception as e:
		print(e)
		print('\a\a\aPlease debug error and try again!')

@manager.command
def runserver_on_OS_wifi_port():
	"""Run the server via external port."""
	try:
		app.run(host='192.168.43.253', port=5000, debug=True)
	except Exception as e:
		print(e)
		print('\a\a\aPlease debug error and try again!')


@manager.command
def runserver_on_OS_wifi_port2():
	"""Run the server via external port."""
	try:
		app.run(host='192.168.43.210', port=5000, debug=True)
	except Exception as e:
		print(e)
		print('\a\a\aPlease debug error and try again!')


@manager.command
def runserver_on_OS_wifi_port3():
	"""Run the server via external port via your input"""
	try:
		host=str(input('Host : '))
		port=int(input('Port : '))
		app.run(host=host, port=port, debug=True)
	except Exception as e:
		print(e)
		print('\a\a\aPlease debug error and try again!')


if __name__ == '__main__':
	manager.run()