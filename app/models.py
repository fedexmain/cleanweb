from sqlalchemy.exc import IntegrityError
import hashlib
from . import db, moment
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from . import login_manager
from .web_dict import web_dict, delete_web_file, list_folder_filenames
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, abort, flash, url_for
from datetime import datetime
from time import time
import json
from markdown import markdown
import bleach
import random
from random import randint
import datetime_distance as DateTimeDistance


def GenerateSecureCode():
    import random
    abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    num = '1234567890'
    code_maker_list=[abc, num]
    code=''
    while len(code) < 3:
        resp = random.choice(abc[:])
        if not resp in code:
            code+=resp
    code+='-'

    for n in range(3):
        for m in range(4):
            code_maker=random.choice(code_maker_list)
            code+=random.choice(code_maker)

        if len(code) < 18:
            code+='-'

    return code

def generate_tracking_number(length=12):
    """
    Generate a FedEx-style tracking number.
    
    Args:
        length (int): Length of the tracking number (default is 12).
                     Can be 12, 15, or 20 digits.
    
    Returns:
        str: A randomly generated tracking number.
    """
    if length not in [12, 15, 20]:
        raise ValueError("Tracking number length must be 12, 15, or 20 digits.")
    
    # Generate a random number with the specified length
    tracking_number = ''.join(random.choices('0123456789', k=length))
    while Tracking.query.filter_by(tracking_number=tracking_number).first():
        tracking_number = ''.join(random.choices('0123456789', k=length))
        
    return tracking_number


#Creating Database model
class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    VEND_COUPONS = 0X10
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')


    @staticmethod
    def insert_roles():
        roles = {
        'User': (Permission.FOLLOW |
        Permission.COMMENT |
        Permission.WRITE_ARTICLES, True),
        'Vendor':(Permission.FOLLOW |
        Permission.COMMENT |
        Permission.WRITE_ARTICLES |
        Permission.VEND_COUPONS, False),
        'Moderator': (Permission.FOLLOW |
        Permission.COMMENT |
        Permission.WRITE_ARTICLES |
        Permission.VEND_COUPONS |
        Permission.MODERATE_COMMENTS, False),
        'Administrator': (0xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

def get_random_color():
    import random
    r=random.randrange(100)
    g=random.randrange(100)
    b=random.randrange(100)
    return '#{:02x}{:02x}{:02x}'.format(int(r*2.55),int(g*2.55),int(b*2.55))

class TransactionRecipe(db.Model):
    __tablename__ = "TransactionRecipes"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, default=None, nullable=True)
    url = db.Column(db.String, default=None, nullable=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'))

    def __init__(self, filename=None, url=None, **kwargs):
        super(TransactionRecipe, self).__init__(**kwargs)
        self.filename = filename
        self.url = url

    def delete(self):
        try:
            delete_web_file(self.url)
        except Exception as e:
            pass
        db.session.delete(self)
 
    def __repr__(self):
        return '<id: {}, transaction_id:{}>'.format(self.id, self.transaction_id)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    point = db.Column(db.Integer)
    amount = db.Column(db.Integer)
    body = db.Column(db.String(64))
    status = db.Column(db.String(32))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    recipes= db.relationship('TransactionRecipe', backref="transaction", lazy='dynamic')
    """docstring for Transaction"""
    def __init__(self, **kwargs):
        super(Transaction, self).__init__(**kwargs)

class Themes(db.Model):
    __tablename__ = 'themes'
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(32), default=get_random_color)
    second = db.Column(db.String(32), default=get_random_color)
    third = db.Column(db.String(32), default=get_random_color)
    forth = db.Column(db.String(32), default=get_random_color)
    is_default = db.Column(db.Boolean, default=False)
    web_data_id = db.Column(db.Integer, db.ForeignKey('web_datas.id'))

    def __init__(self, **kwargs):
        super(Themes, self).__init__(**kwargs)

    def set_to_random(self):
        self.first = get_random_color()
        self.second = get_random_color()
        self.third = get_random_color()
        self.forth = get_random_color()
        self.is_default = False
        db.session.commit()

    def set_to_default(self):
        self.first = '#000'
        self.second = '#fff'
        self.third = '#c0c0c0'
        self.forth = '#fd7e14'
        self.is_default = True
        db.session.commit()


class WebData(db.Model):
    """docstring for WebData"""
    #Basic Data
    __tablename__ = 'web_datas'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    name_abbreviation = db.Column(db.String(32), unique=True)
    logo = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True)
    exchange_rate = db.Column(db.Float, default=0.5)
    #Themes Data
    themes = db.relationship('Themes', backref="web_data", uselist=False)
    #Post and Reward Data
    free_post_per_day = db.Column(db.Integer, default=5)
    post_fee = db.Column(db.Integer, default=50)
    connection_fee = db.Column(db.Integer, default=2000)
    usps_track_fee = db.Column(db.Integer, default=816)
    usps_track_history_fee = db.Column(db.Integer, default=432)
    page_fee = db.Column(db.Integer, default=5)
    free_post_start_time = db.Column(db.DateTime, default=datetime.utcnow)
    payment_details = db.Column(db.Text)
    payment_details_html = db.Column(db.Text)

    def __init__(self, **kwargs):
        super(WebData, self).__init__(**kwargs)

        if self.themes is None:
            self.themes = Themes(first='#000', second='#fff', third='#c0c0c0', 
                forth='#fd7e14', is_default=True, web_data_id=self.id)
            db.session.add(self.themes)

    @staticmethod
    def on_changed_payment_details(self, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
            'h1', 'h2', 'h3', 'p', 'br']
        self.payment_details_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format='html'), 
                tags=allowed_tags,
                strip=True)
            )

    def generate_logo(self):
        folder = 'logo'
        logos = []
        for filename in list_folder_filenames(folder):
            logos.append(folder+'/'+filename)

        if len(logos):
            random.shuffle(logos)
            return logos[0]
        return self.logo

    def build_default():
        w=WebData(name="BlurtOutLoud", name_abbreviation="BOL", 
                logo="logo.png", email="blurtoutloud@gmail.com")
        db.session.add(w)
        db.session()
        return w

    def convert_naira_to_coin(self, naira_amount):
        return float(naira_amount)*self.exchange_rate

    def convert_coin_to_naira(self, coin_amount):
        return float(coin_amount)/self.exchange_rate

    @property
    def remaining_free_post(self):
        return self.free_post_per_day - Post.query.filter_by(is_free=True).count()
db.event.listen(WebData.payment_details, 'set', WebData.on_changed_payment_details)


profit_percentage=30
class PackageType(db.Model):
    __tablename__ = 'PackageTypes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    amount = db.Column(db.Integer)
    profit_percentage = db.Column(db.Integer)
    task_bonus = db.Column(db.Integer)
    referral_bonus = db.Column(db.Integer)
    default = db.Column(db.Boolean, default=False, index=True)
    available = db.Column(db.Boolean, default=True, index=True)
    coupons = db.relationship('Coupon', backref='package_type', lazy='dynamic')

    @property
    def interest(self):
        return self.profit_percentage/100*self.amount

    @staticmethod
    def insert_package_types():
        packages = {'Basic':(40, profit_percentage, 2, 5, True),
        'Premium':(65, profit_percentage, 4, 10, False),
        'Silver':(130, profit_percentage, 8, 15, False),
        'Platinum':(315, profit_percentage, 16, 20, False),
        'Royal':(630, profit_percentage, 32, 25, False),
        'Gold':(1250, profit_percentage, 64, 30, False)}

        for p in packages:
            package = PackageType.query.filter_by(name=p).first()
            if package is None:
                package = PackageType(name=p)
            package.amount = packages[p][0]
            package.profit_percentage = packages[p][1]
            interest = ((package.profit_percentage/100)*package.amount)
            cashout = interest+package.amount
            referral_bonus = str(cashout/30)
            if '.' in referral_bonus:
                referral_bonus = referral_bonus[:referral_bonus.index('.')+2]
            else:
                referral_bonus += '.0'
            
            #print('\a', eval(referral_bonus))
            package.referral_bonus = eval(referral_bonus)
            package.task_bonus = package.referral_bonus
            package.default = packages[p][4]
            package.available = True
            db.session.add(package)
        db.session.commit()

    def delete(self):
        #To delete package type relaed coupons first
        for cp in self.coupons:
            cp.delete()
        db.session.delete(self)

    def generate_coupons(self, user, count=1):
        coupons = []
        if self.available:
            for u in range(count):
                coupon = Coupon(package_type=self, vendor=user)
                db.session.add(coupon)
                coupon.generate_code()
                coupons.append(coupon)
            
            db.session.commit()

        return coupons

    def __repr__(self):
        return '<PackageType %r>' % (self.name)


class Coupon(db.Model):
    """docstring for Coupon"""
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, unique=True)
    used = db.Column(db.Boolean, default=False)
    package_type_id = db.Column(db.Integer, db.ForeignKey('PackageTypes.id'))
    vendor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)


    def __init__(self, **kwargs):
        super(Coupon, self).__init__(**kwargs)
        if PackageType.query.all() == []:
            PackageType.insert_package_types()

        if self.package_type is None:
            self.package_type = PackageType.query.filter_by(default=True).first()

        if not self.code:
            self.generate_code()

    def generate_code(self):
        code = GenerateSecureCode()
        if not self.code:
            while Coupon.query.filter_by(code=code).first():
                code = GenerateSecureCode()
            self.code = code
        return code

    def use(self):
        self.used = True
        db.session.add(self)

    def verify_code(code):
        coupon = Coupon.query.filter_by(code=code).first()
        return(coupon is not None and not coupon.used)
        
    def delete(self):
        db.session.delete(self)


class PackageFile(db.Model):
    __tablename__ = 'PackageFiles'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, default=None, nullable=True)
    url = db.Column(db.String, default=None, nullable=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'))

    def __init__(self, filename=None, url=None, **kwargs):
        super(PackageFile, self).__init__(**kwargs)
        self.filename = filename
        self.url = url

    def delete(self):
        try:
            delete_web_file(self.url)
        except Exception as e:
            pass
        db.session.delete(self)

    def __repr__(self):
        return "<PackageFile for %s package>"%self.package.user.username
        
class Package(db.Model):
    __tablename__ = 'packages'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer)
    profit_percentage = db.Column(db.Integer)
    task_bonus = db.Column(db.Integer, default=0)
    referring_bonus = db.Column(db.Integer, default=0)
    cash_requested = db.Column(db.Boolean, default=False, index=True)
    paid = db.Column(db.Boolean, default=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    coupon = db.relationship('Coupon', backref='package', uselist=False)
    payment_file = db.relationship('PackageFile', backref='package', uselist=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __init__(self, coupon, **kwargs):
        super(Package, self).__init__(**kwargs)
        self.amount = coupon.package_type.amount
        self.profit_percentage = coupon.package_type.profit_percentage
        self.referring_bonus = coupon.package_type.referral_bonus
        self.coupon = coupon

    @property
    def total_earnings(self):
        return self.interest+self.amount+self.referring_bonus

    @property
    def interest(self):
        return self.profit_percentage/100*self.amount

    def pay(self):
        self.paid = True
        db.session.add(self)

    def is_ripe_to_cash(self):
        cashout_rem_days = self.cashout_remaining_days
        return (cashout_rem_days == 0)

    def is_active(self):
        return(self.paid == self.cash_requested == self.is_ripe_to_cash() == False)

    @property
    def cashout_percent(self):
        days = 30 - self.cashout_remaining_days
        percent = str(days/30*100)
        if '.' in percent:
            percent=percent[:percent.index('.')+2]

        return eval(percent)

    @property
    def cashout_remaining_days(self):
        now = datetime.utcnow()
        month=now.month - self.timestamp.month
        days=now.day - self.timestamp.day

        if month:
            if month > 1 or days > 0:
                days = 30
            else:
                return 0 #abs(days)
        
        return (30 - days)

    def delete(self):
        if self.payment_file:
            self.payment_file.delete()
        if self.coupon:
            self.coupon.delete()
        db.session.delete(self)

    def reset(self):
        self.payment_file.delete()
        self.cash_requested = False
        self.paid = False
        db.session.add(self)

    def __repr__(self):
        if self.user is None or self.coupon is None:
            self.delete()
            return '<%r Delete Package lacking main attribute %r>'
        return '<%r Package, for %r>' % (self.coupon.package_type.name, self.user.username)
        
class DailyTask(db.Model):
    __tablename__ = 'DailyTasks'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    @staticmethod
    def on_changed_body(self, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
            'h1', 'h2', 'h3', 'p']
            
        self.body_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format='html'), 
                tags=allowed_tags, strip=True)
            )
db.event.listen(DailyTask.body, 'set', DailyTask.on_changed_body)


class CoinRecharger(db.Model):
    __tablename__ = 'CoinRechargers'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String, unique=True)
    amount = db.Column(db.Integer) 
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __init__(self, **kwargs):
        super(CoinRecharger, self).__init__(**kwargs)
        if self.code is None:
            self.generate_code()

    @staticmethod
    def make_coin_code(amount, user):
        coin = CoinRecharger(amount=amount, sender_id=user.id)
        db.session.add(coin)
        db.session.commit()
        return coin
        
    def generate_code(self):
        if not self.code:
            code = GenerateSecureCode()
            while CoinRecharger.query.filter_by(code=code).first():
                code = GenerateSecureCode()
            self.code = code
        return self.code

    def use(self):
        self.delete()

    def verify_code(code):
        code = CoinRecharger.query.filter_by(code=code).first()
        return(code is not None and not code.used)

    def delete(self):
        db.session.delete(self)


class CoinPackage(db.Model):
    __tablename__ = 'coin_packages'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    naira_amount = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    naira_rate = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    payments = db.relationship('CoinPackagePayment', backref='coin_package')
    limited = db.Column(db.Boolean, default=True)  # Indicates if package has limit set amount or not

    def delete(self):
        for payment in self.payments:
            if not payment.verified and not payment.rejected:
                return 'There is a payment yet to be verified on this coin package!!!'
            payment.delete()
        db.session.delete(self)
        return 'Coin package successfully deleted !!'

    @property
    def dollar_amount(self):
        return self.naira_amount * self.naira_rate

    @property
    def dollar_rate(self):
        return (self.naira_amount / self.dollar_amount)

    @property
    def min_amount(self):
        return (self.dollar_amount-(self.dollar_amount/4))

    @property
    def max_amount(self):
        return self.dollar_amount

    def is_single_coin_package(self):
        return self.quantity < 1

    def is_multi_coin_package(self):
        return self.quantity > 1

    def make_coin_for(self, user):
        amount=self.dollar_amount
        total_amount=0
        coin_result = ''
        if self.is_multi_coin_package():
            max_decrease = amount/random.randint(4,10)
            decreased_amount = amount - max_decrease
            lines=self.quantity
            for num in range(lines):
                if total_amount < decreased_amount:
                    random_amount=random.randint(100, int(amount) if int(amount) > 100 else 200)

                    if (random_amount+total_amount) > decreased_amount:
                        random_amount=(decreased_amount - total_amount) / (lines-num)

                    coin = CoinRecharger.make_coin_code(random_amount, user)
                    if coin:
                        coin_result+=f"${coin.amount}|{coin.code}{', ' if num != lines-1 else ''}"
                        db.session.add(coin)
                    total_amount+=random_amount
        else:
            coin = CoinRecharger.make_coin_code(amount, user)
            if coin:
                coin_result=f"{coin.amount}|{coin.code}"
                db.session.add(coin)
            total_amount = amount

        user.load_coin(coin)

        return total_amount, coin_result


    def insert_coin_packages():
        packages = [
            {'name': 'Random-mINI', 'naira_amount': 35000, 'naira_rate': 0.3429, 'quantity': 8},
            {'name': 'Certain-mINI', 'naira_amount': 35000, 'naira_rate': 0.6429, 'quantity': 1},
            {'name': 'Random-cOMBO', 'naira_amount': 70000, 'naira_rate': 0.7429, 'quantity': 8},
            {'name': 'cERTAIN-cOMBO', 'naira_amount': 70000, 'naira_rate': 0.8429, 'quantity': 1}
        ]
        
        for package in packages:
            if not CoinPackage.query.filter_by(name=package['name']).first():
                coin_package = CoinPackage(
                    name=package['name'],
                    naira_amount=package['naira_amount'],
                    naira_rate=package['naira_rate'],
                    quantity=package['quantity']
                )
                db.session.add(coin_package)
        db.session.commit()


class CoinPackagePayment(db.Model):
    __tablename__ = 'coin_package_payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    coin_package_id = db.Column(db.Integer, db.ForeignKey('coin_packages.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    receipt = db.Column(db.String, nullable=False)  # Path to uploaded receipt file
    details = db.Column(db.String)  
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)
    rejected = db.Column(db.Boolean, default=False)  # Indicates if payment was rejected

    def delete(self):
        db.session.delete(self)
        
    def verify(self):
        """Verify the payment and link to payment."""
        if not self.verified and not self.rejected:
            # Retrieve package details and generate coins for the user
            package = CoinPackage.query.get(self.coin_package_id)
            total_amount, coin_result = package.make_coin_for(self.user)
            self.details = str(coin_result)
            self.verified = True
            self.delete_receipt()
            return total_amount, coin_result
        return None

    def delete_receipt(self):
        delete_web_file(self.receipt)
        self.receipt = ''

    def reject(self):
        self.rejected=True

    def get_status(self):
        if self.verified:
            return 'Verified'
        elif self.rejected:
            return 'Rejected'
        else:
            return 'Pending Verification'



class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
    primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
    primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Follow %s %s>'%(self.followed_id, self.follower_id)


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sent = db.Column(db.Boolean, default=True)
    read = db.Column(db.Boolean, default=False)
    delivered=db.Column(db.Boolean, default=False)
    file=db.relationship('MessageRecipe', backref='message', lazy='dynamic')

    @staticmethod
    def on_changed_body(self, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
            'h1', 'h2', 'h3', 'p']
        self.body_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format='html'), 
                tags=allowed_tags,
                strip=True)
            )

    def delete(self):
        for file in self.file.all():
            file.delete()
        db.session.delete(self)

    def __repr__(self):
        return '<Message {}>'.format(self.body)
db.event.listen(Message.body, 'set', Message.on_changed_body)

class MessageRecipe(db.Model):
    __tablename__ = "MessageRecipes"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, default=None, nullable=True)
    url = db.Column(db.String, default=None, nullable=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'))
    is_deletable = db.Column(db.Boolean, default=True) 

    def __init__(self, filename=None, url=None, **kwargs):
        super(MessageRecipe, self).__init__(**kwargs)
        self.filename = filename
        self.url = url

    def check_to_delete_a_day_old_file(self):
        file = self
        past_datetime = file.message.timestamp
        if not file.message:
            file.delete()

        elif DateTimeDistance.fromNow(self.message.timestamp,'in_hour') >= 24 and file.url != '':
            try:
                if file.url:
                    delete_web_file(file.url)
            except Exception as e:
                flash(e)
            
            file.url = ''
            db.session.add(file)

        db.session.commit()

    def delete(self):
        if self.is_deletable:
            try:
                delete_web_file(self.url)
            except:
                pass
                
        db.session.delete(self)
 
    def __repr__(self):
        return '<id: {}, message_id:{}>'.format(self.id, self.message_id)

class PostRecipe(db.Model):
    __tablename__ = "PostRecipes" 
    id = db.Column(db.Integer, primary_key=True)
    is_public = db.Column(db.Boolean, nullable=False)
    filename = db.Column(db.String, default=None, nullable=True)
    url = db.Column(db.String, default=None, nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def __init__(self, is_public, filename=None, url=None, **kwargs):
        super(PostRecipe, self).__init__(**kwargs)
        self.is_public = is_public
        self.filename = filename
        self.url = url

    def delete(self):
        try:
            delete_web_file(self.url)
        except Exception as e:
            pass
        db.session.delete(self)
 
    def __repr__(self):
        return '<id: {}, post_id:{}>'.format(self.id, self.post_id)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    wall_owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)
    reward_points = db.Column(db.Integer, default=0)
    is_free = db.Column(db.Boolean, default=False)
    is_news = db.Column(db.Boolean, default=False)
    #Relationship
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    likes = db.relationship('PostLike', backref='post', lazy='dynamic')
    dislikes = db.relationship('PostDislike', backref='post', lazy='dynamic')
    recipes = db.relationship('PostRecipe', backref='post', lazy='dynamic')

    def calculate_and_assign_rewards(self):
        likes_count = self.likes.count()
        reward_points = calculate_rewards(likes_count)
        self.reward_points += reward_points

    def get_point_per_like(self):
        return calculate_rewards(self.likes.count())

    def cashout(self):
        if self.reward_points:
            self.author.coin+= self.reward_points
            web_data = WebData.query.first()
            trans = Transaction(point=self.reward_points, amount=web_data.convert_to_naira(self.reward_points), 
                body=f'Reward Point of a Content posted around {self.timestamp}',
                status='Success', user=self.author)
            db.session.add(trans)
            self.reward_points=0
    

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            u2 = User.query.offset(randint(0, user_count - 1)).first()
            if u == u2 or u.is_a_friend_to(u2):
                p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                    timestamp=forgery_py.date.date(True),
                    author=u, wall_owner=u2)

                db.session.add(p)
                db.session.commit()


    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
            'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format='html'), 
                tags=allowed_tags,
                strip=True)
            )

    @property
    def likers(self):
        return User.query.join(PostLike, PostLike.user_id==User.id).filter(PostLike.post_id==self.id).all()
    
    @property
    def dislikers(self):
        return User.query.join(PostDislike, PostDislike.user_id==User.id).filter(PostDislike.post_id==self.id).all()

    def delete(self):
        for recipes in self.recipes.all():
            recipes.delete()
            
        for like in self.likes.all():
            like.delete()

        for comment in self.comments.all():
            comment.delete()

        db.session.delete(self)

    def __repr__(self):
        return '<Post %r>' % (self.id)

db.event.listen(Post.body, 'set', Post.on_changed_body)


class PostLike(db.Model):
    __tablename__ = 'PostLikes'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def __init__(self, **kwargs):
        super(PostLike, self).__init__(**kwargs)
        self.post.calculate_and_assign_rewards()

    def delete(self):
        db.session.delete(self)

class PostDislike(db.Model):
    __tablename__ = 'PostDislikes'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def delete(self):
        db.session.delete(self)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    likes = db.relationship('CommentLike', backref='comment', lazy='dynamic')
    dislikes = db.relationship('CommentDislike', backref='comment', lazy='dynamic')

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py
        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            p= Post.query.offset(randint(0, user_count - 1)).first()
            
            c = Comment(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                timestamp=forgery_py.date.date(True),
                author=u, post=p)
            try:
                db.session.add(c)
                db.session.commit()
            except IntegrityError as e:
                print(e)
                db.session.rollback()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
        target.body_html = bleach.linkify(bleach.clean(
        markdown(value, output_format='html'),
        tags=allowed_tags, strip=True))

    @property
    def likers(self):
        return User.query.join(CommentLike, CommentLike.user_id==User.id).filter(CommentLike.comment_id==self.id).all()
    
    @property
    def dislikers(self):
        return User.query.join(CommentDislike, CommentDislike.user_id==User.id).filter(CommentDislike.comment_id==self.id).all()

    def delete(self):
        for like in self.likes:
            like.delete()
        db.session.delete(self)
db.event.listen(Comment.body, 'set', Comment.on_changed_body)

class CommentLike(db.Model):
    __tablename__ = 'CommentLikes'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))

    def delete(self):
        db.session.delete(self)

class CommentDislike(db.Model):
    __tablename__ = 'CommentDislikes'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'))

    def delete(self):
        db.session.delete(self)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    payload_json = db.Column(db.Text)
    note = db.Column(db.String(200))
    read = db.Column(db.Boolean, default=False)

    def get_data(self):
        return json.loads(str(self.payload_json))

    def delete(self):
        db.session.delete(self)

    def __repr__(self):
        return '<%s Notification %s>'%(self.user.username, self.id)

        

class BadgeNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)

    def get_data(self):
        return json.loads(str(self.payload_json))


def calculate_rewards(likes_count):
    reward_points = 0

    if likes_count >= 5:
        reward_points += 5  # Assign a base reward for any post with at least 10 likes

    if likes_count >= 10:
        reward_points += 10  # Assign a base reward for any post with at least 10 likes

    if likes_count >= 50:
        reward_points += 20  # Additional reward for posts with 50 or more likes

    if likes_count >= 100:
        reward_points += 30  # Additional reward for posts with 100 or more likes

    if likes_count >= 500:
        reward_points += 40  # Additional reward for posts with 500 or more likes

    if reward_points == 0:
        reward_points+=1.5

    return reward_points

class ConnectHook(db.Model):
    __tablename__ = 'ConnectHooks'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class CelebrityLogo(db.Model):
    __tablename__ = "CelebrityLogos" 
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, default=None, nullable=True)
    url = db.Column(db.String, default=None, nullable=True)
    celebrity_id = db.Column(db.Integer, db.ForeignKey('celebrities.id'))

    def __init__(self, filename=None, url=None, **kwargs):
        super(CelebrityLogo, self).__init__(**kwargs)
        self.filename = filename
        self.url = url

    def delete(self):
        try:
            delete_web_file(self.url)
        except:
            pass
        db.session.delete(self)
 
    def __repr__(self):
        return '<CelebrityLogo:{}>'.format(self.id)

class CelebrityPicture(db.Model):
    __tablename__ = "CelebrityPictures" 
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, default=None, nullable=True)
    url = db.Column(db.String, default=None, nullable=True)
    celebrity_id = db.Column(db.Integer, db.ForeignKey('celebrities.id'))

    def __init__(self, filename=None, url=None, **kwargs):
        super(CelebrityPicture, self).__init__(**kwargs)
        self.filename = filename
        self.url = url

    def delete(self):
        try:
            delete_web_file(self.url)
        except:
            pass
        db.session.delete(self)
 
    def __repr__(self):
        return '<CelebrityPicture:{}>'.format(self.id)

class Celebrity(db.Model):
    __tablename__ = 'celebrities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True)
    username = db.Column(db.String(32), unique=True, index=True)
    verified = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime(), default=datetime.utcnow)
    #------------------------------------------------------------
    fans = db.relationship('User', backref='celebrity', lazy='dynamic')
    pictures = db.relationship('CelebrityPicture', backref='celebrity', lazy='dynamic')
    logo = db.relationship('CelebrityLogo', backref='celebrity', lazy='dynamic')

    def delete(self):
        for pictures in self.pictures.all():
            pictures.delete()

        for logos in self.logo.all():
            logos.delete()

        db.session.delete(self)

    def __repr__(self):
        return '<Celebrity %r>' % (self.name)
        
class FanCard(db.Model):
    __tablename__ = "FanCards"
    id = db.Column(db.Integer, primary_key=True)
    fan_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))
    sin_number = db.Column(db.String(200))  # Path to the fan card image file
    mother_maiden_name = db.Column(db.String(200))  # Path to the fan card image file
    employment = db.Column(db.String(200))  # Path to the fan card image file
    barcode_image = db.Column(db.String(200))  # Path to the barcode image file
    image_url = db.Column(db.String(200))  # Path to the fan card image file
    status = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    @property
    def update_list(self):
        return [self.name, self.email, self.phone_number, self.sin_number, self.mother_maiden_name, self.employment]

    def need_update(self):
        return (None in self.update_list or '' in self.update_list)

    def __repr__(self):
        return f'<FanCard {self.name}>'
        
class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<Subscriber {self.email}>'

    def delete(self):
        db.session.delete(self)

class TrackingHistory(db.Model):
    __tablename__ = 'tracking_histories'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Text)
    details = db.Column(db.Text)
    location = db.Column(db.Text)
    tracking_id = db.Column(db.Integer, db.ForeignKey('trackings.id'))
    image_url = db.Column(db.String(200))  # Path to the history image file
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
        
class Tracking(db.Model):
    __tablename__ = 'trackings'
    id = db.Column(db.Integer, primary_key=True)
    maker_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tracking_number = db.Column(db.String(128), unique=True, default=generate_tracking_number)
    address = db.Column(db.String(128))
    email = db.Column(db.String(64))
    platform = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    histories = db.relationship('TrackingHistory', backref='tracking', lazy='dynamic')

    @property
    def status(self):
        stat='Arrived & Processing'
        if self.histories.count():
            stat=self.histories.all()[-1].status
        return stat

    def default_status_details(self):
        return f"Your item Arrived at {self.platform} Regional Facility DISTRIBUTION CENTER."

class Winning(db.Model):
    __tablename__ = 'winnings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True)
    image_url = db.Column(db.String(200))
    amount = db.Column(db.Integer())
    referral_id = db.Column(db.String(32))
    celebrity_id = db.Column(db.Integer)
    days_b4_expiration = db.Column(db.Integer())
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def celebrity(self):
        return Celebrity.query.filter_by(id=self.celebrity_id).first()


    @property
    def referral(self):
        return User.query.filter_by(referring_id=self.referral_id).first()

    def claim(self, username, email, mobile_number, password):
        # Check if the user already exists
        existing_user = User.query.filter_by(email=email.lower()).first() or User.query.filter_by(username=username).first()
        if existing_user:
            flash('A user with this email already exists.', 'danger')
            return None

        # Create a new user from the winning claim
        new_user = User(
            name=self.name,
            profile_pix_url=self.image_url,
            fake_coin=self.amount or 500000,
            username=username,
            email=email.lower(),
            mobile_number=mobile_number,
            password=password,
            role=Role.query.filter_by(name='User').first(),
            referral_id=self.referral_id,
            celebrity_id=self.celebrity_id
        )

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        self.delete()
        flash('You have successfully claimed your Winning profile.', 'success')
        return new_user

    def delete(self):
        db.session.delete(self)

    def __repr__(self):
        return f"<Winning {self.name} - ${self.amount}>"


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    #==========================================================
    #           User information column
    #==========================================================
    #Requested information
    #----------------------------------------------------------
    name = db.Column(db.String(32), index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(32), unique=True, index=True)
    mobile_number = db.Column(db.String(32))
    #----------------------------------------------------------
    #System important information Columns
    #----------------------------------------------------------
    coin = db.Column(db.Integer, default=0)
    fake_coin = db.Column(db.Integer, default=500000)
    welcome_msg = db.Column(db.Text)
    welcome_msg_html = db.Column(db.Text)
    password_hash = db.Column(db.String(128))
    avatar_hash = db.Column(db.String(32))
    token = db.Column(db.String(32))
    confirmed = db.Column(db.Boolean, default=False)
    validated_for_work = db.Column(db.Boolean, default=False)
    profile_pix_url= db.Column(db.String, default=None, nullable=True)
    task_count = db.Column(db.Integer, default=0)
    last_task_count_time = db.Column(db.DateTime)
    referring_id = db.Column(db.String(32))
    referral_id = db.Column(db.String(32))
    referring_count = db.Column(db.Integer, default=0)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    last_message_read_time = db.Column(db.DateTime)
    last_notification_read_time = db.Column(db.DateTime)
    restriction_message=db.Column(db.Text)
    restriction_message_html=db.Column(db.Text)
    auto_reply = db.Column(db.Boolean, default=False)
    #User foreign model key column
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    celebrity_id = db.Column(db.Integer, db.ForeignKey('celebrities.id'))

    #----------------------------------------------------------
    #==========================================================
    #       User information column end
    #==========================================================

    #==========================================================
    #       User Relationship data
    #==========================================================
    coin_package_payments = db.relationship('CoinPackagePayment', backref='user', lazy='dynamic')

    fan_cards = db.relationship('FanCard', backref='fan', lazy='dynamic')

    tracking_list = db.relationship('Tracking', backref='maker', lazy='dynamic')

    posts = db.relationship('Post', foreign_keys=[Post.author_id], backref='author', lazy='dynamic')
    
    post_likes = db.relationship('PostLike', backref='user', lazy='dynamic')

    post_dislikes = db.relationship('PostDislike', backref='user', lazy='dynamic')

    Timeline_posts = db.relationship('Post', foreign_keys=[Post.wall_owner_id], backref='wall_owner', lazy='dynamic')

    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    comment_likes = db.relationship('CommentLike', backref='user', lazy='dynamic')
    
    comment_dislikes = db.relationship('CommentDislike', backref='user', lazy='dynamic')

    packages = db.relationship('Package', backref='user', lazy='dynamic')

    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')

    coin_rechargers = db.relationship('CoinRecharger', backref='sender', lazy='dynamic')

    notifications = db.relationship('Notification', backref='user',
                                    lazy='dynamic')

    vend_coupons = db.relationship('Coupon', backref='vendor',
                                    lazy='dynamic')

    badge_notifications = db.relationship('BadgeNotification', backref='user',
                                    lazy='dynamic')

    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='sender', lazy='dynamic')

    messages_received = db.relationship('Message',
                                        foreign_keys='Message.receiver_id',
                                        backref='receiver', lazy='dynamic')

    followed = db.relationship('Follow',
        foreign_keys=[Follow.follower_id],
        backref=db.backref('follower', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan')
    
    followers = db.relationship('Follow',
        foreign_keys=[Follow.followed_id],
        backref=db.backref('followed', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan')
    
    sent_hooks = db.relationship('ConnectHook', 
        foreign_keys=[ConnectHook.sender_id], 
        backref=db.backref('sender', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan')
    
    received_hooks = db.relationship('ConnectHook', 
        foreign_keys=[ConnectHook.receiver_id], 
        backref=db.backref('receiver', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan')
    #==========================================================
    #       User Relationship end
    #==========================================================

    #==========================================================
    #       User Model Methods
    #==========================================================
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        if Role.query.all() == []:
            Role.insert_roles()

        if self.role is None:
            #Assign an admin role to account registered with the current app configuration admin email
            if self.email == current_app.config['ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()

            #set user role to default if not yet provided
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

        #Make user profile avatar hash if email is available
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

        #Generate a username if not provided
        if self.name is None or self.name == '':
            self.name = 'Unknown'
        if self.username is None and self.name:
            self.username=User.suggest_valid_usernames_with(random.choice(self.name.split(' ')))[0]

        if not self.token:
            self.generate_confirmation_token()
        
        if not self.referring_id:
            self.generate_referring_id()

        #You have to follow yourself to see your own posts
        self.follow(self)
    #==========================================================
    #       User information methods
    #==========================================================

    #   Requested information methods
    #==========================================================
    def default_welcome_msg(self, user):
        return f"Dear {user.name.split(' ')[0]}, welcome to {user.celebrity.name if user.celebrity else 'our'} website. Thanks for navigating through!.. how may i help you?!"


    def greet(self, user):
        if not user.is_following(self):
            user.follow(self)
        msg=Message(body=self.welcome_msg or self.default_welcome_msg(user),
            sender=self, receiver=user)
        db.session.add(msg)

    @staticmethod
    def on_changed_restriction_message(self, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
            'h1', 'h2', 'h3', 'p', 'br']
        self.restriction_message_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format='html'), 
                tags=allowed_tags,
                strip=True)
            )

    @staticmethod
    def on_changed_welcome_msg(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
            'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(
            bleach.clean(
                markdown(value, output_format='html'), 
                tags=allowed_tags,
                strip=True)
            )

    @staticmethod
    def on_changed_email(self, value, oldvalue, initiator):
        self.avatar_hash = hashlib.md5(value.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        if password:
            self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        if password and self.password_hash:
            return check_password_hash(self.password_hash, password)
    #==========================================================
    #   Requested information methods end
    #==========================================================
    #   System information methods
    #==========================================================

    #Login manager current_user loading method
    #----------------------------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    #----------------------------------------------------------

    def generate_referring_id(self):
        ref_id = hashlib.md5(GenerateSecureCode().encode()).hexdigest()
        while User.query.filter_by(referring_id=ref_id).first():
            ref_id = hashlib.md5(GenerateSecureCode().encode()).hexdigest()
        self.referring_id = ref_id
        return ref_id

    def get_referring_id(self):
        if self.referring_id == None:
            self.generate_referring_id()
        return self.referring_id

    #----------Others----------------------------------

    @property
    def fan_card(self):
        return self.fan_cards.first()

    @property
    def connected_hooks(self):
        return self.received_hooks.union(self.sent_hooks)

    def is_connected_with(self, user):
        return (not self.connected_hooks.filter_by(sender=user).first() is None) or (not self.connected_hooks.filter_by(receiver=user).first() is None)
    
    def deduct_charges(self, amount):
        if self.can_pay_charges(amount):
            if not self.is_administrator():
                self.coin-=amount
                db.session.add(self)

    def can_pay_charges(self, amount):
        if self.is_administrator():
            return True
        if self.coin == None:
            self.coin = 0
        return (self.coin >= amount )#or self.is_administrator()) 

    def has_free_post(self):
        return (not self.posts.filter_by(is_free=True).first() is None)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
            db.session.commit()
    
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
        .filter(Follow.follower_id == self.id)

    @property
    def follower_users(self):
        return User.query.join(Follow, Follow.follower_id == User.id)\
        .filter(Follow.followed_id == self.id)

    @property
    def followed_users(self):
        return User.query.join(Follow, Follow.followed_id == User.id)\
        .filter(Follow.follower_id == self.id)

    def get_follower_users(self):
        return self.follower_users.all()

    def get_followed_users(self):
        return self.followed_users.all()

    def get_mutual_followed_with(self, user):
        from collections import Counter
        counter = Counter(self.get_followed_users()+user.get_followed_users())
        mutual_followed = [user for user,count in counter.items() if count > 1]
        if self in mutual_followed:
            mutual_followed.pop(mutual_followed.index(self))
        return mutual_followed
 
    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None
    
    def make_coin(self, amount):
        return CoinRecharger.make_coin_code(amount,self)

    def load_coin(self, coin):
        if not self.coin:
            self.coin=coin.amount
        else:
            self.coin+=coin.amount

        web_data=WebData.query.first()
        coin_trans = Transaction(point=coin.amount, amount=web_data.convert_coin_to_naira(coin.amount), body="Recharge Coin", status='Success', user=self)
        db.session.add(coin_trans)
        coin.use()
        db.session.commit()

    def generate_referring_id(self):
        ref_id = hashlib.md5(GenerateSecureCode().encode()).hexdigest()
        while User.query.filter_by(referring_id=ref_id).first():
            ref_id = hashlib.md5(GenerateSecureCode().encode()).hexdigest()
        self.referring_id = ref_id
        return ref_id

    @property
    def referral(self):
        return User.query.filter_by(referring_id=self.referral_id).first()
        

    def add_referring_bonus(self, amount):
        self.referring_count +=1
        self.coin+= amount
        db.session.add(self)

    def add_task_bonus(self):
        self.task_count +=1
        self.last_task_count_time = datetime.utcnow()
        db.session.add(self)
        for p in self.packages.all():
            if p.is_active():
                p.task_bonus += p.package_type.task_bonus
                db.session.add(p)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

    def has_active_package(self):
        for p in self.packages.all():
            if p.is_active():
                return True
        return False

    def can_still_run_task(self):
        lt=self.last_task_count_time
        now = datetime.utcnow()
        try:
            return (lt.day != now.day)
        except Exception as e:
            return True

    #Method for creating automatic names
    #----------------------------------------------------------
    def generate_names(self, count=10):
        from random import seed, choice
        import forgery_py
        seed()
        names = []
        while len(names) < count:
            for i in range(count):
                name=forgery_py.internet.first_name()+' '+forgery_py.internet.first_name()
                names.append(name)
                if len(names) >= count:
                    break
        return names


    #Method for creating automatic user list
    #----------------------------------------------------------
    def generate_users(count=1):
        from sqlalchemy.exc import IntegrityError
        import random
        from random import seed, choice
        import forgery_py
        seed()

        users=[]
        while  len(users) < count:
            for i in range(count):
                u = User(name=forgery_py.internet.first_name()+' '+forgery_py.internet.first_name(),
                    email=forgery_py.internet.email_address(),
                    username=forgery_py.internet.user_name(True),
                    password='12345',
                    confirmed=True,
                    member_since=forgery_py.date.date(True))

                db.session.add(u)
                token=u.generate_confirmation_token()
                u.generate_referring_id()
                users.append(u)
                
                #Statement to get accurate amount of user to produce
                if len(users) == count:
                    break
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        return users
    #----------------------------------------------------------

    #Method to timestamp user walking flow (ping)
    #----------------------------------------------------------
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        self.make_new_message_delivered()
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
    #----------------------------------------------------------

    #This is the method to generate user profile picture url logically
    #----------------------------------------------------------
    def gravatar(self, size=100, default='identicon', rating='g', _external=False, **kwargs):
        if not self.profile_pix_url:
            if request.is_secure:
                url = 'https://secure.gravatar.com/avatar'
            else:
                url = 'http://www.gravatar.com/avatar'

            hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
            return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)
        elif _external and not 'http' in self.profile_pix_url:
            return url_for('static', filename=self.profile_pix_url.replace('/static/',''), _external=True)
        return self.profile_pix_url
    #----------------------------------------------------------

    #Method to generate accurate username suggestion
    #----------------------------------------------------------
    def suggest_valid_usernames_with(username, num=5):
        usernames=[]
        for n in range(num):
            count=0
            prod_name = username
            while User.query.filter_by(username=prod_name).first() or (prod_name in usernames):
                prod_name=username+str(count+1)
                count+=1
            usernames.append(prod_name)
        return usernames
    #-----------------------------------------------------------

    #Method to prepare User unique token
    #----------------------------------------------------------
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        s = s.dumps({'confirm': self.id})
        token = str(s)[2:-1]
        while User.query.filter_by(token=token).first():
            s = Serializer(current_app.config['SECRET_KEY'], expiration)
            s = s.dumps({'confirm': self.id})
            token = str(s)[2:-1]
        self.token = token
        return s


    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False

        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        db.session.add(self)
        return True
    #----------------------------------------------------------

    #   System information methods end
    #==========================================================

    #==========================================================
    #User information methods end
    #==========================================================


    #==========================================================
    #User Relationship methods
    #==========================================================
    def build_package(self, coupon_code):
        coupon = Coupon.query.filter_by(code=coupon_code).first()
        package = Package(coupon=coupon, user=self)
        db.session.add(package)
        coupon.used = True
        return package

    def add_badge_notification(self, name, data):
        #delete old notification and build a new one to meet the timeline
        self.badge_notifications.filter_by(name=name).delete()
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

        #Building a new one with the new data
        n = BadgeNotification(name=name, payload_json=json.dumps(data), user_id=self.id)
        try:
            db.session.add(n)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return n


    def add_notification(self, name, data):            
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        try:
            db.session.add(n)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        return n

    
    def new_notifications_count(self):
        return self.new_notifications.count()

    @property
    def new_notifications(self):
        last_read_time = self.last_notification_read_time or datetime(1900, 1, 1)
        return Notification.query.filter_by(user=self).filter(Notification.timestamp > last_read_time)

    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(receiver=self).filter(
            Message.timestamp > last_read_time).filter_by(read = False)

    def new_messages_count(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return self.new_messages().count()

    def new_messages_users_count(self):
        new_messages_query = self.new_messages()
        users=[]
        new_messages=new_messages_query.all()
        for msg in new_messages:
            if not msg.sender in users:
                users.append(msg.sender)
        return len(users)

    def make_new_message_delivered(self):
        for m in self.new_messages().filter_by(delivered=False).all():
            m.delivered = True
            db.session.add(m)
            db.session.commit()

    @property
    def messages(self):
        return self.messages_received.union(self.messages_sent)

    def return_messages_with(self, user):
        return self.messages_received.filter_by(sender=user).union(
            self.messages_sent.filter_by(receiver=user)).order_by(
            Message.timestamp.asc())

    #==========================================================
    #User Relationship methods end
    #==========================================================

    #Permission checking methods
    #----------------------------------------------------------
    def can(self, permissions):
        return self.role is not None and \
        (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def is_moderator(self):
        return self.can(Permission.MODERATE_COMMENTS)
    #----------------------------------------------------------

    #User walkflow status method
    def is_active(self):
        now = datetime.utcnow()
        year=now.year - self.last_seen.year
        month=now.month - self.last_seen.month
        day=now.day - self.last_seen.day
        hour=now.hour - self.last_seen.hour
        minute= now.minute - self.last_seen.minute
        seconds= now.second - self.last_seen.second

        return (not year and not month and not day and not hour and minute <= 1 )

    #Model Garbaging
    def delete(self):
        #delete all user related model

        for p in self.packages.all():
            p.delete()

        for n in self.notifications.all():
            n.delete()

        for bn in self.badge_notifications.all():
            bn.delete()

        for m in self.messages.all():
            m.delete()
        db.session.delete(self)

    def __repr__(self):
        return '<User %r>' % self.username
db.event.listen(User.email, 'set', User.on_changed_email)
db.event.listen(User.welcome_msg, 'set', User.on_changed_welcome_msg)
db.event.listen(User.restriction_message, 'set', User.on_changed_restriction_message)

#AnonymousUser Model
#==============================================
class AnonymousUser(AnonymousUserMixin):
    profile_pix_url=None
    email='anonymous_user@gmail.com'
    avatar_hash=None
    celebrity = None
    fan_card = None
    referral = None
    def can(self, permissions):
        return False

    def has_active_package(self):
        False

    def is_administrator(self):
        return False

    def is_active(self):
        return False

    def is_connected_with(self, user):
        return False

    @property
    def name(self):
        return 'AnonymousUser'

    @property
    def username(self):
        return 'AnonymousUser'

    def is_following(self,user):
        return False

    @property
    def followed_posts(self):
        return Post.query

    def get_referring_id(self):
        '''it is suppose to be load from cookies'''
        return ''

    def get_mutual_followed_with(self,user):
        return []

    #This is the method to generate user profile picture url logically
    #----------------------------------------------------------
    def gravatar(self, size=100, default='identicon', rating='g', **kwargs):
        return ''
    #----------------------------------------------------------

    #Method for creating automatic names
    #----------------------------------------------------------
    def generate_names(self, count=1):
        from random import seed, choice
        import forgery_py
        seed()
        names = []
        while len(names) < count:
            for i in range(count):
                name=forgery_py.internet.first_name()+' '+forgery_py.internet.first_name()
                names.append(name)
                if len(names) >= count:
                    break
        return names

login_manager.anonymous_user = AnonymousUser
