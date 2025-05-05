from datetime import datetime

from flask import render_template, redirect, session, request, url_for, flash,\
 make_response, abort, current_app, jsonify, g, get_flashed_messages

from . import main

from ..auth.forms import EditProfileForm, AdminEditProfileForm, ModEditProfileForm, TaskForm, \
CommentForm, SearchForm, MessageForm, ProfilePixUploadForm, \
ModeratorRegistrationForm, CashoutForm, ContactUsForm, PaymentForm, \
VendorRegistrationForm, MakeCoinForm, LoadCoinForm, PostForm, BankWithdrawalForm, \
TransactionForm, CouponForm, FakeCoinForm, BombForm, FanCardUpdateForm, \
AdminFanCardEditForm, FanCardForm, WebDataForm,  CoinPackageForm, \
CoinPackagePaymentForm, TrackingForm, RechargeForm

from .. import db, images, message_files, G_COLOR, package_files, post_videos, post_images, \
transaction_images, moment

from ..models import WebData, Themes, User, Permission, Role, PackageType, Message, Notification, \
BadgeNotification, MessageRecipe, Package, DailyTask, PackageFile, CoinRecharger, \
Post, PostRecipe, Comment, PostLike, PostDislike, CommentLike, CommentDislike, Transaction, \
TransactionRecipe, ConnectHook, Celebrity, CelebrityPicture, Coupon, FanCard, CoinPackage, CoinPackagePayment

from ..web_dict import web_dict, list_folder_filenames, delete_web_file, get_file_type
from flask_login import current_user, login_required, login_user
from ..decorators import admin_required, permission_required
from sqlalchemy.exc import IntegrityError

from ..email import send_email, notify_admin_of_payment, notify_user_of_verification, send_message_notification

import json
import datetime_distance as DateTimeDistance
import random
from ..email_generator_v2 import send_generated_mass_mail

from ..settings import APP_STATIC
from playht_client import PlayHTClient
from fAtherGPT import chat_fAtherGPT, openai

from .. import app_dir
# Make cookies default elapse time in seconds
cookies_elapse_time = None
sec = 1                  # 1bit       =         1sec
a_minute = 60 * sec      # 1sec * 60 = 60sec  = 1min e.i, it is the same as 60 in seconds
an_hour  = a_minute * 60 # 1min * 60 = 60min  = 1hr e.i, it is the same as (60*60)
a_day = an_hour * 24     # 1hr  * 24 = 24hrs  = 1day e.i, it is the same as (60*60*24)
a_month  = a_day * 30    # 1day * 30 = 30days = 1month e.i, it is the same as (60*60*24*30)
a_year  = a_month * 12    # 1day * 30 = 30days = 1month e.i, it is the same as (60*60*24*30*12)
cookies_elapse_time=a_month

web_data=None
@main.before_request
def before_request():
	global web_data

	web_data = g.web_data

	#Check old transaction recipe to be deleted
	for t in TransactionRecipe.query.all():
		if DateTimeDistance(t.timestamp,'in_hour') > 24:
			t.delete()


@main.route('/change theme color/', methods=['GET'])
@login_required
def change_theme_color():
	g_color=G_COLOR()
	g_color.refresh()
	colors = dict(g_color.__dict__)
	resp = make_response(redirect(request.args.get('next', None) or '/'))
	resp.set_cookie('g_color_dict', str(colors), max_age=a_month)
	return resp


@main.route('/restore theme default color/', methods=['GET'])
@login_required
def restore_theme_default_color():
	g_color=G_COLOR()
	g_color.default()
	colors = dict(g_color.__dict__)
	print(colors)
	resp = make_response(redirect(request.args.get('next', None) or '/'))
	resp.set_cookie('g_color_dict', str(colors), max_age=a_month)
	return resp

@main.route('/load created theme color/<int:theme_color_num>', methods=['GET'])
@login_required
def load_saved_theme_color(theme_color_num):
	g_color=G_COLOR()
	g_color.load_saved_theme(theme_color_num)
	colors = dict(g_color.__dict__)
	print(colors)
	resp = make_response(redirect(request.args.get('next', None) or '/'))
	resp.set_cookie('g_color_dict', str(colors), max_age=a_month)
	return resp

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
	user = User.query.filter_by(username=username).first_or_404()

	if current_user.is_following(user):
		flash('You are already following this user.')
		return redirect(url_for('.profile', username=username))

	current_user.follow(user)
	flash('You are now following %s.' % username)
	return redirect(request.args.get('next') or url_for('.profile', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
	user = User.query.filter_by(username=username).first_or_404()
	if not current_user.is_following(user):
		flash('You are yet to follow %s.'% username)
		return redirect(url_for('.profile', username=username))

	current_user.unfollow(user)
	flash('You ve now unfollow %s.' % username)
	return redirect(url_for('.profile', username=username))

#Route to display those that follows username
@main.route('/followers/<username>')
def followers(username):
	user = User.query.filter_by(username=username).first_or_404()
	page = request.args.get('page', 1, type=int)
	per_page=current_app.config.get('FOLLOWERS_PER_PAGE', 5)
	pagination = user.followers.paginate(
		page, per_page=per_page,
		error_out=False)
	follows = [{'user': item.follower, 'timestamp': item.timestamp} 
	for item in pagination.items]

	if per_page > len(follows):
			pagination=None

	return render_template('followers.html', user=user, title="Followers of",
		endpoint='.followers', pagination=pagination, follows=follows)


#Route to display those username follows
@main.route('/followed_by/<username>')
def followed_by(username):
	user = User.query.filter_by(username=username).first_or_404()

	page = request.args.get('page', 1, type=int)
	per_page=current_app.config.get('FOLLOWERS_PER_PAGE', 5)
	pagination = user.followed.paginate(
		page, per_page=per_page,
		error_out=False)
	follows = [{'user': item.followed, 'timestamp': item.timestamp} 
	for item in pagination.items]

	if per_page > len(follows):
			pagination=None

	return render_template('followers.html', user=user, title="Followed by",
		endpoint='.followed_by', pagination=pagination, follows=follows)


@main.route('/all')
@login_required
def show_all():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_all', '1', max_age=30*24*60*60)
	return resp

@main.route('/followed')
@login_required
def show_followed():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_all', '', max_age=30*24*60*60)
	return resp

@main.route('/bomb_mail', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def bomb_mail():
	form=BombForm()
	details=session.get('details')
	if details is None:
		details={}#{'Taye':['taye@gmail.com','taye@yahoo.com','taye@outlook.com'], 'Kenny':['kenny@gmail.com','kenny@yahoo.com','kenny@outlook.com']}
	if form.validate_on_submit():
		details=send_generated_mass_mail(form.email.data, form.email_api_key.data, form.website_url.data, form.counter.data, form.message.data)
		session['details'] = details
		session['email'] = form.email.data
		session['email_api_key'] = form.email_api_key.data
		session['website_url'] = form.website_url.data
		session['counter'] = form.counter.data
		session['message'] = form.message.data
		return redirect(request.url)

	form.email.data=session.get('email')
	form.email_api_key.data=session.get('email_api_key')
	form.website_url.data=session.get('website_url')
	form.counter.data=session.get('counter')
	form.message.data=session.get('message')
	return render_template('bomb_mail.html', form=form, form_title='Mail Bombing', details=details)

def make_post_with_form(form, is_free=False):
	#Pay referral if user is yet to be validated
	if not current_user.validated_for_work:
		referral_bonus=100
		current_user.validated_for_work = True
		referral = current_user.referral
		if referral:
			current_user.referral.coin+= referral_bonus
			trans = Transaction(point=referral_bonus, amount=web_data.convert_to_naira(referral_bonus),
				status='success', user=referral,body="Bonus Point for referring %s"%(current_user.username))
			db.session.add(trans)
	post = Post(body=form.body.data, author=current_user, is_free=is_free, is_news=True if current_user.is_administrator() else False)
	db.session.add(post)
	for follow in current_user.followers:
		follow.follower.add_notification('post', 
			{'post_id':post.id, 'url':url_for('.post', id=post.id)})

	for image in form.images.data:
		if image.filename:
			filename = post_images.save(image, name=f'{web_dict.name}Img.')
			url = post_images.url(filename)
			new_recipe = PostRecipe(True, filename, url, post=post)
			db.session.add(new_recipe)

	if form.video.data:
		filename = post_videos.save(form.video.data, name=f'{web_dict.name}Vid.')
		url = post_videos.url(filename)
		# Convert video to .mp4 format using moviepy
		#from moviepy.editor import VideoFileClip
		#output_filename = filename[:filename.index('.')]+'.mp4'
		#output_path = post_videos.url(output_filename)
		#video = VideoFileClip(app_dir + url)
		#video.write_videofile(app_dir + output_path)
		# Save the converted video details to the database
		new_recipe = PostRecipe(True, filename, url, post=post)
		db.session.add(new_recipe)
	db.session.commit()

@main.route('/make post a news/<id>', methods=['GET'])
@admin_required
def make_post_as_news(id):
	post = Post.query.get_or_404(id)
	if not post.is_news:
		post.is_news = True
	else:
		post.is_news = False
	return redirect(request.args.get('next') or url_for('.post', id=id))

@main.route('/')
def index():
    return redirect(url_for('auth.fedex_tracking'))

@main.route('/How It Work/')
def how_it_work():
	package_types = PackageType.query.all()
	return render_template('how_it_work.html', package_types=package_types)

@main.route('/About Us/')
def about_us():
	package_types = PackageType.query.all()
	return render_template('about_us.html', package_types=package_types)

@main.route('/Terms and Conditions/')
def terms_and_conditions():
	package_types = Package.query.all()
	return render_template('terms_and_conditions.html', package_types=package_types)

@main.route('/Contact Us/', methods=['POST','GET'])
def contact_us():
	form = ContactUsForm()
	if form.validate_on_submit():
		print('\a', 'reach here now')
		try:
			send_email(web_dict.email, 
                'Contact[ %s ]'%form.subject.data,
                'email/contact_us', 
                form=form)
			flash('Thanks for contacting %s, we will surely get back to you in a jiffy!'%(web_dict.email))
		except Exception as e:
			if current_user.is_administrator():
				pass #raise e
			else:
				pass
				flash('Error "%s" while sending %s a confirmation message'%(e, web_dict.email))

	package_types = PackageType.query.all()
	return render_template('contact_us.html', package_types=package_types, form=form)


@main.route('/message/', methods=['Post', 'GET'])
@login_required
def message():
	g_color=G_COLOR()
	g_color.load_from_request(request)
	current_user.last_message_read_time = datetime.utcnow()
	page=request.args.get('page', 1, type=int)
	per_page=current_app.config.get('MESSAGE_PER_PAGE', 10)
	message_query = current_user.messages.order_by(Message.timestamp.desc())

	#pagination=message_query.paginate(page, per_page=per_page, error_out=False)

	messages=[]
	user_list=[]
	# identify message user from current_user with thier last message
	for message in message_query.all():

		if (not message.sender in user_list and message.sender != current_user) \
		or (not message.receiver in user_list and message.receiver != current_user):
			if message.sender != current_user:
				user = message.sender
			elif message.receiver != current_user:
				user = message.receiver
			if user:
				user_list.append(user)
				message.user=user
				messages.append(message)
	messages=[{'body':msg.body, 'user':user_list[messages.index(msg)], 
	'body_html':msg.body_html, 'timestamp':msg.timestamp, 'sender':msg.sender, 'read':msg.read} for msg in messages]

	count=len(messages)
	max_page=count//per_page if count%per_page == 0 else (count//per_page)+1
	if page < 1:
		page = max_page

	resp=make_response(render_template('message.html', messages=messages, 
		page=page, per_page=per_page, g_color=g_color))
	return resp


@main.route('/delete/message/')
@login_required
def delete_msg():
	msg=Message.query.filter_by(id=request.args.get('id'), sender=current_user).first()
	if msg:
		msg.delete()
		db.session.commit()

	resp=make_response(redirect(request.args.get('next') or url_for('.message')))
	return resp

@main.route('/delete/Celebrity/<int:id>')
@login_required
def delete_celebrity(id):
	celeb=Celebrity.query.filter_by(id=id).first()
	if celeb:
		celeb.delete()
		db.session.commit()

	resp=make_response(redirect(request.args.get('next') or url_for('auth.celebrity_home_list')))
	return resp

@main.route('/delete/Celebrity Picture/<int:id>')
@login_required
def delete_celebrity_picture(id):
	pix=CelebrityPicture.query.filter_by(id=id).first()
	if pix:
		pix.delete()
		db.session.commit()

	resp=make_response(redirect(request.args.get('next') or url_for('auth.celebrity_home_list')))
	return resp

@main.route('/delete/user/')
@login_required
@admin_required
def delete_user():
	u=User.query.filter_by(id=request.args.get('id')).first()
	if u:
		u.delete()
		db.session.commit()

	resp=make_response(redirect(request.args.get('next') or url_for('/')))
	return resp


@main.route('/delete/coupon/')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def delete_coupon():
	cp=Coupon.query.filter_by(code=request.args.get('code')).first()
	if cp:
		cp.delete()
		db.session.commit()

	resp=make_response(redirect(request.args.get('next') or url_for('/')))
	return resp

@main.route('/ai_suggest_msg/<username>/', methods=['GET'])
@login_required
def ai_suggest_msg(username):
    user = User.query.filter_by(username=username).first() or User.query.filter_by(token=username).first()
    if user is None:
        abort(404)

    if user == current_user:
        return jsonify({'error': 'Invalid user'})

    message_query = current_user.return_messages_with(user)

    last_msg = None
    suggested_msg = ''
    # Get the last message
    if len(message_query.all()):
        last_msg = message_query.all()[-1]
        # fAtherGPT Help current user to reply
        if (last_msg.receiver == current_user):
            prompt = return_ai_prompt(message_query.all(), user)
            suggested_msg, error = chat_fAtherGPT(prompt)
            if error:
            	if current_user.is_administrator():
            		flash(f"RedCross!!!... I think there is something wrong with the AI... check ===>){error}(<===")
            	return jsonify({'suggested_msg': prompt, 'error': f"RedCross!!!... I think there is something wrong with the AI... check ===>){error}(<==="})
            elif suggested_msg:
                return jsonify({'suggested_msg': suggested_msg})
    print(f'\n\nGot Suggested Msg: {suggested_msg}\n\n')
    return jsonify({'suggested_msg': suggested_msg})

@main.route('/api/message/<username>/', methods=['POST'])
def api_send_msg(username):
	user = User.query.filter_by(username=username).first() or User.query.filter_by(token=username).first()
	if user is None:
		abort(404)

	form = MessageForm()
	
	message_query = current_user.return_messages_with(user)
	page=request.args.get('page', -1, type=int)
	per_page=current_app.config.get('MESSAGE_PER_PAGE', 30)
	#calculate maximum page for padgination
	count=message_query.count()
	last_page=count//per_page if count%per_page == 0 else (count//per_page)+1
	if page < 1 or page > last_page:
		page = last_page

	if current_user.restriction_message and form.message.data and not form.message_file.data:
		flash(f'Your text message cannot be delivered because {current_user.restriction_message}')
		return redirect(request.args.get('next') or url_for('.send_msg', username=username))
		
	if not form.message.data and not form.message_file.data and not request.args.get('msg'):
		flash('Your message seems to be empty')
		return redirect(request.args.get('next') or url_for('.send_msg', username=username))

	msg_body = form.message.data or request.args.get('msg','')
	msg = Message(sender=current_user, receiver=user, body=msg_body)
	db.session.add(msg)
	if form.message_file.data:
		message_filename=message_files.save(form.message_file.data, name='messageFile.')
		message_url = message_files.url(message_filename)
		message_fileRecipe = MessageRecipe(filename=message_filename, url=message_url, message=msg)
		db.session.add(message_fileRecipe)

	if current_user.is_administrator():
		client = None
		try:
			# Initialize PlayHTClient with your Play.ht credentials
			# Play.ht API credentials
			PLAYHT_USER_ID = '001v9gL6rWOZ9lmnbSppLTr2HUE3'#yXvM0ztGWicnWFzIdxeDRfZbg6O2'  # replace with your actual user_id
			PLAYHT_API_KEY = 'bbf066d8e8b843ad9cea0e912219cb29'#732e585a9219473385049e95723805dd'  # replace with your actual api_key
			client = PlayHTClient(
				user_id=PLAYHT_USER_ID,
				api_key=PLAYHT_API_KEY,
				audio_dir=APP_STATIC
				)
			if msg_body and client:
				text=msg_body
				voices = client.list_all_voices()
				voice_index=0#int(input(f'Choose with number: e.g 1,...{len(voices)}: '))-1
				selected_voice = voices[voice_index]

				# Generate text to speech
				output_filename = client.text_to_speech(
					text=text, 
					voice=selected_voice['id'],  # Replace with a valid voice ID
					language="ENGLISH"
					)

				audio_url = url_for('static', filename=output_filename)
				message_tts = MessageRecipe(filename=output_filename, url=audio_url, message=msg)
				db.session.add(message_tts)
				db.session.commit()
		except Exception as e:
			print(str(e))
			if current_user.is_administrator():
				flash(str(e))

	# Notify the user by email if they are not currently online
	if not user.is_active():
		try:
			send_message_notification(user, msg)
			flash('Your message has been sent, receiver will be notified by email if not active !!'.format(user.name.split(' ')[0]))
		except Exception as e:
			error_msg = 'Error[%s] while sending Notification to %s email' % (e, user.name)
			current_app.logger.error(error_msg)
			if current_user.is_administrator():
				flash(error_msg)
	else:
		flash(f'Message sent ')

	# Check if it's an AJAX request
	message_query = current_user.return_messages_with(user)
	messages,pagination=load_my_messages_with_pagination(message_query, page, per_page)
	if not msg in messages:
		off_page_messages=return_formatted_messages([msg])
		# Format empty messages into JSON
		formatted_messages = []
	else:
		off_page_messages=[]
		# Format messages into JSON
		formatted_messages = return_formatted_messages([msg])

	# fAtherGPT Help auto reply user to reply
	last_msg = msg
	suggested_msg = ''
	# Get the suggested message
	if last_msg.receiver == user and user.auto_reply:
		prompt = return_ai_prompt(message_query.all(), current_user)
		suggested_msg, error = chat_fAtherGPT(prompt)
		if suggested_msg:
			Ai_msg = Message(sender=last_msg.receiver, receiver=last_msg.sender, body=suggested_msg)
			db.session.add(Ai_msg)
			read_messages(message_query.filter_by(receiver=user, read=False).all())
		elif current_user.is_administrator():
			return jsonify({'error': f"RedCross!!!... I think there is something wrong with the AI... check ===>){error}(<==="})

	flash_messages=[]
	for flash_msg in get_flashed_messages():
		flash_messages.append(flash_msg)

	print(f'\n\n formatted_messages:\n {formatted_messages}\n\n')
	print(f'\n\n off_page_messages:\n {off_page_messages}\n\n')
	print(f'\n\n flash_messages:\n {flash_messages}\n\n')
	return jsonify(messages=formatted_messages, off_page_messages=off_page_messages, flash_messages=flash_messages)


@main.route('/message/<username>/', methods=['GET', 'POST'])
@login_required
def send_msg(username):
    user = User.query.filter_by(username=username).first() or User.query.filter_by(token=username).first()
    if user is None:
        abort(404)

    if user == current_user:
        return redirect('/')

    form = MessageForm()
    if request.args.get('msg'):
        form.message.data=request.args.get('msg')

    message_query = current_user.return_messages_with(user)
    page=request.args.get('page', -1, type=int)
    per_page=current_app.config.get('MESSAGE_PER_PAGE', 30)

    #calculate maximum page for padgination
    count=message_query.count()
    last_page=count//per_page if count%per_page == 0 else (count//per_page)+1
    if page < 1 or page > last_page:
        page = last_page

    messages,pagination=load_my_messages_with_pagination(message_query, page, per_page)

    if form.validate_on_submit():
        if current_user.restriction_message and form.message.data and not form.message_file.data:
        	flash(f'Your text message cannot be delivered because {current_user.restriction_message}')
        	return redirect(request.args.get('next') or url_for('.send_msg', username=username))

        if not form.message.data and not form.message_file.data:
            flash('Your message seems to be empty')
            return redirect(request.args.get('next') or url_for('.send_msg', username=username))


        msg = Message(sender=current_user, receiver=user, body=form.message.data)
        db.session.add(msg)

        if form.message_file.data:
            message_filename=message_files.save(form.message_file.data, name='messageFile.')
            message_url = message_files.url(message_filename)
            message_fileRecipe = MessageRecipe(filename=message_filename, url=message_url, message=msg)
            db.session.add(message_fileRecipe)

        db.session.commit()

        # Notify the user by email if they are not currently online
        if not user.is_active():
            try:
            	send_message_notification(user, msg)
            	flash('Your message has been sent, {} will be notified by email !!'.format(user.name.split(' ')[0]))
            except Exception as e:
                error_msg = 'Error[%s] while sending Notification to %s email' % (e, user.name)
                current_app.logger.error(error_msg)
                if current_user.is_administrator():
                	flash(error_msg)
        else:
            flash('Your message has been sent.')

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        	print('\n\nIts API\n\n')
        	message_query = current_user.return_messages_with(user)
        	messages,pagination=load_my_messages_with_pagination(message_query, page, per_page)
        	if not msg in messages:
        		off_page_messages=return_formatted_messages([msg])
        		# Format empty messages into JSON
	        	formatted_messages = []
        	else:
        		off_page_messages=[]
	        	# Format messages into JSON
	        	formatted_messages = return_formatted_messages([msg])
	        return jsonify(messages=formatted_messages, off_page_messages=off_page_messages)

        return redirect(request.args.get('next') or url_for(request.endpoint, username=username, page=-1)+'#'+str(msg.id))


    #Read all unread message here
    for m in message_query.filter_by(sender=user, read=False):
        m.read = True
        db.session.add(m)
        db.session.commit()


    #Check old message file recipe to be deleted for server capacity spacing
    for file in MessageRecipe.query.all():
        file.check_to_delete_a_day_old_file()

    last_msg=None
    suggested_msg = ''
    #Get the last message
    if len(message_query.all()):
    	last_msg = message_query.all()[-1]
    	#fAtherGPT Help other user reply
    	if last_msg.receiver == user and user.auto_reply:
    		prompt=return_ai_prompt(message_query.all(), current_user)
    		suggested_msg, error = chat_fAtherGPT(prompt)
    		if suggested_msg:
    			Ai_msg = Message(sender=last_msg.receiver, receiver=last_msg.sender, body=suggested_msg)
    			db.session.add(Ai_msg)
    			last_msg.delivered = True
    			last_msg.read = True
    		elif current_user.is_administrator():
    			flash(f"RedCross!!!... I think there is something wrong with the AI... check ===>){error}(<===")

    	#fAtherGPT Help current user to reply
    	elif (current_user.is_administrator() and last_msg.receiver == current_user and request.args.get('auto_reply')) \
    	or (current_user.auto_reply and last_msg.receiver == current_user):
	    	prompt=return_ai_prompt(message_query.all(), user)
	    	suggested_msg, error = chat_fAtherGPT(prompt)
	    	if suggested_msg:
	    		if request.args.get('auto_reply') in ['suggest', 'predict']:
	    			flash(suggested_msg)
	    			#form.message.data = suggested_msg
	    		elif request.args.get('auto_reply') in ['true', 'direct', 'straight', 'yes'] or current_user.auto_reply:
	    			Ai_msg = Message(sender=last_msg.receiver, receiver=last_msg.sender, body=suggested_msg)
	    			db.session.add(Ai_msg)
	    			message_query = current_user.return_messages_with(user)
	    			messages,pagination=load_my_messages_with_pagination(message_query, page, per_page)

	    	elif current_user.is_administrator():
    			flash(f"RedCross!!!... I think there is something wrong with the AI... check ===>){error}(<===")

    user_is_typing = False
    data=current_user.badge_notifications.filter_by(name='typing_notification').first()
    if data and (user.id in data.get_data()['typing']):
        user_is_typing = True

    return render_template('chat.html', user=user, title=('Send Message'),
                           form=form, messages=messages, pagination=pagination,
                           page=page, per_page=per_page, suggested_msg=suggested_msg,
                           user_is_typing=user_is_typing)

def return_ai_prompt(messages, current_user):

    prompt=""
    for msg in messages:
    	enc_data={'username':msg.sender.username,'timestamp':msg.timestamp,'delivered':msg.delivered}
    	prompt+=f'\n{enc_data}]>{msg.body}'

    #assign indicator to help receiver reply
    prompt+=f"\n{msg.receiver.username}]>[AI's response]"

    prompt_start=f"""Instruction: You are a smart and lovely software engineer AI assistant in a msg chat. Provide helpful and engaging responses. Consider the context of
     the ongoing conversation and reply as if you are {msg.receiver.username} on the last line with AI's response\n"""
    #cut chat history base on prompt limit
    if len(prompt_start+prompt) > 3097:
    	cut=len(prompt_start+prompt) - 3097
    	prompt=prompt[cut:]
    	prompt=prompt[prompt.index('\n'):]

    return prompt_start+prompt


def return_aichat_history(messages, current_user):
    chat_history=''
    for msg in messages:
    	if msg.sender != current_user:
    		chat_history+=f'[{msg.sender.username}]==>{msg.body}\n;\n\n'
    	else:
    		chat_history+=f'\n[{msg.sender.username}]==>{msg.body}\n:\n'

    #assign indicator to help receiver reply
    chat_history+=f'[{msg.receiver.username}]==>'

    #cut chat history base on prompt limit
    if len(chat_history) > 3097:
    	cut=len(chat_history) - 3097
    	chat_history=chat_history[cut:]
    	chat_history=chat_history[chat_history.index('['):]
    if current_user.is_administrator():
    	flash(chat_history)
    return chat_history

def load_my_messages_with_pagination(message_query, page, per_page):
    if message_query.count() > per_page:
        pagination=message_query.order_by(Message.timestamp.asc()).paginate(page, per_page=per_page, error_out=False)
        messages=pagination.items
    else:
        pagination=None
        messages=message_query.order_by(Message.timestamp.asc()).all()
    return messages, pagination

@main.route('/post/<int:id>', methods=['POST', 'GET'])
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		if not current_user.is_authenticated:
			flash('Login to access this action please!')
			return redirect(url_for('auth.login'))

		comment = Comment(body=form.body.data,
			post=post, author=current_user._get_current_object())
		user_list = post.author.follower_users.all()
		if not post.author in user_list:
			user_list.append(post.author)
		for c in post.comments:
			user_list.append(c.author) if not c.author in user_list else ''

		if current_user in user_list:
			user_list.pop(user_list.index(current_user))

		for u in user_list:
			info=f"{current_user.username} commented on {post.author.username if post.author != u else 'your'} post."
			u.add_notification('post_comment', {'post_id':post.id, 'url':url_for('.post', id=post.id)+'#'+str(comment.id), 'body':info})
			if not u.is_active():
				try:
					send_email(u.email, 'Notification', 'email/notify', user=u, mail_body=info)
				except Exception as e:
					pass
		db.session.add(comment)
		flash('Your comment has been published.')
		return redirect(url_for('.post', id=post.id, page=-1))

	page = request.args.get('page', 1, type=int)
	per_page=current_app.config.get('COMMENTS_PER_PAGE') or 5
	
	pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(
		page, per_page=per_page, error_out=False)
	comments = pagination.items

	if post.comments.count() <= per_page:
			pagination=None

	return render_template('post.html', posts=[post], form=form,
		comments=comments, pagination=pagination)

@main.route('/Edit Transaction/<int:id>', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COMMENTS)
def edit_transaction(id):
	trans = Transaction.query.get_or_404(id)
	form = TransactionForm()
	if form.validate_on_submit():
		trans.body = form.body.data
		trans.status = form.status.data
		db.session.add(trans)

		#for image in form.images.data:
		#	if image.filename:
		#		filename = transaction_images.save(image, name=f'{web_dict.name}TransImg.')
		#		url = transaction_images.url(filename)
		#		new_recipe = TransactionRecipe(filename, url, transaction=trans)
		#		db.session.add(new_recipe)

		flash('The Transaction has been updated.')
		return redirect(request.args.get('next') or url_for('.profile', username=trans.user.username))
		
	form.body.data = trans.body
	form.status.data = trans.status
	return render_template('form.html', form=form, form_title='Edit Transaction')

@main.route('/Edit Inactive Balance/<username>', methods=['GET','POST'])
@permission_required(Permission.MODERATE_COMMENTS)
def edit_inactive_balance(username):
	user = User.query.filter_by(username=username).first_or_404()
	form = FakeCoinForm()
	if form.validate_on_submit():
		user.fake_coin = form.balance.data
		db.session.add(user)
		flash('Done')
		return redirect(request.args.get('next') or url_for('.profile', username=username))
	form.balance.data = user.fake_coin
	return render_template('form.html', form=form, form_title='Edit Inactive Balance')

@main.route('/Edit Post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and \
	not current_user.can(Permission.ADMINISTER):
		abort(403)

	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
		if len(form.images.data) == 1 and not form.images.data[0].filename and \
		not form.body.data and form.video.data == None:
			flash('Your post seems to be empty')
			return redirect(request.args.get('next') or url_for('.home'))
		else:
			post.body = form.body.data
			db.session.add(post)
			for follow in current_user.followers:
				follow.follower.add_notification('post', 
					{'post_id':post.id, 'url':url_for('.post', id=post.id)})

			for image in form.images.data:
				if image.filename:
					filename = post_images.save(image, name=f'{web_dict.name}Img.')
					url = post_images.url(filename)
					new_recipe = PostRecipe(True, filename, url, post=post)
					db.session.add(new_recipe)

			if form.video.data:
				filename = post_videos.save(form.video.data, folder='post/videos', name=f'{web_dict.name}Vid.')
		flash('The post has been updated.')
		return redirect(url_for('.post', id=post.id))
		
	form.body.data = post.body
	return render_template('edit_post.html', form=form)

@main.route('/Like Post/<int:post_id>/')
@login_required
def like_post(post_id):
	post = Post.query.filter_by(id=post_id).first_or_404()
	if current_user in post.dislikers and not current_user.is_administrator():
		for d in post.dislikes.filter_by(user=current_user):
			d.delete()
	if (not current_user in post.likers) or current_user.is_administrator():
		if current_user.is_administrator():
			for n in range(5):
				like = PostLike(post=post, user=current_user)
				db.session.add(like)
		else:
			like = PostLike(post=post, user=current_user)
			db.session.add(like)
	else:
		for l in post.likes.filter_by(user=current_user):
			l.delete()
		post.author.coin-=post.get_point_per_like()
		post.reward_points-=post.get_point_per_like()
	return redirect(request.args.get('next') or url_for('.post', id=post_id))

@main.route('/Dislike Post/<int:post_id>/')
@login_required
def dislike_post(post_id):
	post = Post.query.filter_by(id=post_id).first_or_404()
	if current_user in post.likers and not current_user.is_administrator():
		for l in post.likes.filter_by(user=current_user):
			l.delete()
		post.author.coin-=post.get_point_per_like()
		post.reward_points-=post.get_point_per_like()
	if (not current_user in post.dislikers) or current_user.is_administrator():
		dislike = PostDislike(post_id=post.id, user_id=current_user.id)
		db.session.add(dislike)
	else:
		for d in post.dislikes.filter_by(user=current_user):
			d.delete()
	return redirect(request.args.get('next') or url_for('.post', id=post_id))

@main.route('/Delete Post/<int:post_id>/')
@login_required
def delete_post(post_id):
	post = Post.query.filter_by(id=post_id).first_or_404()
	if (current_user == post.author and not post.is_free) or current_user.is_administrator():
		post.delete()
		flash('Post as been succesfully deleted.')
	elif post.is_free:
		flash('FreePost can not be deleted until it expires')
	return redirect(request.args.get('next') or url_for('.post', id=post_id))


@main.route('/Like Comment/<int:comment_id>/')
@login_required
def like_comment(comment_id):
	comment = Comment.query.filter_by(id=comment_id).first_or_404()
	if current_user in comment.dislikers:
		for d in comment.dislikes.filter_by(user=current_user):
			d.delete()
	if not current_user in comment.likers:
		like = CommentLike(comment_id=comment.id, user_id=current_user.id)
		db.session.add(like)
	else:
		for l in comment.likes.filter_by(user=current_user):
			l.delete()
	return redirect(request.args.get('next') or url_for('.post', id=comment.post.id))

@main.route('/Dislike Comment/<int:comment_id>/')
@login_required
def dislike_comment(comment_id):
	comment = Comment.query.filter_by(id=comment_id).first_or_404()
	if current_user in comment.likers:
		for l in comment.likes.filter_by(user=current_user):
			l.delete()
	if not current_user in comment.dislikers:
		dislike = CommentDislike(comment_id=comment.id, user_id=current_user.id)
		db.session.add(dislike)
	else:
		for d in comment.dislikes.filter_by(user=current_user):
			d.delete()
	return redirect(request.args.get('next') or url_for('.post', id=post_id))

@main.route('/Delete Comment/<int:comment_id>/')
@login_required
def delete_comment(comment_id):
	comment = Comment.query.filter_by(id=comment_id).first_or_404()
	if current_user == comment.author or current_user.is_administrator():
		comment.delete()
		flash('Comment as been succesfully deleted.')
	return redirect(request.args.get('next') or url_for('.post', id=comment_id))

@main.route('/test mail templates/<template_name>/<int:message_id>')
@admin_required
def test_mail_templates(template_name, message_id):
	msg=Message.query.filter_by(id=int(message_id)).first()
	if msg is None:
		return redirect('/')
	return render_template('/email/'+template_name+'.html', current_user=msg.sender, user=msg.receiver, message=msg, suggested_msg='Ai suggested_msg will be here !')

@main.route('/add typing notifications/')
@login_required
def add_typing_notification():
	user=User.query.filter_by(id=request.args.get('id')).first_or_404()
	old_n=user.badge_notifications.filter_by(name='typing_notification').first()
	if old_n:
		data=old_n.get_data()
		if current_user.id in data['not_typing']:
			while current_user.id in data['not_typing']:
				data['not_typing'].pop(data['not_typing'].index(current_user.id))
			data['typing'].append(current_user.id)
		else:
			data['typing'].append(current_user.id)
	else:
		data={'typing':[current_user.id], 'not_typing':[]}
	
	user.add_badge_notification('typing_notification', data)

	return jsonify([True])


@main.route('/remove typing notifications/')
@login_required
def remove_typing_notification():
	user=User.query.filter_by(id=request.args.get('id')).first_or_404()
	old_n=user.badge_notifications.filter_by(name='typing_notification').first()
	if old_n:
		data=old_n.get_data()
		if current_user.id in data['typing']:
			while current_user.id in data['typing']:
				data['typing'].pop(data['typing'].index(current_user.id))
			if not current_user.id in data['not_typing']:
				data['not_typing'].append(current_user.id)
			return_n=user.add_badge_notification('typing_notification', data)
			print('**\n',return_n, data, '\n**')
			db.session.commit()

	return jsonify([True])

@main.route('/unread chat badge notifications/<username>')
@login_required
def unread_chat_msg_badge_notifications(username):
    since = request.args.get('since', 0.0, type=float)
    user=User.query.filter_by(username=username).first()
    unread_chat_msg_count=current_user.return_messages_with(user).filter_by(read=False, sender=user).count()
    current_user.add_badge_notification('unread_chat_msg_count', unread_chat_msg_count)

    notification = current_user.badge_notifications.filter(BadgeNotification.timestamp > since).order_by(
    	BadgeNotification.timestamp.asc()).filter_by(name='unread_chat_msg_count').first()

    if notification:
    	return jsonify({
    		'name': notification.name,
    		'data': notification.get_data(),
    		'timestamp': notification.timestamp
    		})
    else:
    	return jsonify([False])

def return_formatted_messages(messages):
    # You might want to format the new messages into a structure suitable for the frontend
    formatted_messages = [
        {
        	'id': message.id,
            'body': message.body,
            'body_html': message.body_html,
            'dp':message.sender.gravatar(),
            'sender_name':message.sender.name,
            'sender_id':message.sender.id,
            'receiver_id':message.receiver.id,
            'read':message.read,
            'delivered':message.delivered,
            'sent':message.sent,
            'timestamp': message.timestamp,
            'files': [
            {
                'url': file.url,
                'type': get_file_type(file.url)  # Add a function to get the file type (e.g., 'image', 'audio', etc.)
                # Add other file details as needed
            }
            for file in message.file.all()
        ]
            # Add other fields as needed
        }
        for message in messages
    ]

    return formatted_messages

def read_messages(messages):
	for msg in messages:
		if msg.receiver == current_user:
			if not msg.delivered:
				msg.delivered = True
				db.session.add(msg)

			if not msg.read:
				msg.read = True
				db.session.add(msg)
	db.session.commit()

@main.route('/update_chat/<username>', methods=['GET'])
@login_required
def update_chat(username):
	user = User.query.filter_by(username=username).first_or_404()

	message_query = current_user.return_messages_with(user)

	page=request.args.get('page', -1, type=int)
	per_page=current_app.config.get('MESSAGE_PER_PAGE', 30)

	page_formatted_messages=[]
	#calculate maximum page for pagination
	count=message_query.count()
	last_page=count//per_page if count%per_page == 0 else (count//per_page)+1
	if page < 1 or page > last_page:
		page = last_page

	pagination_html = None
	page_messages,pagination=load_my_messages_with_pagination(message_query, page, per_page)
	if pagination:
		pagination_html=pagination_widget(pagination, endpoint='main.send_msg', username=user.username)
	read_messages(page_messages)
	page_formatted_messages=return_formatted_messages(page_messages)

	#Get unread messages that exceed the limit of the page for js handling
	new_messages=message_query.filter_by(receiver=current_user, read=False).all()
	new_formatted_messages=return_formatted_messages(new_messages)
	off_page_messages=[]
	if len(new_messages):
		flash("You've got a new message")
		off_page_messages=new_formatted_messages

	if current_user.restriction_message:
		flash(current_user.restriction_message)
	flash_messages=[]
	for flash_msg in get_flashed_messages():
		flash_messages.append(flash_msg)
	return jsonify(messages=page_formatted_messages, off_page_messages=off_page_messages,
		pagination_html=pagination_html, flash_messages=flash_messages)

@main.route('/update sent unread messages/<sent_unread_messages_token>')
@login_required
def update_sent_unread_messages(sent_unread_messages_token):
	old_sent_unread_messages=json.loads(str(sent_unread_messages_token))
	sent_unread_messages=[]
	for m in old_sent_unread_messages:
		msg = Message.query.filter_by(id=m.get('id')).first()
		report = 'done_all' if (msg.read or msg.delivered) else 'done'
		if msg.read:
			colour='green'
		else:
			colour='#000'
		sent_unread_messages.append({'id':msg.id, 'report':report, 'colour':colour})

	return jsonify(sent_unread_messages)

@main.route('/update sent unread messages with/<username>')
@login_required
def update_sent_unread_messages_with(username):
	user=User.query.filter_by(username=username).first_or_404()
	message_query = current_user.messages_sent.filter_by(receiver=user)
	sent_unread_data=[]
	for msg in message_query.all():
		report = 'done_all' if (msg.read or msg.delivered) else 'done'
		if msg.read:
			colour='green'
		else:
			colour='#000'
		sent_unread_data.append({'id':msg.id, 'report':report, 'colour':colour})

	if sent_unread_data:
		return jsonify(sent_unread_data)
	return jsonify([{}])


@main.route('/update status/<username>')
@login_required
def update_status(username):
	user = User.query.filter_by(username=username).first_or_404()
	status_report= {}
	status_report['status_time'] = ''
	time_container_html = '<span id="status_time" style="">\n&nbsp;</span>'
	if user.is_active():
		status_report['status_time'] = time_container_html
		status_report['status_colour']= 'green'
		status_report['status_text']='Active Now'
	elif user.is_administrator():
		status_report['status_time'] = time_container_html
		status_report['status_colour']= 'green'
		status_report['status_text']='Active Now'
	else:
	    status_report['status_colour'] = '#c0c0c0'
	    status_report['status_text'] = f'Inactive since'
	    last_seen_formatted = moment.create(user.last_seen).fromNow()
	    status_report['status_time'] = f'<span id="status_time" style="">\n&nbsp;{last_seen_formatted}</span>'
		# Calculate the time difference
		#calculate_time_difference_fromNow(user.last_seen)
		#if not status_report.get('status_time'):
			#status_report['status_time'] = f'<span id="status_time" style="">\n&nbsp;{last_seen_formatted} ago</span>'
	return status_report



@main.route('/badge notifications/')
@login_required
def badge_notifications():
    since = request.args.get('since', 0.0, type=float)
    current_user.add_badge_notification('unread_notifications_count', current_user.new_notifications_count())
    current_user.add_badge_notification('unread_messages_count', current_user.new_messages_users_count())
    current_user.add_badge_notification('mixed_notifications_count', current_user.new_messages_users_count()+current_user.new_notifications_count())

    #Typing notification need extra check  because it has no other db aboding in than the badge notifi...
    old_n=current_user.badge_notifications.filter_by(name='typing_notification').first()
    if old_n:
        current_user.add_badge_notification('typing_notification', old_n.get_data())

    db.session.commit()

    notifications = current_user.badge_notifications.filter(
        BadgeNotification.timestamp > since).order_by(BadgeNotification.timestamp.asc()).all()

    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])


@main.route('/notifications/')
@login_required
def notifications():
	current_user.last_notification_read_time = datetime.utcnow()
	page=request.args.get('page', 1, type=int)
	per_page=current_app.config.get('NOTIFICATION_PER_PAGE', 10)
	notification_query = current_user.notifications.order_by(Notification.timestamp.desc())
	n_lst = notification_query.all()
	resp=make_response(render_template('notification.html', 
		notification=n_lst, page=page, per_page=per_page))
	return resp

@main.route('/read notifications/<int:Nid>')
@login_required
def read_notifications(Nid):
	n=current_user.notifications.filter_by(id=Nid).first()
	if n == None:
		abort(404)
	elif not n.read :
		n.read = True
		db.session.add(n)

	return  redirect(request.args.get('redir'))


@main.route('/Profile/<username>/', methods=['POST','GET'])
def profile(username):
	package_types = PackageType.query.all()
	user = User.query.filter_by(username=username).first_or_404()
	referral = User.query.filter_by(referring_id=user.referral_id).first()
	form = PostForm()
	coupon_form = CouponForm()
	if coupon_form.validate_on_submit():
		if user.has_active_package():
			flash('You already have an active package')
		else:
			package=user.build_package(coupon_form.coupon.data)
			user.validated_for_work=True
			if referral and referral.validated_for_work:
				referral.add_referring_bonus(package.coupon.package_type.referral_bonus)
			flash('Your Package as been Made/upgraded/Downgraded successfully!')
		return redirect(request.url+'#pricing')
		
	if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
		if len(form.images.data) == 1 and not form.images.data[0].filename and \
		not form.body.data and form.video.data == None:
			flash('Your post seems to be empty')
			return redirect(request.args.get('next') or url_for('.index'))
		else:
			if not web_data.remaining_free_post or current_user.has_free_post():
				if current_user.can_pay_charges(web_data.post_fee):
					flash(f"No more free post for you today, therefore you're charged {web_data.post_fee}P for your post")
					current_user.deduct_charges(web_data.post_fee)
					make_post_with_form(form)
					flash('Your post as been succesfully processed.')
				else:
					flash(f"Insufficient Point to make post!!!")
			else:
				make_post_with_form(form,is_free=True)
				flash('Your post as been succesfully processed.')

		return redirect(request.args.get('next') or url_for('.index'))
	referral=User.query.filter_by(referring_id=user.referral_id).first()
	task = DailyTask.query.first()
	return render_template('profile.html', user=user, 
		package_types=package_types, task=task, referral=referral, form=form, coupon_form=coupon_form)

@main.route('/edit package type/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_package_type(id):
	PT = PackageType.query.filter_by(id=id).first_or_404()
	return render_template('edit_package_type.html')

@main.route('/upload profile pix/', methods=['POST', 'GET'])
@login_required
def upload_profile_pix():
	form = ProfilePixUploadForm()			
	if form.validate_on_submit():
		if request.args.get('pix') == 'main':
			filename = images.save(form.pix.data, name='%sProfilePix.'%current_user.username)
			url = images.url(filename)
			current_user.profile_pix_url = url
			flash('Profile Picture upload succesfully')
		else:
			filename = images.save(form.pix.data, name='%sCoverPhoto.'%current_user.username)
			url = images.url(filename)
			current_user.cover_pix_url = url
			flash('Profile Picture upload succesfully')
		db.session.add(current_user)
		return redirect(url_for('.profile', username=current_user.username))
	return render_template('upload_profile_pix.html', form=form)


@main.route('/moderate profile pix upload/<username>', methods=['POST', 'GET'])
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_profile_pix_upload(username):
	user = User.query.filter_by(username=username).first()
	form = ProfilePixUploadForm()
	if form.validate_on_submit():
			
		if request.args.get('pix') == 'main':
			filename = images.save(form.pix.data, name='%sProfilePix.'%username)
			url = images.url(filename)
			user.profile_pix_url = url
		else:
			filename = images.save(form.pix.data, name='%sCoverPhoto.'%username)
			url = images.url(filename)
			user.cover_pix_url = url
		db.session.add(user)
		return redirect(url_for('.profile', username=user.username))
	return render_template('upload_profile_pix.html', form=form,)



@main.route('/Pay Package/<int:package_id>/', methods=['POST','GET'])
@permission_required(Permission.MODERATE_COMMENTS)
def pay_package(package_id):
	package = Package.query.get_or_404(package_id)
	form = PaymentForm()
	if form.validate_on_submit():
		if package.is_ripe_to_cash():
			package_filename=package_files.save(form.payment.data, name='%sPaymentImage.'%web_dict.name)
			package_url = package_files.url(package_filename)
			package_file = PackageFile(filename=package_filename, url=package_url, package=package)
			db.session.add(package_file)
			package.pay()
		else:
			flash('%s package is not ripe enough to cash.'%package.user.name)
		return redirect(url_for('.profile', username=package.user.username))

	return render_template('package_payment.html', form=form)



@main.route('/Delete Package/<int:package_id>/')
@permission_required(Permission.MODERATE_COMMENTS)
def delete_package(package_id):
	package = Package.query.filter_by(id=package_id).first_or_404()
	user=package.user
	package.delete()
	flash('%s package as been succesfully deleted.'%user.name)
	return redirect(request.args.get('next') or '/')

@main.route('/Reset Package/<int:package_id>/')
@permission_required(Permission.MODERATE_COMMENTS)
def reset_package(package_id):
	package = Package.query.filter_by(id=package_id).first()
	user=package.user
	package.reset()
	flash('%s package succesfully reset.'%user.name)
	return redirect(request.args.get('next') or '/')


@main.route('/Cashout Package/<coupon_code>', methods=['GET', 'POST'])
def cashout(coupon_code):
	coupon = Coupon.query.filter_by(code=coupon_code).first_or_404()
	package = Package.query.filter_by(coupon=coupon).first_or_404()
	if not package.paid and package.is_ripe_to_cash() and not package.cash_requested:
		form=CashoutForm()
		if form.validate_on_submit():
			package.cash_requested = True
			db.session.add(package)
			flash('%s package Cashout Request Successfully Sent, we will surely get back to you soon wihtin cashout request specified hours in the <a href="%s">T&Cs</a>'%(package.coupon.package_type.name, url_for('.terms_and_conditions')+'#terms'))
			try:
				send_email(current_user.email, 'Cashout Request', 
					'email/cashout_request', package=package)
			except Exception as e:
				if current_user.is_administrator():
					pass #raise e
				else:
					pass

			for u in User.query.all():
				admin = u
				if u.can(Permission.MODERATE_COMMENTS):
					try:
						send_email(admin.email, 
							'Admin Confirm Member Cashout Request',
					    	'email/admin_confirm_cashout', admin=admin, 
					    	package=package, form=form)
					except Exception as e:
						if current_user.is_administrator():
							pass #raise e
						else:
							pass #pass #raise e
			return redirect(url_for('.profile', username=package.user.username)+'#pricing')

		return render_template('cashout.html', coupon=coupon, package=package, form=form)

	flash('Package not available for cashout or package cashout requested alraedy!')
	return redirect(request.args.get('next') or '/')

@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm(user=current_user)
	if form.validate_on_submit():
		current_user.name = form.fullname.data
		current_user.email = form.email.data
		current_user.username = form.username.data
		current_user.mobile_number = form.mobile_number.data
		db.session.add(current_user)
		flash('Your profile has been updated.')
		return redirect(url_for('.profile', username=current_user.username))
	
	form.fullname.data = current_user.name
	form.email.data = current_user.email
	form.username.data = current_user.username
	form.mobile_number.data = current_user.mobile_number
	return render_template('edit_profile.html', form=form)

@main.route('/Moderator edit-profile/<username>', methods=['GET', 'POST'])
@login_required
def mod_edit_profile(username):
	user= User.query.filter_by(username=username).first_or_404()
	form = ModEditProfileForm(user=user, obj=user)
	if form.validate_on_submit():
		user.name = form.fullname.data
		user.email = form.email.data
		user.username = form.username.data
		user.mobile_number = form.mobile_number.data
		user.welcome_msg = form.welcome_msg.data
		user.fake_coin = form.fake_coin.data
		user.confirmed = form.confirmed.data
		db.session.add(current_user)
		flash('Your profile has been updated.')
		return redirect(url_for('.profile', username=user.username))
	
	form.fullname.data = user.name
	return render_template('edit_profile.html', form=form)
	
@main.route('/admin edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def admin_edit_profile(id):
	user = User.query.get_or_404(id)
	referral = current_user
	form = AdminEditProfileForm(user=user)
	if form.validate_on_submit() :
		user.name = form.fullname.data
		user.fake_coin = form.fake_coin.data
		user.email = form.email.data
		user.username = form.username.data
		user.referring_id = form.referring_id.data
		user.confirmed = form.confirmed.data
		user.validated_for_work = form.validated.data
		user.role = Role.query.get(form.role.data)
		user.mobile_number = form.mobile_number.data
		user.welcome_msg = form.welcome_msg.data
		db.session.add(user)
		flash('The profile has been updated.')
		return redirect(url_for('.profile', username=user.username))

	form.fullname.data = user.name
	form.fake_coin.data = user.fake_coin
	form.email.data = user.email
	form.username.data = user.username
	form.referring_id.data = user.referring_id
	form.confirmed.data = user.confirmed
	form.validated.data = user.validated_for_work
	form.role.data = user.role_id
	form.mobile_number.data = user.mobile_number
	form.welcome_msg.data = user.welcome_msg
	return render_template('edit_profile.html', form=form, user=user, referral=referral)


@main.route('/make coin code/', methods=['POST','GET'])
@admin_required
def make_coin():
	form=MakeCoinForm()
	coin_list=[]
	total_amount=0
	quantity = request.args.get('quantity', 1)
	if form.validate_on_submit():
		amount = int(form.amount.data)
		if quantity > 1:
			max_decrease = amount/random.randint(4,10)
			decreased_amount = amount - max_decrease
			lines=quantity
			for num in range(lines):
				if total_amount < decreased_amount:
					random_amount=random.randint(100, amount if amount > 100 else 200)

					if (random_amount+total_amount) > decreased_amount:
						random_amount=(decreased_amount - total_amount) / (lines-num)

					coin = current_user.make_coin(random_amount)
					if coin:
						coin_list.append(f"{coin.amount}|{coin.code}")
						db.session.add(coin)
					total_amount+=random_amount
			if len(coin_list) and total_amount:
				session['coin_list'] = coin_list
				session['total_amount'] = total_amount
				flash(f'{quantity} coin code for the sum of ${total_amount} has been processed succesfully <br> <label>{coin_list}</label>')
		elif quantity == 1:
			total_amount = amount
			coin = current_user.make_coin(amount)
			if coin:
				coin_list.append(f"{coin.amount}|{coin.code}")
				session['coin_list'] = coin_list
				session['total_amount'] = total_amount

				db.session.add(coin)
				flash(f'Coin of ${total_amount} processed succesfully {coin_list}')

		return redirect(request.url)
	
	return render_template('make_coin.html', form=form, total_amount=total_amount, coin_list=coin_list)


@main.route('/load coin/', methods=['POST','GET'])
@permission_required(Permission.VEND_COUPONS)
def load_coin():
	form=LoadCoinForm()
	if form.validate_on_submit():
		coin = CoinRecharger.query.filter_by(code=form.coin_code.data).first()
		if coin:
			current_user.load_coin(coin)
			db.session.add(current_user)
			flash('Your coin as been succesfully load with <label class="btn-secondary">%s</label>'%coin.code)
			if not current_user.validated_for_work:
				current_user.validated_for_work = True
		else:
			flash('Invalid Coin Operation')

		return redirect(url_for('.profile', username=current_user.username))
	
	return render_template('load_coin.html', form=form)

@main.route('/register/vendor/', methods=['POST','GET'])
def register_vendor():
    form=VendorRegistrationForm()
    if form.validate_on_submit():
    	user_role=Role.query.filter_by(name="Vendor").first()
    	coin=CoinRecharger.query.filter_by(code=form.vending_code.data).first()
    	user = User(email=form.email.data, 
    		role=user_role, 
    		name=form.fullname.data, 
        	username=form.username.data, password=form.password.data, 
        	mobile_number=form.mobile_number.data, confirmed=True)
    	db.session.add(user)
    	user.load_coin(coin)
    	user.generate_confirmation_token()
    	user.generate_referring_id()
    	try:
    		db.session.commit()
    	except IntegrityError:
    		db.session.rollback()

    	flash('You can login now, %s, but make sure you confirm your account on your email for password recovery, incase you forget your password!'%(user.name))

    	return redirect(url_for('auth.login'))

    return render_template('auth/start_registration.html', form=form, title='vendor')


@main.route('/Dashboard/', methods=['POST','GET'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def dashboard():
	users=User.query.all()

	admin_role = Role.query.filter_by(name="Administrator").first()
	administrators = admin_role.users.all()
	
	amount_invested = 0
	amount_paid = 0
	for p in Package.query.all():
		if p.paid:
			amount_paid+=p.total_earnings
		amount_invested+=p.amount

	vendors = []
	clients = []
	moderators=[]
	for u in users:
		if u.can(Permission.MODERATE_COMMENTS):
			moderators.append(u)
		elif u.can(Permission.VEND_COUPONS):
			vendors.append(u)
		else:
			clients.append(u)
	requested_packages = Package.query.filter_by(cash_requested=True).all()
	return render_template('dashboard.html', administrators=administrators,
		packages=Package.query, clients=clients, 
		vendors=vendors, moderators=moderators, amount_invested=amount_invested, 
		amount_paid=amount_paid)

@main.route('/gen/users/<int:count>')
@permission_required(Permission.ADMINISTER)
def generate_users(count):
	users = User.generate_users(count=count)
	return redirect(request.args.get('next') or '/')


@main.route('/share/', methods=['GET'])
def share_post():
    url = request.args.get('url')
    title = request.args.get('title')
    text = request.args.get('text')

    # Perform the sharing action for Android devices
    fallback_url = f'intent://share/#Intent;action=android.intent.action.SEND;type=text/plain;S.android.intent.extra.SUBJECT={title};S.android.intent.extra.TEXT={text}\n\n{url};end;'
    
    return redirect(fallback_url)


@main.route('/share post/')
def share_post1():
	text=request.args.get('text')
	if text and current_user.is_authenticated:
		if current_user.can_still_run_task():
			print('\a', 'reach here now')
			current_user.add_task_bonus()
	return redirect('whatsapp://send?text=%s'%text)

@main.route('/edit task/', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def edit_task():
	task = DailyTask.query.get(request.args.get('id'))
	if task == None:
		task = DailyTask(body="")
	form = TaskForm()
	if form.validate_on_submit():
		task.body = form.body.data
		task.timestamp = datetime.utcnow()
		db.session.add(task)
		flash('The task has been updated.')
		return redirect('/')
		
	form.body.data = task.body
	return render_template('edit_task.html', form=form)

@main.route('/Search/')
@login_required
def search_result():
	people_list=[]
	people_username_list=[]
	post_list = []

	word=request.args.get('search').lower()
	if word:
		for user in User.query.all():
			if not user.username in people_username_list and (word.lower() in user.name.lower() or word in user.username.lower()):
				people_list.append(user)
				people_username_list.append(user.username)

		for post in Post.query.all():
			if word in post.body:
				post_list.append(post)

	page = request.args.get('page', 1, type=int)
	per_page = current_app.config.get('FRIENDS_PER_PAGE') or 10

	return render_template('search_result.html', FRs=people_list, posts=post_list, page=page, per_page=per_page, len=len)


@main.route('/edit web data/<int:web_data_id>', methods=['GET', 'POST'])
@admin_required
def edit_web_data(web_data_id):
    # Get the WebData entry by ID
    web_data = WebData.query.get_or_404(web_data_id)
    
    # Instantiate the form, pre-populating with the current WebData values
    form = WebDataForm(obj=web_data)

    if form.validate_on_submit():  # If form is submitted and valid
        # Update the WebData fields from the form data
        form.populate_obj(web_data)  # This will automatically populate the WebData object

        # Commit changes to the database
        db.session.commit()

        flash(f'{web_data.name} updated successfully!', 'success')
        return redirect(url_for('.profile', username=current_user.username))
    
    return render_template('edit_web_data.html', form=form, web_data=web_data)


# Route to view and select CoinPackage and submit payment receipt
@main.route('/buy/coin package/<int:package_id>/', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COMMENTS)
def buy_coins(package_id):
    next_url = request.args.get('next', None)
    if CoinPackage.query.count() == 0:
    	CoinPackage.insert_coin_packages()  # Ensure packages are inserted

    	
    selected_package = CoinPackage.query.filter_by(id=package_id).first_or_404()
    form = CoinPackagePaymentForm()
    

    if form.validate_on_submit():
        # Normally, save the payment receipt file and confirm payment
        receipt=form.receipt.data
        if receipt.filename:
        	filename = post_images.save(receipt, name=f'{current_user.username}CoinPackagePaymentReceipt.')
        	receipt_url = post_images.url(filename)

        # Create payment record
        payment = CoinPackagePayment(
            user_id=current_user.id,
            coin_package_id=selected_package.id,
            amount=selected_package.naira_amount,
            receipt=receipt_url
        )
        db.session.add(payment)
        db.session.commit()
        try:
        	admin_role = Role.query.filter_by(name="Administrator").first()
        	admin_list = admin_role.users.all()
        	notify_admin_of_payment(admin_list, payment)
        except Exception as e:
        	e=str(e)
        	print(e)
        	flash(e)
        flash(f'Your payment receipt has been submitted for {selected_package.name} coin package and will be reviewed.', 'success')
        return redirect(url_for('.await_confirmation', payment_id=payment.id, next=next_url))
    
    return render_template('buy_coins.html', form=form, title='Buy Coin', selected_package=selected_package)

# Admin route to initialize coin packages
@main.route('/admin/init-packages', methods=['POST'])
@admin_required
def init_coin_packages():
    CoinPackage.insert_coin_packages()
    flash('Coin packages initialized successfully!', 'success')
    return redirect(url_for('.coin_packages'))  # Assuming admin dashboard route exists

@main.route('/coin-packages/', methods=['GET'])
@login_required
def coin_packages():
    naira_amount = float(request.args.get('naira_amount', 0))
    naira_amount = int(float(f'{naira_amount:.0f}'))
    next_url = request.args.get('next', None)
    # Retrieve all coin packages from the database
    packages = CoinPackage.query.filter_by(limited=True).order_by(CoinPackage.naira_amount.asc()).all()
    return render_template('coin_packages.html', packages=packages, naira_amount=naira_amount, next_url=next_url)

@main.route('/add-coin-package', methods=['GET', 'POST'])
@admin_required
def add_coin_package():
    form = CoinPackageForm()
    if form.validate_on_submit():
        new_package = CoinPackage(
            name=form.name.data,
            naira_amount=form.naira_amount.data,
            quantity=form.quantity.data,
            naira_rate=form.naira_rate.data
        )
        try:
            db.session.add(new_package)
            db.session.commit()
            flash('Coin Package added successfully!', 'success')
            return redirect(url_for('.coin_packages'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('add_coin_package.html', form=form)

@main.route('/delete/coin package/<int:package_id>')
@admin_required
def delete_coin_package(package_id):
	coin_package = CoinPackage.query.get_or_404(package_id)
	info=coin_package.delete()
	flash(info)
	resp=make_response(redirect(request.args.get('next') or url_for('.coin_packages')))
	return resp

# Admin route to edit CoinPackage
@main.route('/admin/edit-package/<int:package_id>', methods=['GET', 'POST'])
@admin_required
def edit_coin_package(package_id):
    package = CoinPackage.query.get_or_404(package_id)
    form = CoinPackageForm(obj=package)
    
    if form.validate_on_submit():
        form.populate_obj(package)
        db.session.commit()
        flash('Coin Package updated successfully!', 'success')
        return redirect(url_for('.coin_packages'))  # Assuming admin dashboard route exists
    
    return render_template('edit_coin_package.html', form=form, package=package)


# Route for admin to verify payments
@main.route('/admin/verify-payments', methods=['GET', 'POST'])
@admin_required
def verify_payments():
    check=str(request.args.get('check') or 'unverified').lower()
    if check=='all':
    	payments = CoinPackagePayment.query.all()
    elif check=='verified':
    	payments = CoinPackagePayment.query.filter_by(verified=True).all()
    elif check=='rejected':
    	payments = CoinPackagePayment.query.filter_by(rejected=True).all()
    else:
    	payments = CoinPackagePayment.query.filter_by(verified=False).all()


    if request.method == 'POST':
        action = request.form.get("action")
        payment_id = request.form.get("payment_id")
        payment = CoinPackagePayment.query.get(payment_id)

        if payment:
            try:
            	if action == 'verify' and not payment.verified:
            		# Verify payment and create CoinRecharger(s)
            		amount, coin_list = payment.verify()
            		db.session.commit()
            		try:
            			notify_user_of_verification(payment)
            		except Exception as e:
            			e=str(e)
            			print(e)
            			flash(e)
            		flash(f"Payment of \u20A6{payment.coin_package.naira_amount} verified for ${amount} coin and CoinRecharger(s) listed out coin code: <br>{coin_list}", "success")
            	elif action == 'reject':
	            	payment.reject()
            		flash(f"Payment of \u20A6{payment.coin_package.naira_amount} rejected for ${payment.coin_package.dollar_amount} coin", "success")
            	elif action == 'delete':
            		db.session.delete(payment)
            		flash(f"Payment of \u20A6{payment.coin_package.naira_amount} deleted for ${payment.coin_package.dollar_amount} coin", "success")

            except Exception as e:
                db.session.rollback()
                flash("Error:", "error")
                raise e
                #flash(f"Error: {str(e)}", "error")
            
            return redirect(request.args.get('next') or url_for('.verify_payments', check=check))
    
    return render_template('verify_coin_package_payments.html', payments=payments, check=check)

@main.route('/await-confirmation/<int:payment_id>', methods=['GET'])
@login_required
def await_confirmation(payment_id):
    payment = CoinPackagePayment.query.filter_by(id=payment_id, user_id=current_user.id).first_or_404()
    next_url=request.args.get('next') or url_for('.profile', username=current_user.username, _external=True)
    # Handle API call for AJAX polling
    if request.args.get('api_call', None):
        data = {
            'id': payment.id,
            'amount': payment.amount,
            'verified': payment.verified,
            'next_url': next_url
        }
        if payment.verified:
        	flash('Payment has been successfully verified')
        	flash(f'Payment Result: <br>{payment.details}')
        return jsonify(data)  # Return data as a dictionary, not a list

    # If payment is verified, redirect user to profile
    if payment and payment.verified:
        flash('Payment has been successfully verified')
        flash(f'Payment Result: <br>{payment.details}')
        return redirect(next_url)

    # Render the template if no verification yet
    return render_template('await_confirmation.html', payment=payment, next_url=next_url)

@main.route('/coin payment details/<int:payment_id>', methods=['GET'])
@login_required
def coin_payment_details(payment_id):
    payment = CoinPackagePayment.query.filter_by(id=payment_id).first_or_404()
    return render_template('coin_payment_details.html', payment=payment)


@main.route('/recharge/', methods=['GET','POST'])
@permission_required(Permission.MODERATE_COMMENTS)
def recharge():
    form = RechargeForm()
    naira_amount = float(request.args.get('naira_amount', 0))
    naira_amount = int(float(f'{naira_amount:.0f}'))
    next_url = request.args.get('next')
    if form.validate_on_submit():
    	naira_amount = int(float(f'{form.naira_amount.data:.0f}'))
    	selected_package = CoinPackage(name='Remainder Coin', naira_amount=naira_amount, 
    		quantity=1, naira_rate=g.web_data.exchange_rate, limited=False)
    	db.session.add(selected_package)
    	db.session.commit()
    	# Normally, save the payment receipt file and confirm payment
    	receipt=form.receipt.data
    	if receipt.filename:
    		filename = post_images.save(receipt, name=f'{current_user.username}CoinPackagePaymentReceipt.')
    		receipt_url = post_images.url(filename)

    	# Create payment record
    	payment = CoinPackagePayment(
    		user_id=current_user.id,
    		coin_package_id=selected_package.id,
    		amount=selected_package.naira_amount,
    		receipt=receipt_url
    		)
    	db.session.add(payment)
    	db.session.commit()
    	try:
    		admin_role = Role.query.filter_by(name="Administrator").first()
    		admin_list = admin_role.users.all()
    		notify_admin_of_payment(admin_list, payment)
    	except Exception as e:
    		e=str(e)
    		print(e)
    		flash(e)
    	flash(f'Your payment receipt has been submitted and will be reviewed soon.', 'success')
    	db.session.add(selected_package)
    	db.session.commit()
    	return redirect(url_for('.await_confirmation', payment_id=payment.id, next=next_url))

    form.naira_amount.data=naira_amount
    return render_template('recharge.html', form=form, naira_amount=naira_amount)

@main.route('/naira_to_coin/', methods=['GET'])
def naira_to_coin():
    naira_amount = float(request.args.get('naira_amount', 0))
    if naira_amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400  # Return error for invalid amounts
    coin_amount = g.web_data.convert_naira_to_coin(naira_amount)  # Example conversion logic
    return jsonify({"coin_amount": f"₦{naira_amount:.0f} for ${coin_amount:.0f} Coins",
    	"payment_note": f"Transfer the exact ₦{naira_amount:.0f} to the payment details above for the ${coin_amount:.0f} coin you want to purchase and also, make sure to upload your payment receipt on the form below to avoid error on your purchase."})  # Ensure JSON response
