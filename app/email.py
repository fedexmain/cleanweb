from flask import render_template, flash, current_app as app
from flask_mail import Message
from . import mail
from . import create_app
from .web_dict import web_dict as web_dict_bank

web_dict=web_dict_bank()
#   Abstracting the  common parts of the application’s email sending functionality 
# into a function called send_email!
def send_email(to, subject, template, web_dict=web_dict, **kwargs):
	msg = Message(app.config.get('MAIL_SUBJECT_PREFIX') + subject, 
		sender=app.config.get('MAIL_SENDER'), 
		recipients=[to])
	msg.body = render_template(template + '.txt', **kwargs)
	msg.html = render_template(template + '.html', **kwargs)

	mail.send(msg)

def notify_admin_of_payment(admin_list, payment):
    msg = Message("New Payment Notification",
                  sender=app.config.get('MAIL_SENDER'),
                  recipients=[admin.email for admin in admin_list])
    msg.html = render_template('email/admin_payment_notification.html', payment=payment)
    mail.send(msg)

def notify_user_of_verification(payment):
    msg = Message("Payment Verified",
                  sender=app.config.get('MAIL_SENDER'),
                  recipients=[payment.user.email])
    msg.html = render_template('email/user_payment_verified.html', user=payment.user, payment=payment)
    mail.send(msg)

def send_message_notification(user, message, attachments=None, sync=False):
    if user.email:
        subject = f"NEW MESSAGE NOTIFICATION from {message.sender.name}"
        send_email(user.email, subject, 'email/reply', attachments=attachments, sync=sync, user=user, message=message)
