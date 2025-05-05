from flask import Blueprint
auth = Blueprint('auth', __name__)
from . import views
from ..web_dict import web_dict as web_obj