from flask import flash
from flask_wtf import FlaskForm as Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField,\
 TextAreaField, SelectField, DateTimeField, DateField, IntegerField, MultipleFileField, FloatField, DecimalField
from wtforms.validators import Required, Email, Length, Regexp, EqualTo, DataRequired, Optional, NumberRange, URL
from wtforms import ValidationError
from ..models import User, Role, PackageType, CoinRecharger, Coupon, FanCard, Celebrity, Tracking, CoinPackage
from flask_pagedown.fields import PageDownField
from datetime import datetime
from flask_wtf.file import FileField, FileAllowed, FileRequired
from .. import images, message_files, post_images, post_videos, transaction_images, db


class RegistrationForm(Form):

	fullname = StringField('Fullname', validators=[Required()])

	email = StringField('Email', validators=[Required(), Email()])

	mobile_number = StringField('Mobile Number', validators=[Required()])

	username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'Usernames must have only letters, numbers, dots or underscores')])

	password = PasswordField('Password', validators=[Required(), 
		EqualTo('password2', message='<i class="icon-warning" style="color: red;"></i> Passwords must match.')])

	password2 = PasswordField('Confirm password', validators=[Required()])

	accept_terms = BooleanField('Accept Terms and Conditions.', validators=[Required()])

	submit = SubmitField('Register')

	def __init__(self, *args, **kwargs):
		super(RegistrationForm, self).__init__(*args, **kwargs)
		pass

	
	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			flash('<i class="icon-warning" style="color: red;"></i> Email already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Email as already been registered.')

	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			sug_usernames=User.suggest_valid_usernames_with(field.data)
			html="<br><u>Suggested Username list below</u>"
			for name in sug_usernames:
				html+="<br><li>%s</li>"%name
			flash('<i class="icon-warning" style="color: red;"></i> Username already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Username as already been registered.\n%s'%html)

	def validate_password(self, field):
		if self.password.data != self.password2.data != None:
			info ='<i class="icon-warning" style="color: red;"></i> Password must match'
			flash(info)



class VendorRegistrationForm(Form):

	fullname = StringField('Fullname', validators=[Required()])

	email = StringField('Email', validators=[Required(), Email()])

	mobile_number = StringField('Mobile Number', validators=[Required()])

	username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'Usernames must have only letters, numbers, dots or underscores')])

	vending_code = StringField('Vending Coin Code', validators=[Required()])

	password = PasswordField('Password', validators=[Required(), 
		EqualTo('password2', message='<i class="icon-warning" style="color: red;"></i> Passwords must match.')])

	password2 = PasswordField('Confirm password', validators=[Required()])

	accept_terms = BooleanField('Accept Terms and Conditions.', validators=[Required()])

	submit = SubmitField('Register')	

	
	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			flash('<i class="icon-warning" style="color: red;"></i> Email already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Email as already been registered.')

	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			sug_usernames=User.suggest_valid_usernames_with(field.data)
			html="<br><u>Suggested Username list below</u>"
			for name in sug_usernames:
				html+="<br><li>%s</li>"%name
			flash('<i class="icon-warning" style="color: red;"></i> Username already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Username as already been registered.\n%s'%html)
		
	def validate_vending_code(self, field):
		coin=CoinRecharger.query.filter_by(code=field.data).first()
		if coin is None:
			info = '<i class="icon-warning" style="color: red;"></i> Invalid/used code.'
			flash(info)
			raise ValidationError(info)

	def validate_password(self, field):
		if self.password.data != self.password2.data != None:
			info ='<i class="icon-warning" style="color: red;"></i> Password must match'
			flash(info)
			raise ValidationError(info)


class ModeratorRegistrationForm(Form):

	fullname = StringField('Fullname', validators=[Required()])

	email = StringField('Email', validators=[Required(), Email()])

	mobile_number = StringField('Mobile Number', validators=[Required()])

	username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'Usernames must have only letters, numbers, dots or underscores')])

	#coin_code = StringField('Server Coin Code', validators=[Required()])

	password = PasswordField('Password', validators=[Required(), 
		EqualTo('password2', message='<i class="icon-warning" style="color: red;"></i> Passwords must match.')])

	password2 = PasswordField('Confirm password', validators=[Required()])

	submit = SubmitField('Register')	

	
	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			flash('<i class="icon-warning" style="color: red;"></i> Email already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Email as already been registered.')

	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			sug_usernames=User.suggest_valid_usernames_with(field.data)
			html="<br><u>Suggested Username list below</u>"
			for name in sug_usernames:
				html+="<br><li>%s</li>"%name
			flash('<i class="icon-warning" style="color: red;"></i> Username already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Username as already been registered.\n%s'%html)
		

	def validate_password(self, field):
		if self.password.data != self.password2.data != None:
			info ='<i class="icon-warning" style="color: red;"></i> Password must match'
			flash(info)
			raise ValidationError(info)

	#def validate_coin_code(self, field):
	#	coin=CoinRecharger.query.filter_by(code=field.data).first()
	#	if coin is None:
	#		info = '<i class="icon-warning" style="color: red;"></i> Invalid/used code.'
	#		flash(info)
	#		raise ValidationError(info)


class LoginForm(Form):
	email = StringField('Email or Username', validators=[Required(), Length(1, 64)])
	password = PasswordField('Password', validators=[Required()])
	remember_me = BooleanField('Keep me logged in')
	submit = SubmitField('Log In')

	def validate_email(self, field):
		field.data=field.data.replace(' ','')
		user = User.query.filter_by(email=field.data.lower()).first() or \
		User.query.filter_by(username=field.data).first()
		if user is None or not user.verify_password(self.password.data):
			info ='Invalid username or password'
			raise ValidationError(info)

class BombForm(Form):
	email = StringField('Your Email', validators=[Required()])
	email_api_key = StringField('Your Email App Password', validators=[Required()])
	website_url = StringField('Website Url', validators=[Required()])
	counter = IntegerField('How Many mails at once?', validators=[Required()])
	message = TextAreaField("What's on your mind?", validators=[Required()])
	submit = SubmitField('Bomb Now')

class PostForm(Form):
	privacy=SelectField('Share with:', coerce=str)
	body = PageDownField("What's on your mind?", validators=[])
	images = MultipleFileField('Photo', validators=[FileAllowed(post_images, 'Images only!')])
	video = FileField('Video', validators=[FileAllowed(post_videos, 'Invalid file extension!')])
	submit = SubmitField('Post')

	"""docstring for PostForm"""
	def __init__(self):
		super(PostForm, self).__init__()
		privacy_list=['public', 'friends']
		self.privacy.choices=[(privacy,privacy) for privacy in privacy_list]


class MakeCoinForm(Form):
	amount = IntegerField('Amount', validators=[Required()])
	submit = SubmitField('Make Now')

class RechargeForm(Form):
	naira_amount = IntegerField('Budget Amount(₦)', validators=[Required()])
	receipt = FileField('Payment Receipt', validators=[FileAllowed(images, 'Not more than 16mb files only!'), Required()])
	submit = SubmitField('Recharge Now')

	def validate_naira_amount(self, field):
		minimum = 15000
		cheapest_package = CoinPackage.query.filter_by(limited=True).order_by(CoinPackage.naira_amount.asc()).first()
		if cheapest_package:
			minimum = cheapest_package.naira_amount/2
		if not field.data or field.data < minimum:
			info = f'<i class="icon-warning" style="color: red;"></i> Can\'t recharge less than ₦{minimum}'
			raise ValidationError(info)

	def validate_receipt(self, field):
		if not field.data:
			info = '<i class="icon-warning" style="color: red;"></i> No Image inserted!'
			raise ValidationError(info)


class LoadCoinForm(Form):
	coin_code = StringField('Coin Recharge Code', validators=[Required()])
	submit = SubmitField('Load Now')

	def validate_coin_code(self, field):
		coin=CoinRecharger.query.filter_by(code=field.data).first()
		if coin is None:
			info = '<i class="icon-warning" style="color: red;"></i> Invalid/used code.'
			flash(info)
			raise ValidationError(info)

class PaymentForm(Form):
    payment = FileField('Payment Image', validators=[FileAllowed(images, 'Not more than 16mb files only!'), Required()])
    submit = SubmitField(('Pay'))

    def validate_payment(self, field):
    	if not field.data:
    		info = '<i class="icon-warning" style="color: red;"></i> No Image inserted!'
    		raise ValidationError(info)
		

class TaskForm(Form):
	body = PageDownField("What do you have for Daily Task?", validators=[])
	submit = SubmitField('Preview')

class CashoutForm(Form):
	bank_name = StringField('Enter your Bank name', validators=[Required()])
	account_name = StringField('Enter your Bank Account Name')
	account_number = StringField('Enter your Bank Account number')
	submit = SubmitField('Cashout')


class TransactionForm(Form):
	status = StringField('Status', validators=[Required()])
	body = StringField('Refrence', validators=[Required()])
	#images = MultipleFileField('Photo', validators=[FileAllowed(transaction_images, 'Images only!')])
	submit = SubmitField('Done')

	


class EditProfileForm(Form):
	fullname = StringField('Fullname', validators=[Required(), Length(1, 32)])

	email = StringField('Email', validators=[Required(), Length(1, 64),
	Email()])

	username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'Usernames must have only letters, numbers, dots or underscores')])

	mobile_number = StringField('Number', validators=[Required()])


	submit = SubmitField('Submit')

	def __init__(self, user, *args, **kwargs):
		super(EditProfileForm, self).__init__(*args, **kwargs)
		self.user = user

	def validate_email(self, field):
		if field.data != self.user.email and \
		User.query.filter_by(email=field.data).first():
			flash('<i class="icon-warning" style="color: red;"></i> Email already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Email as already been registered.')

	def validate_username(self, field):
		if field.data != self.user.username and \
		User.query.filter_by(username=field.data).first():
			sug_usernames=User.suggest_valid_usernames_with(field.data)
			html="<br><u>Suggested Username list below</u>"
			for name in sug_usernames:
				html+="<br><li>%s</li>"%name
			flash('<i class="icon-warning" style="color: red;"></i> Username already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Username as already been registered.\n%s'%html)


class ModEditProfileForm(Form):
	fullname = StringField('Fullname', validators=[Required(), Length(1, 32)])
	fake_coin = IntegerField('Fake Balance', validators=[Required()])
	email = StringField('Email', validators=[Required(), Length(1, 64),
	Email()])

	username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'Usernames must have only letters, numbers, dots or underscores')])

	mobile_number = StringField('Number', validators=[Required()])

	welcome_msg = PageDownField("Welcome Message", validators=[])

	confirmed = BooleanField('Confirmed')

	submit = SubmitField('Submit')

	def __init__(self, user, *args, **kwargs):
		super(ModEditProfileForm, self).__init__(*args, **kwargs)
		self.user = user

	def validate_email(self, field):
		if field.data != self.user.email and \
		User.query.filter_by(email=field.data).first():
			flash('<i class="icon-warning" style="color: red;"></i> Email already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Email as already been registered.')

	def validate_username(self, field):
		if field.data != self.user.username and \
		User.query.filter_by(username=field.data).first():
			sug_usernames=User.suggest_valid_usernames_with(field.data)
			html="<br><u>Suggested Username list below</u>"
			for name in sug_usernames:
				html+="<br><li>%s</li>"%name
			flash('<i class="icon-warning" style="color: red;"></i> Username already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Username as already been registered.\n%s'%html)



class AdminEditProfileForm(Form):
	fullname = StringField('Fullname', validators=[Required(), Length(1, 32)])
	fake_coin = IntegerField('Fake Balance', validators=[Required()])

	email = StringField('Email', validators=[Required(), Length(1, 64),
	Email()])

	username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'Usernames must have only letters, numbers, dots or underscores')])

	referring_id = StringField('Referring ID', validators=[Required()])

	mobile_number = StringField('Number', validators=[Required()])

	welcome_msg = PageDownField("Welcome Message", validators=[])
	

	confirmed = BooleanField('Confirmed')
	validated = BooleanField('Validated')
	role = SelectField('Role', coerce=int)
	submit = SubmitField('Submit')

	def __init__(self, user, *args, **kwargs):
		super(AdminEditProfileForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name) for \
		role in Role.query.order_by(Role.name).all()]

		self.user = user
		
	def validate_email(self, field):
		if field.data != self.user.email and \
		User.query.filter_by(email=field.data).first():
			flash('<i class="icon-warning" style="color: red;"></i> Email already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Email as already been registered.')

	def validate_username(self, field):
		if field.data != self.user.username and \
		User.query.filter_by(username=field.data).first():
			sug_usernames=User.suggest_valid_usernames_with(field.data)
			html="<br><u>Suggested Username list below</u>"
			for name in sug_usernames:
				html+="<br><li>%s</li>"%name
			flash('<i class="icon-warning" style="color: red;"></i> Username already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Username as already been registered.\n%s'%html)

class FakeCoinForm(Form):
	balance = IntegerField('Balance', validators=[Required()])
	submit = SubmitField('Submit')

class CouponForm(Form):
	coupon = StringField('Coupon code', validators=[Required()])
	package = SelectField('Packages', coerce=int)
	submit = SubmitField('Upgrade/Subscribe')

	def validate_coupon(self, field):
		coupon=Coupon.query.filter_by(code=field.data).first()
		if coupon is None or coupon.used:
			info = '<i class="icon-warning" style="color: red;"></i> Invalid/used coupon code.'
			flash(info)
			raise ValidationError(info)

		if coupon and coupon.package_type_id != self.package.data:
			info = '<i class="icon-warning" style="color: red;"></i> Coupon type not related with the package chose!'
			flash(info)
			raise ValidationError(info)

	def __init__(self, *args, **kwargs):
		super(CouponForm, self).__init__(*args, **kwargs)
		self.package.choices = [(p.id, p.name) for p in PackageType.query.all()]
		

class CommentForm(Form):
	body = StringField('', validators=[Required()])
	submit = SubmitField('Comment')

class SearchForm(Form):
	search = StringField("Green Search", validators=[Required()])
	submit = SubmitField('search')

class MessageForm(Form):
    message = TextAreaField(('Message'), validators=[])
    message_file = FileField('Message file', validators=[FileAllowed(message_files, 'Not more than 16mb files only!')])
    submit = SubmitField(('Send'))

class ProfilePixUploadForm(Form):
	pix = FileField('Update Profile Photo', validators=[FileRequired(), FileAllowed(images, 'Images only!')])
	preview = SubmitField('Preview')

class PasswordResetForm(Form):
	id = StringField('Identity', validators=[Required()])
	submit = SubmitField('Ask for password reset')

class PasswordResetValidatingForm(Form):
	password = PasswordField('New Password', validators=[Required(), EqualTo('password2', message='Passwords must match.')])
	password2 = PasswordField('Confirm New Password', validators=[Required()])
	submit = SubmitField('Reset')

	def validate_password(self, field):
		if self.password.data != self.password2.data != None:
			info ='Password must match'
			return ValidationError(info)

class ContactUsForm(Form):
	fname = StringField('First Name', validators=[Required()])
	lname = StringField('Last Name', validators=[Required()])
	subject = StringField('Subject', validators=[Required()])
	email = StringField('Email', validators=[Required(), Email()])
	message = TextAreaField('Message')
	submit = SubmitField('Send Message')
		
class BankWithdrawalForm(Form):
	"""docstring for BankWitdrawalForm"""
	amount = IntegerField('Amount', validators=[Required()])
	bank_name = StringField('Bank Name', validators=[Required()])
	account_name = StringField('Account Name', validators=[Required()])
	account_number = StringField('Account Number', validators=[Required()])
	submit = SubmitField('Request Now')

class CelebrityForm(Form):
    logo_file = FileField('Celebrity Logo', validators=[FileAllowed(images, 'Not more than 16mb files only!')])
    name = StringField('Celebrity Name', validators=[Required()])
    username = StringField('Celebrity Alias', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z0-9][A-Za-z0-9_.]*$', 0,
    	'Alias must have only letters, numbers, dots or underscores')])
    verified = BooleanField('Verified')
    picture_files = MultipleFileField('Celebrity Pictures', validators=[FileAllowed(post_images, 'Images only!')])
    submit = SubmitField(('Add'))

    def validate_username(self, field):
    	if Celebrity.query.filter_by(username=field.data, verified=False).first():
            unverified_celeb=Celebrity.query.filter_by(username=field.data, verified=False).first()
            unverified_celeb.delete()
            db.session.commit()

    	if Celebrity.query.filter_by(username=field.data, verified=True).first():
    		flash('<i class="icon-warning" style="color: red;"></i> Username already in use!')
    		raise ValidationError('Username as already been registered !!')

class CelebrityEditForm(Form):
    logo_file = FileField('Celebrity Logo', validators=[FileAllowed(images, 'Not more than 16mb files only!')])
    name = StringField('Celebrity Name', validators=[Required()])
    username = StringField('Celebrity Alias', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z0-9][A-Za-z0-9_.]*$', 0,
    	'Alias must have only letters, numbers, dots or underscores')])
    verified = BooleanField('Verified')
    picture_files = MultipleFileField('Celebrity Pictures', validators=[FileAllowed(post_images, 'Images only!')])
    submit = SubmitField(('Save'))

    def __init__(self, celebrity, *args, **kwargs):
    	super(CelebrityEditForm, self).__init__(*args, **kwargs)
    	self.celebrity = celebrity

    def validate_username(self, field):
    	if field.data != self.celebrity.username and Celebrity.query.filter_by(username=field.data, verified=False).first():
            unverified_celeb=Celebrity.query.filter_by(username=field.data, verified=False).first()
            unverified_celeb.delete()
            db.session.commit()

    	if field.data != self.celebrity.username and Celebrity.query.filter_by(username=field.data, verified=True).first():
    		flash('<i class="icon-warning" style="color: red;"></i> Username already in use!')
    		raise ValidationError('Username as already been registered !!')

class FanCardForm(Form):
    card_image = FileField('Passport Photo', validators=[FileRequired(), FileAllowed(post_images, 'Images only!')])
    name = StringField('Name', validators=[Required()])
    email = StringField('Email', validators=[Required()])
    sin_number = StringField('SIN Number', validators=[Required()])
    mother_maiden_name = StringField('Mother Maiden Name', validators=[Required()])
    employment = StringField('Employment', validators=[Required()])
    phone_number = StringField('Phone Number')
    submit = SubmitField('Create')

    def validate_email(self, field):
    	if FanCard.query.filter_by(email=field.data).first():
    		flash('<i class="icon-warning" style="color: red;"></i> Email already in use!')
    		raise ValidationError('Email as already been registered.')

class AdminFanCardEditForm(Form):
    card_image = FileField('Passport Photo', validators=[FileAllowed(post_images, 'Images only!')])
    fake_coin = IntegerField('Amount')
    name = StringField('Name', validators=[Required()])
    email = StringField('Email', validators=[Required()])
    sin_number = StringField('SIN Number', validators=[])
    mother_maiden_name = StringField('Mother Maiden Name', validators=[])
    employment = StringField('Employment', validators=[])
    phone_number = StringField('Phone Number')
    status = StringField('Status')
    submit = SubmitField('Update', render_kw={"class": "btn btn-primary"})

    def __init__(self, fan, *args, **kwargs):
    	super(AdminFanCardEditForm, self).__init__(*args, **kwargs)
    	self.fan = fan

    def validate_email(self, field):
    	if field.data != self.fan.fan_card.email and FanCard.query.filter_by(email=field.data).first():
    		flash('<i class="icon-warning" style="color: red;"></i>New Email already in use!')
    		raise ValidationError('New Email as already been registered.')


class FanCardUpdateForm(Form):
    card_image = FileField('Passport Photo', validators=[FileAllowed(post_images, 'Images only!')])
    name = StringField('Name', validators=[Required()])
    email = StringField('Email', validators=[Required()])
    sin_number = StringField('SIN Number', validators=[Required()])
    mother_maiden_name = StringField('Mother Maiden Name', validators=[Required()])
    employment = StringField('Employment', validators=[Required()])
    phone_number = StringField('Phone Number')
    submit = SubmitField('Update', render_kw={"class": "btn btn-primary"})

    def __init__(self, fan, *args, **kwargs):
    	super(FanCardUpdateForm, self).__init__(*args, **kwargs)
    	self.fan = fan

    def validate_email(self, field):
    	if field.data != self.fan.fan_card.email and FanCard.query.filter_by(email=field.data).first():
    		flash('<i class="icon-warning" style="color: red;"></i>New Email already in use!')
    		raise ValidationError('New Email as already been registered.')

class TrackingForm(Form):
	tracking_number = TextAreaField('Tracking Number', validators=[Required()])
	submit = SubmitField('Track', render_kw={"class":"button tracking-btn"})


class AddTrackingForm(Form):
	address = StringField('Address', validators=[Required()])
	submit = SubmitField('Add Track', render_kw={"class":"button tracking-btn"})

	def validate_tracking_number(self, field):
		if Tracking.query.filter_by(tracking_number=field.data).first():
			flash('<i class="icon-warning" style="color: red;"></i> Tracking number already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Tracking number as already been registered.')


status_list=['From', 'Arrived', 'Canceled', 'Delayed', 'Delivered', 'Departed', 'In Transit', 'On Hold', 'Out for Delivery', 'Pending', 'Preparing for Delivery', 'Returned', 'WE HAVE YOUR PACKAGE']

class AddTrackingHistoryForm(Form):
	status=SelectField('Status:', coerce=str)
	details = TextAreaField('Details', validators=[Required()])
	location = StringField('Location', validators=[Required()])
	image = FileField('Evidence', validators=[FileAllowed(post_images, 'Images only!')])
	submit = SubmitField('Add History', render_kw={"class":"button tracking-btn"})

	"""docstring for AddTrackingHistoryForm"""
	def __init__(self):
		super(AddTrackingHistoryForm, self).__init__()
		self.status.choices = [(stat,stat) for stat in status_list]
		

class WebDataForm(Form):
    # Basic Data
    name = StringField('Name', validators=[DataRequired()])
    name_abbreviation = StringField('Abbreviation', validators=[DataRequired()])
    logo = StringField('Logo URL', validators=[Optional()])
    payment_details = TextAreaField('Payment Details', validators=[Optional()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    exchange_rate = FloatField('Exchange Rate', validators=[DataRequired(), NumberRange(min=0)])

    # Post and Reward Data
    free_post_per_day = IntegerField('Free Posts per Day', validators=[DataRequired(), NumberRange(min=0)])
    post_fee = IntegerField('Post Fee', validators=[DataRequired(), NumberRange(min=0)])
    connection_fee = IntegerField('Connection Fee', validators=[DataRequired(), NumberRange(min=0)])
    usps_track_fee = IntegerField('USPS Track Fee', validators=[DataRequired(), NumberRange(min=0)])
    usps_track_history_fee = IntegerField('USPS Track History Fee', validators=[DataRequired(), NumberRange(min=0)])
    page_fee = IntegerField('Page Fee', validators=[DataRequired(), NumberRange(min=0)])

class CoinPackageForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    naira_amount = IntegerField('Naira Amount', validators=[DataRequired(), NumberRange(min=1)])
    naira_rate = FloatField('Naira Rate', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Save')

class CoinPackagePaymentForm(Form):
    receipt = FileField('Upload Receipt', validators=[DataRequired()])
    submit = SubmitField('Submit Payment')
		

class ClaimWinningForm(Form):

	email = StringField('Email', validators=[Required(), Email()])

	username = StringField('Username', validators=[Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,'Usernames must have only letters, numbers, dots or underscores')])

	mobile_number = StringField('Mobile Number', validators=[Required()])

	password = PasswordField('Password', validators=[Required(), 
		EqualTo('password2', message='<i class="icon-warning" style="color: red;"></i> Passwords must match.')])

	password2 = PasswordField('Confirm password', validators=[Required()])

	submit = SubmitField('Claim')	
	
	def validate_email(self, field):
		if User.query.filter_by(email=field.data.lower()).first():
			flash('<i class="icon-warning" style="color: red;"></i> Email already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Email as already been registered.')

	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			sug_usernames=User.suggest_valid_usernames_with(field.data)
			html="<br><u>Suggested Username list below</u>"
			for name in sug_usernames:
				html+="<br><li>%s</li>"%name
			flash('<i class="icon-warning" style="color: red;"></i> Username already in use!')
			raise ValidationError('<i class="icon-warning" style="color: red;"></i> Username as already been registered.\n%s'%html)

	def validate_password(self, field):
		if self.password.data != self.password2.data != None:
			info ='<i class="icon-warning" style="color: red;"></i> Password must match'
			flash(info)


class AddWinningForm(Form):
    name = StringField('Winner Name', validators=[DataRequired()])
    image_url = StringField('Image URL', validators=[DataRequired()])
    amount = IntegerField('Winning Amount', validators=[DataRequired(), NumberRange(min=200)])
    days_b4_expiration = IntegerField('Days b4 Expiration', validators=[DataRequired(), NumberRange(min=1)])
    celebrity_id = SelectField('Client Celebrity', coerce=int, validators=[DataRequired()])
    referral_id = StringField('Referrer ID', validators=[DataRequired()])
    submit = SubmitField('Add Winning')

    def __init__(self, **kwargs):
    	super(AddWinningForm, self).__init__(**kwargs)
    	self.celebrity_id.choices = [(celeb.id, celeb.name) for celeb in Celebrity.query.all()]
		