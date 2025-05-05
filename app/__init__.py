from flask import Flask, render_template, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config, TOP_LEVEL_DIR
from flask_login import LoginManager
from flask_mail import Mail
from flask_pagedown import PageDown
from flask_uploads import UploadSet, IMAGES, configure_uploads, AUDIO, DOCUMENTS, patch_request_class
from .web_dict import web_dict as web_obj, read_data_from_file, list_folder_filenames, save_data_to_file, convert_to_html
from datetime import datetime
import os
import datetime_distance as DateTimeDistance

bootstrap = Bootstrap()

mail = Mail()

moment = Moment()

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

app_dir = os.path.abspath(os.path.dirname(__file__))
pagedown=PageDown()

IMAGES = IMAGES+tuple('jfif')+tuple('ico')+tuple('svg')

# Make image uploading configuration via Flask-Uploads
images = UploadSet('images', IMAGES)
package_files = UploadSet('PackageFiles', IMAGES)
transaction_images = UploadSet('Transactions', IMAGES)
post_images = UploadSet('postImages', IMAGES)
post_videos = UploadSet('postVideos', ('mp4'))
message_files = UploadSet('MessageFiles', IMAGES+AUDIO+DOCUMENTS+tuple('mp4'))


def create_app(config_name=None):
	if not config_name or not isinstance(config_name, str):
		config_name = os.getenv('FLASK_CONFIG') or 'default'
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	config[config_name].init_app(app)
	# Maximum allowed file size in bytes (e.g., 100MB)
	app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024
	bootstrap.init_app(app)
	mail.init_app(app)
	moment.init_app(app)
	db.init_app(app)
	login_manager.init_app(app)
	pagedown.init_app(app)
	# configure image uploading configuration via Flask-Uploads
	configure_uploads(app, (images, message_files, package_files,post_videos,post_images,transaction_images))
	#patch_request_class(app, app.config['MAX_CONTENT_LENGTH'])

	# attach routes and custom error pages here

	#import main route and custom error pages
	from .main import main as main_blueprint
	#To inject data available in the create method to the app context for main route blueprint
	@main_blueprint.app_context_processor
	def inject_main_other_data():
		from .models import User, Role, PackageType, Transaction, Coupon, Message, Celebrity, Tracking, TrackingHistory, Winning
		import random
		from .auth.forms import TrackingForm
		from datetime import timedelta
		return dict(config_name=config_name, config=config, User=User, Role=Role, PackageType=PackageType, 
			len=len, r_color=r_color, web_dict=web_obj.__dict__, str=str, type=type, datetime=datetime, 
			float=float, g_color=G_COLOR, random=random, Transaction=Transaction, Tracking=Tracking,
			TrackingHistory=TrackingHistory, list_folder_filenames=list_folder_filenames, Coupon=Coupon, flash=flash, 
			Message=Message, Celebrity=Celebrity, Winning=Winning, timedelta=timedelta,
			DateTimeDistance=DateTimeDistance, convert_to_html=convert_to_html, tracking_form=TrackingForm())


	@main_blueprint.app_context_processor
	def inject_permissions():
		from .models import Permission
		return dict(Permission=Permission)

	@main_blueprint.app_context_processor
	def inject_WebData():
		from .models import WebData
		web_data = WebData.query.first()
		if web_data is None:
			web_data = WebData.build_default()
		return dict(web_data=web_data)

	app.register_blueprint(main_blueprint)

	#import auth route and custom error pages
	from .auth import auth as auth_blueprint
	#To inject data available in the create method to the app context for auth route blueprint
	@auth_blueprint.app_context_processor
	def inject_auth_other_data():
		return dict(config_name=config_name, config=config)

	app.register_blueprint(auth_blueprint, url_prefix='/auth')
	

	return app

def r_color():
	import random
	r=random.randrange(100)
	g=random.randrange(100)
	b=random.randrange(100)
	
	return '#{:02x}{:02x}{:02x}'.format(int(r*2.55),int(g*2.55),int(b*2.55))

class G_COLOR():
	first = '#000'#r_color()
	second = '#fff'#r_color()
	third = '#c0c0c0'#r_color()
	forth = '#fd7e14'#r_color()
	fifth = '#232323'#r_color()
	sixth = '#ad4777'#r_color()

	def load_from_request(self, request):
		g_color_dict=request.cookies.get('g_color_dict', None)
		if g_color_dict:
			g_color_dict=eval(g_color_dict)
			self.load(g_color_dict)
			#save_data_to_file('theme/theme_color7.txt', str(g_color_dict))
			return g_color_dict


	def refresh(self):
		self.first = r_color()#
		self.second =r_color()#
		self.third = r_color()#
		self.forth = r_color()#
		self.fifth = r_color()#
		self.sixth = r_color()#

	def default(self):
		self.load(G_COLOR.__dict__)

	def load(self, g_color_dict):
		if type(g_color_dict) == type({}):
			self.__dict__ = g_color_dict
		else:
			print('Only dictionary values are allow in G_color.load')

	def load_saved_theme(self, theme_color_num):
		g_color_dict_list=self.return_saved_theme_color_list()
		if g_color_dict_list:
			g_color_dict=g_color_dict_list[theme_color_num]
			self.load(g_color_dict)

	def return_saved_theme_color_list(self):
		g_color_dict_list=[]
		folder_name = 'theme'
		theme_filename_list = list_folder_filenames(folder_name)
		if theme_filename_list:
			for filename in theme_filename_list:
				g_color_dict=read_data_from_file('/'+folder_name+'/'+filename)
				g_color_dict_list.append(g_color_dict)
		return g_color_dict_list

	def __repr__(self):
		return '\nfirst:{}\n\nsecond:{}\n\nthird:{}\n\nforth:{}\n\nfifth:{}\n\nsixth:{}\n'.format(self.first, self.second, self.third, self.forth, self.fifth, self.sixth)




if __name__ == '__main__':
	import os
	app=create_app(os.getenv('FLASK_CONFIG') or 'default')
	opr='l'#str(input(' >>>Host as l(ocall or w)ireless Server: '))
	if opr.startswith('l') or opr.startswith('L') :
		app.run(debug=True)
	elif opr.startswith('w') or opr.startswith('W'):
		app.run(host='192.168.43.253', port='', debug=True) ,
	
	raise 'Unknown Operation'
