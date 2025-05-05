from flask import render_template
from . import main
from flask_login import login_user
from ..web_dict import web_dict

web_dict=web_dict.__dict__

@main.app_errorhandler(404)
def page_not_found(e):
	return render_template('404.html', web_dict=web_dict, e=e), 404

@main.app_errorhandler(500)
def internal_server_error(e):
	return render_template('500.html', web_dict=web_dict, e=e), 500