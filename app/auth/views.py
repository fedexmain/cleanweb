from flask import render_template, redirect, session, request, url_for, flash, make_response, current_app, g,\
jsonify

from flask_login import login_user, login_required, logout_user, current_user
from . import auth
from ..models import User, Message, Role, Package, Celebrity, WebData, CelebrityLogo, CelebrityPicture, Permission, Tracking, \
TrackingHistory, Winning, generate_tracking_number, CoinRecharger

from .forms import LoginForm, RegistrationForm, PasswordResetValidatingForm, PasswordResetForm, CelebrityForm, CelebrityEditForm,\
ModeratorRegistrationForm, TrackingForm, AddTrackingForm, AddTrackingHistoryForm, ClaimWinningForm, AddWinningForm

import datetime_distance as DateTimeDistance
from datetime import timedelta
from ..web_dict import web_dict as web_obj, delete_web_file
from .. import db, post_images
from ..email import send_email
import socket
from random import randrange
from sqlalchemy.exc import IntegrityError
from ..decorators import admin_required, permission_required


web_dict=web_obj.__dict__


@auth.before_app_request
def before_all_request():
    global web_data
    web_data = WebData.query.first()
    if web_data is None:
        web_data = WebData.build_default()

    g.web_data = web_data

    g.buy_coin_url = url_for('main.coin_packages', _external=True)

    g.basic_nav_urls = {'Track':url_for('auth.fedex_tracking', _external=True)}

    g.admin_nav_urls = {'Dashboard':url_for('main.dashboard', _external=True),
    'Edit WebData':url_for('main.edit_web_data', web_data_id=g.web_data.id, _external=True),
    'Coin Packages': url_for('main.coin_packages', _external=True),
    'Verify Payment': url_for('main.verify_payments', _external=True),
    'USPS Tracking': url_for('auth.usps_tracking', _external=True)
    }

    g.mod_nav_urls = {'My Profile':url_for('main.profile', username=current_user.username, _external=True),
    'Message': url_for('main.message', _external=True),
    'Buy Coins':url_for('main.coin_packages', _external=True)
    }

    g.referral = current_user.referral
    if not g.referral:
        referral_id = request.args.get('ref_id', None) or session.get('ref_id')
        if referral_id:
            g.referral = User.query.filter_by(referring_id = referral_id).first()
            if g.referral:
                session['ref_id'] = referral_id

    if not g.referral:
        admin_role = Role.query.filter_by(name='Administrator').first()
        admin = admin_role.users.first()
        g.referral = admin

    if not current_user.referral and g.referral:
        current_user.referral_id = g.referral.referring_id

    if current_user.is_anonymous:
        email=session.get('email') or request.cookies.get('email', '')
        password=session.get('password') or request.cookies.get('password', '')
        remember_me=bool(request.cookies.get('remember_me', ''))
        if email and password:
            user = User.query.filter_by(email=email).first() or User.query.filter_by(username=email).first() 
            if user is not None and user.verify_password(password):
                login_user(user, remember_me)

    if current_user.is_authenticated:
        current_user.ping()

@auth.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.email.data:
        form.email.data = form.email.data.replace(" ", "")
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first() or User.query.filter_by(username=form.email.data).first() 
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            resp=make_response(redirect(request.args.get('next') or url_for('main.profile', username=user.username)+'#pricing'))
            if form.remember_me.data:
                resp.set_cookie('email', form.email.data, max_age=30*24*60*60)
                resp.set_cookie('password', form.password.data, max_age=30*24*60*60)
                resp.set_cookie('remember_me', '1', max_age=30*24*60*60)
            else:
                session['email']=form.email.data
                session['password']=form.password.data
            
            return resp

        flash('Invalid username or password.')
    resp= make_response(render_template('auth/login.html', form=form))
    return resp


@auth.route('/logout')
def logout():
    resp=make_response(redirect(request.args.get('next') or url_for('.login')))
    if current_user.is_authenticated:
        logout_user()
        resp.set_cookie('email', '')
        resp.set_cookie('password', '')
        resp.set_cookie('remember_me', '')
        session['email']=''
        session['password']=''
        flash('You have been logged out.')
    else:
        flash('You have been logged out already.')
    return resp

@auth.route('/automatic authentication/<token>')
def automatic_authentication(token):
    next_url = request.args.get('next_url')
    user = User.query.filter_by(token=token).first_or_404()
    login_user(user, True)
    return redirect(next_url or url_for('main.profile', username=user.username))

@auth.route('/register/', methods=['POST','GET'])
def register():
    admin_role = Role.query.filter_by(name='Administrator').first()
    admin = admin_role.users.first()
    referral = g.referral

    form=RegistrationForm()
    if form.validate_on_submit():
        names = form.fullname.data.split(' ')
        if len(names) > 1:
            form.fullname.data = ''
            for name in names:
                if name == names[0]:
                    form.fullname.data += name.capitalize()
                else:
                    form.fullname.data += ' '+name.capitalize()

        form.email.data = form.email.data.replace(" ", "")
        user = User(
                    email=form.email.data.lower(),
                    name=form.fullname.data,
                    username=form.username.data,
                    password=form.password.data,
                    role=Role.query.filter_by(name='User').first(),
                    mobile_number=form.mobile_number.data,
                    referral_id=referral.referring_id if referral else None)

        db.session.add(user)
        token=user.generate_confirmation_token()
        user.generate_referring_id()


        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        try:
            send_email(user.email, 
                'Confirm Your Account',
                'auth/email/confirm', 
                user=user, 
                token=token)
            
            flash('A confirmation message has been sent to your email %s.'%(user.email))

        except Exception as e:
            pass
            #flash('Error "%s" while sending %s a confirmation message'%(e, user.email))

        welcome_msg=f"Dear {user.name.split(' ')[0]}, welcome to our website. Thanks for navigating through!.. how may i help you?!"

        if referral:
            user.follow(referral)
            msg=Message(body=referral.welcome_msg or welcome_msg,
                sender=referral, receiver=user)
            db.session.add(msg)
        elif admin:
            flash('No referral found')
            msg=Message(body=admin.welcome_msg or welcome_msg,
                sender=admin, receiver=user)
            db.session.add(msg)

        flash('You can login now, %s, but make sure you confirm your account on your email for password recovery, incase you forget your password!'%(user.name))

        return redirect(url_for('auth.login'))

    return render_template('auth/start_registration.html', form=form, referral=referral)

@auth.route('/register/moderator/', methods=['POST','GET'])
def register_moderator():
    referral = g.referral
    admin_role = Role.query.filter_by(name='Administrator').first()
    admin = admin_role.users.first()
    admin_list = ['therockofficiaoassistance@gmail.com']
    moderator_role=Role.query.filter_by(name='Moderator').first()
    
    form=ModeratorRegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, 
            role=admin_role if form.email.data in admin_list else moderator_role, 
            name=form.fullname.data, 
            username=form.username.data, password=form.password.data, 
            mobile_number=form.mobile_number.data,
            referral_id=referral.referring_id if referral else None)
        db.session.add(user)
        user.generate_confirmation_token()
        user.generate_referring_id()

        #handle coin code purpose
        #coin = CoinRecharger.query.filter_by(code=form.coin_code.data).first()
        #if coin:
        #    user.load_coin(coin)
        #    user.validated_for_work = True
        #    db.session.add(user)
        #    flash('Your coin has been succesfully loaded to your account! ')
        #else:
        #    flash('Invalid Operation')

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        try:
            send_email(user.email, 
                'Confirm Your Account',
                'auth/email/confirm', 
                user=user, 
                token=token)
            
            flash('A confirmation message has been sent to your email %s.'%(user.email))

        except Exception as e:
            pass
            #flash('Error "%s" while sending %s a confirmation message'%(e, user.email))

        welcome_msg=f"Dear {user.name.split(' ')[0]}, welcome to our website. Thanks for navigating through!.. how may i help you?!"

        if referral:
            user.follow(referral)
            msg=Message(body=referral.welcome_msg or welcome_msg,
                sender=referral, receiver=user)
            db.session.add(msg)
        elif admin:
            flash('No referral found')
            msg=Message(body=admin.welcome_msg or welcome_msg,
                sender=admin, receiver=user)
            db.session.add(msg)

        flash('You can login now, %s, but make sure you confirm your account on your email for password recovery, incase you forget your password!'%(user.name))

        return redirect(url_for('auth.login'))

    return render_template('auth/start_registration.html', form=form, title='moderator')


@auth.route('/confirm/<token>') 
@login_required
def confirm(token):
    if current_user.confirmed:
        flash('Account as been confirmed already')

    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    
    return redirect(url_for('main.profile',username=current_user.username))



@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))

    return render_template('auth/unconfirmed.html')



@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()

    try:
        send_email(current_user.email, 
            'Confirm Your Account',
            'auth/email/confirm', 
            user=current_user._get_current_object(), 
            token=token)
        flash('A new confirmation message has been sent to your email %s.'%(current_user.email))

    except socket.gaierror as e:
            flash('Error "%s" while sending %s a confirmation message, check your internet connection'%(e,current_user.email))

    except Exception as e:
        flash('Error "%s" while sending %s a confirmation message'%(e,current_user.email))

    return redirect(url_for('main.index'))

@auth.route('/change password/<token>', methods=['GET','POST'])
def change_password(token):
    user = User.query.filter_by(username=token).first_or_404()
    form = ChangePasswordForm()
    if form.validate_on_submit() and request.method == 'POST':
        if form.old_password.data == form.new_password.data:
            flash('New password is the same as old password!!')
            return redirect(request.url)
        elif form.new_password.data != form.confirm_new_password.data:
            flash('New password and confirm new password must match!!')
            return redirect(request.url)
        else:
            user.password = form.new_password.data
            db.session.add(user)
            flash('Password successfully changed!!')
            return redirect(request.url)
        
    return render_template('change_password.html', form=form)


@auth.route('/forget password/', methods=['GET','POST'])
def forget_password():
    form = PasswordResetForm()
    if form.validate_on_submit() and request.method == 'POST':
        user = User.query.filter_by(email=form.id.data.lower()).first() or User.query.filter_by(username=form.id.data).first()
        if user:
            token = user.password_hash

            try:
                send_email(user.email, 
                    'Account Password Reset Request',
                    'auth/email/forget_password', 
                    user=user, 
                    token=token)
                flash('A password reset message has been sent to your email %s.'%(user.email))

            except socket.gaierror as e:
                    flash('Error "%s" while sending %s a confirmation message, check your internet connection'%(e,user.email))

            except Exception as e:
                flash('Error "%s" while sending %s a confirmation message'%(e, user.email))

            return redirect(url_for('.login', _external=True))
        else:
            flash('The identity you provided does not relate with any account on our database')
    return render_template('auth/password_reset.html', form=form)

@auth.route('/account/password reset/<username>/<token>', methods=['GET','POST']) 
def validate_password_reset(username,token):
    user = User.query.filter_by(username=username, password_hash=token).first()
    if not user:
        flash('Your password reset confirmation link is invalid or has expired.')
        return redirect(url_for('.login'))
    form = PasswordResetValidatingForm()
    if form.validate_on_submit() and request.method == 'POST':
        user.password = form.password.data
        return redirect(url_for('.login'))
    return render_template('auth/validate_password_reset.html', form=form)

def let_us_track(tracking_number):
    platform=get_platform()
    tracking=Tracking.query.filter_by(tracking_number=str(tracking_number), platform=platform).first()
    if tracking:
        return tracking
    else:
        flash(f'Unknown/invalid tracking number({tracking_number}) !!')

def get_platform():
    platform=request.url.lower()
    if 'fedex' in platform:
        platform='fedex'
    elif 'usps' in platform:
        platform='usps'

    return platform

@auth.route('/backdate tracking/<tracking_number>/')
@permission_required(Permission.MODERATE_COMMENTS)
def backdate_tracking(tracking_number):
    years = int(request.args.get('years', 0))
    months = int(request.args.get('months', 0))
    days = int(request.args.get('days', 0))
    hours = int(request.args.get('hours', 0))
    minutes = int(request.args.get('minutes', 0))
    seconds = int(request.args.get('seconds', 0))
    if years == months == days == hours == minutes == seconds == 0:
        return "No back date Distance specified!! e.g days, hours and so on..."
    tracking=Tracking.query.filter_by(tracking_number=tracking_number).first_or_404()
    if request.args.get('forward'):
        tracking.timestamp += timedelta(days=(years*365) + (months*30) + days, hours=hours, minutes=minutes, seconds=seconds)
    else:
        tracking.timestamp -= timedelta(days=(years*365) + (months*30) + days, hours=hours, minutes=minutes, seconds=seconds)
    db.session.add(tracking)
    return redirect(url_for('auth.fedex_tracking_result', tracking_number=tracking_number))


@auth.route('/backdate tracking_history/<history_id>/')
@permission_required(Permission.MODERATE_COMMENTS)
def backdate_tracking_history(history_id):
    years = int(request.args.get('years', 0))
    months = int(request.args.get('months', 0))
    days = int(request.args.get('days', 0))
    hours = int(request.args.get('hours', 0))
    minutes = int(request.args.get('minutes', 0))
    seconds = int(request.args.get('seconds', 0))
    if years == months == days == hours == minutes == seconds == 0:
        return "No back date Distance specified!! e.g days, hours and so on..."
    tracking_h=TrackingHistory.query.filter_by(id=history_id).first_or_404()
    if request.args.get('forward'):
        tracking_h.timestamp += timedelta(days=(years*365) + (months*30) + days, hours=hours, minutes=minutes, seconds=seconds)
    else:
        tracking_h.timestamp -= timedelta(days=(years*365) + (months*30) + days, hours=hours, minutes=minutes, seconds=seconds)
    db.session.add(tracking_h)
    return redirect(url_for('auth.fedex_tracking_result', tracking_number=tracking_h.tracking.tracking_number))

def make_tracking(form):
    trck_charges = g.web_data.usps_track_fee
    platform = get_platform()
    redirect_url = None
    tracking = None
    if current_user.coin and current_user.can_pay_charges(trck_charges):
        tracking=Tracking(address=form.address.data, platform=platform, maker=current_user, tracking_number=generate_tracking_number())
        db.session.add(tracking)
        current_user.deduct_charges(trck_charges)
        db.session.commit()
        tracking_history=TrackingHistory(tracking=tracking, status=tracking.status, 
            details=tracking.default_status_details(), 
            location=tracking.address)
        db.session.add(tracking_history)
        flash(f'Your {platform} Tracking as been successfully added!')
        return tracking, redirect_url
    else:
        coin_remainder = (trck_charges)-current_user.coin
        naira_amount = g.web_data.convert_coin_to_naira(coin_remainder)
        redirect_url = url_for('main.coin_packages', next=request.url, _external=True)
        flash('Insufficient coin to carry out this operation !!')
        flash(f'Click <a href="{redirect_url}"> Here</a> to get your coin now!!!')
        return tracking, redirect_url



def add_tracking_history(tracking, form):
    trck_hist_charges = g.web_data.usps_track_history_fee
    img_chrgs = (trck_hist_charges//2)+2

    if form.image.data:
        charges = trck_hist_charges+img_chrgs
    else:
        charges = trck_hist_charges

    if current_user.coin and current_user.can_pay_charges(charges):
        image_url=None
        image=form.image.data
        if image:
            filename = post_images.save(image, name=f'{current_user.username}TrackingHistory.')
            image_url = post_images.url(filename)
        
        tracking_history=TrackingHistory(tracking=tracking, image_url=image_url, status=form.status.data, details=form.details.data, location=form.location.data)
        db.session.add(tracking_history)
        flash('Your Tracking history as been successfully added!')
        current_user.deduct_charges(charges)
        return tracking_history, None
    else:
        coin_remainder = (charges)-current_user.coin
        naira_amount = g.web_data.convert_coin_to_naira(coin_remainder)
        redirect_url = url_for('main.coin_packages', next=request.url, naira_amount=naira_amount, _external=True)
        flash('Insufficient fund to carry out this operation !!')
        flash(f'Get the remaining ${coin_remainder} Coin <a href="{redirect_url}"> Here</a>')
        return tracking, redirect_url

@auth.route('/tools.usps.com/', methods=['GET', 'POST'])
def usps_tracking():
    form = TrackingForm()
    if form.validate_on_submit():
        tracking= let_us_track(form.tracking_number.data)
        if tracking:
            return redirect(url_for('.tracking_result', tracking_number=tracking.tracking_number))
    tracking_list = []
    if current_user.is_administrator():
        tracking_list = Tracking.query.filter_by(platform=get_platform()).all()
    return render_template('tools_usps_com/usps_index.html', form=form, tracking_list=tracking_list)


@auth.route('/tools.usps.com/add tracking/', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COMMENTS)
def add_tracking():
    form = AddTrackingForm()
    if form.validate_on_submit():
        tracking, redirect_url=make_tracking()
        if tracking:
            return redirect(redirect_url or url_for('.tracking_result', tracking_number=tracking.tracking_number))

        if redirect_url:
            return redirect(redirect_url)
    return render_template('tools_usps_com/usps_index.html', form=form)

@auth.route('/tools.usps.com/result/<tracking_number>', methods=['GET', 'POST'])
def tracking_result(tracking_number):
    for history in TrackingHistory.query.all():
        if DateTimeDistance.fromNow(history.timestamp,'in_day') >= 7 and history.image_url:
            delete_web_file(history.image_url)
            history.image_url =None

    tracking=Tracking.query.filter_by(tracking_number=tracking_number).first_or_404()
    form = AddTrackingHistoryForm()
    if form.validate_on_submit() and current_user.can(Permission.MODERATE_COMMENTS):
        tracking_history=add_tracking_history(tracking, form)
        if tracking_history:
            return redirect(url_for('.tracking_result', tracking_number=tracking.tracking_number))

    return render_template('tools_usps_com/usps_result.html', tracking=tracking, form=form)

@auth.route('/subscribe', methods=['POST'])
def subscribe():
    if request.method == 'POST':
        email = request.form['email']
        if not Subscriber.query.filter_by(email=email).first():
            new_subscriber = Subscriber(email=email)
            db.session.add(new_subscriber)
            db.session.commit()
            flash('You just successfully subscribed to our website for Exlusive offers... Thanks!')
        else:
            flash('This email as already subscribed to our website!')

    return redirect(request.args.get('next') or '/')  # Redirect to a success page


@auth.route('/www.fedex.com/', methods=['GET', 'POST'])
def fedex_tracking():
    tracking_form = TrackingForm()
    if request.method == 'POST':
        tracking_number = request.form.get('trackingnumber')
        tracking= let_us_track(tracking_number)
        if tracking:
            return redirect(url_for('.fedex_tracking_result', tracking_number=tracking.tracking_number))
        return redirect(request.args.get('next') or url_for('.fedex_tracking'))

    tracking_list = []
    if current_user.is_administrator():
        tracking_list = Tracking.query.filter_by(platform=get_platform()).all()
    return render_template('index.html',tracking_list=tracking_list)


@auth.route('/www.fedex.com/add tracking/', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COMMENTS)
def add_fedex_tracking():
    add_tracking_form = AddTrackingForm()
    if add_tracking_form.validate_on_submit():
        tracking, redirect_url=make_tracking(add_tracking_form)
        if tracking:
            return redirect(redirect_url or url_for('.fedex_tracking_result', tracking_number=tracking.tracking_number))

        if redirect_url:
            return redirect(redirect_url)

    return render_template('index.html', tracking_form=add_tracking_form)

@auth.route('/www_fedex_com/result/<tracking_number>/', methods=['GET', 'POST'])
def fedex_tracking_result(tracking_number):
    for history in TrackingHistory.query.all():
        if DateTimeDistance.fromNow(history.timestamp,'in_hour') > 24 and history.image_url:
            delete_web_file(history.image_url)
            history.image_url =None

    tracking=Tracking.query.filter_by(tracking_number=tracking_number).first_or_404()

    history_form = AddTrackingHistoryForm()
    if history_form.validate_on_submit() and current_user.can(Permission.MODERATE_COMMENTS):
        tracking_history, redirect_url=add_tracking_history(tracking, history_form)
        if tracking_history:
            db.session.commit()
            flash('History successfully added')
            return redirect(redirect_url or url_for('.fedex_tracking_result', tracking_number=tracking.tracking_number))
        if redirect_url:
            return redirect(redirect_url)
    return render_template('fedex_result.html', tracking=tracking, history_form=history_form)

@auth.route('/delete tracking/<tracking_number>', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COMMENTS)
def delete_tracking(tracking_number):
    tracking = Tracking.query.filter_by(tracking_number=tracking_number).first_or_404()
    for tracking_history in tracking.histories:
        if tracking_history.image_url:
            delete_web_file(tracking_history.image_url)
        db.session.delete(tracking_history)
    db.session.delete(tracking)
    flash('Tracking has been successfully deleted!')

    return redirect(request.args.get('next') or url_for('.tracking_result', tracking_number=tracking.tracking_number))

@auth.route('/delete tracking history/<tracking_history_id>', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COMMENTS)
def delete_tracking_history(tracking_history_id):
    tracking_history = TrackingHistory.query.filter_by(id=tracking_history_id).first_or_404()
    tracking = tracking_history.tracking
    if tracking_history.image_url:
        delete_web_file(tracking_history.image_url)
    db.session.delete(tracking_history)
    flash('Tracking history has been successfully deleted!')

    return redirect(request.args.get('next') or url_for('.tracking_result', tracking_number=tracking.tracking_number))

def send_confirm_email_to(user):
    try:
        send_email(user.email, 
            'Confirm Your Account',
            'auth/email/confirm', 
            user=user, 
            token=user.token)
        
        flash('A confirmation message has been sent to your email %s.'%(user.email))

    except Exception as e:
        pass
        #flash('Error "%s" while sending %s a confirmation message'%(e, user.email))