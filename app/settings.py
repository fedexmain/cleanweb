#settings.py
import os
# __file__ refers to the file settings.py 
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_STATIC = os.path.join(APP_ROOT, 'static')



if __name__ == '__main__':
	input(
		'APP_ROOT:{}\n\
		APP_STATIC:{}\n\
		Press Enter to exit!'.format(
			APP_ROOT, 
			APP_STATIC
			)
		)