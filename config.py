import os
from dotenv import load_dotenv

load_dotenv()  # Only needed locally

basedir = os.path.abspath(os.path.dirname(__file__))
TOP_LEVEL_DIR = basedir

class Config:
	SECRET_KEY = os.getenv('SECRET_KEY')
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True
	SQLALCHEMY_TRACK_MODIFICATIONS = True
	MAIL_SUBJECT_PREFIX = '[FanGrant]'
	MAIL_SENDER = os.getenv('ADMIN_MAIL')
	MAIL_USERNAME = os.getenv('MAIL_USERNAME')
	MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
	ADMIN = os.getenv('ADMIN')
	#Uploads configuration
	MAX_CONTENT_LENGTH = 388800 * 1024 * 1024
	UPLOADS_DEFAULT_DEST = TOP_LEVEL_DIR + '/app/static/web_files/'
	UPLOADS_DEFAULT_URL = '/static/web_files/'
	 
	UPLOADED_IMAGES_DEST = TOP_LEVEL_DIR + '/app/static/web_files/photo/'
	UPLOADED_IMAGES_URL = '/static/web_files/photo/'

	POSTS_PER_PAGE = 10
	COMMENTS_PER_PAGE = 5
	FOLLOWERS_PER_PAGE = 10
	FRIENDS_PER_PAGE = 10
	FRIEND_REQUESTS_PER_PAGE = 10

	@staticmethod
	def init_app(app):
		pass


class DevelopmentConfig(Config):
	DEBUG = True
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL') or \
	'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

class TestingConfig(Config):
	TESTING = True
	SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL') or \
	'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
	

class ProductionConfig(Config):
	DEBUG = True
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or \
	'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
	'development': DevelopmentConfig,
	'testing': TestingConfig,
	'production': ProductionConfig,
	'default': DevelopmentConfig
	}


