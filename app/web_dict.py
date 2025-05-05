from flask import flash
import os
from markdown import markdown
import bleach

APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top
APP_STATIC = os.path.join(APP_ROOT, 'static')

class web_dict(object):
	"""docstring for web_dict"""
	name_abrr          = 'BlurtOutLouD'
	name               = 'BlurtOutLouD'
	facebook_link = "https://facebook.com/BlurtOutLouD-108345811413614"
	instagram_link = 'https://instagram.com/BlurtOutLouD'
	email           = 'BlurtOutLouD@gmail.com' 
	number_list            = ['+2349074219408', '+2348051031118'] 

def save_data_to_file(name, data):
	file= open(APP_STATIC+'/'+name, 'w')
	file.write(data)
	file.close()

def read_data_from_file(name):
	file = open((APP_STATIC+'/'+name).replace('\\', '/'), 'r')
	if file:
		data=file.read()
		file.close()
		return eval(data)

def list_folder_filenames(folder_name):
	print(APP_STATIC+'/'+folder_name)
	try:
		return os.listdir((APP_STATIC+'/'+folder_name).replace('\\', '/'))
	except Exception as e:
		flash(e)
		return []

def delete_web_file(url):
	try:
		os.remove((APP_STATIC[:-7]+url).replace('\\', '/'))
	except Exception as e:
		raise e

def get_file_type(file_url):
    _, file_extension = os.path.splitext(file_url)
    file_extension = file_extension.lower()
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
    audio_extensions = ['.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a']
    video_extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.wmv']
    document_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt']
    archive_extensions = ['.zip', '.rar', '.tar', '.gz', '.7z']

    if file_extension in image_extensions:
        return 'image'
    elif file_extension in audio_extensions:
        return 'audio'
    elif file_extension in video_extensions:
        return 'video'
    elif file_extension in document_extensions:
        return 'document'
    elif file_extension in archive_extensions:
        return 'archive'
    else:
        return 'unknown'


def convert_to_html(text):
    if text:
	    allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
	        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
	        'h1', 'h2', 'h3', 'p', 'br', 'span', 'hr']
	    return bleach.linkify(
	        bleach.clean(
	            markdown(text, output_format='html'), 
	            tags=allowed_tags,
	            strip=True)
	        )
    else:
    	return ''

