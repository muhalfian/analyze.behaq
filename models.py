import datetime, re, hashlib, urllib
import http.client, urllib.request, urllib.parse, urllib.error, base64

from app import db, login_manager, bcrypt

@login_manager.user_loader
def _user_loader(user_id):
    return User.query.get(int(user_id))

def slugify(s):
    return re.sub('[^\w]+', '-', s).lower()

entry_tags = db.Table('entry_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('entry_id', db.Integer, db.ForeignKey('entry.id'))
)

class User(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True)
    password_hash = db.Column(db.String(255))
    name = db.Column(db.String(64), default='')
    slug = db.Column(db.String(64), unique=True, default='')
    active = db.Column(db.Boolean, default=True)
    admin = db.Column(db.Boolean, default=False)
    feedback = db.relationship('Feedback', backref='author', lazy='dynamic')
    created_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    
    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.generate_slug()
    
    def is_admin(self):
        return self.admin

    def generate_slug(self):
        if self.name:
            self.slug = slugify(self.name)

    # Flask-Login interface..
    def get_id(self):
        return str(self.id)

    def is_authenticated(self):
        return True
    
    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    @staticmethod
    def make_password(plaintext):
        password_hash = bcrypt.generate_password_hash(plaintext).decode('utf-8')
        return password_hash
    
    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)
    
    @classmethod
    def create(cls, email, password, **kwargs):
        return User(
            email=email,
            password_hash=User.make_password(password),
            **kwargs)

    @staticmethod
    def authenticate(email, password):
        users = User.query.filter(User.email == email).first()
        if users and users.check_password(password):
            return users
        return False

class hoax_training_set(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(255), unique=True)
    value = db.Column(db.Integer, default=0)
    created_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)

class ham_training_set(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(255), unique=True)
    value = db.Column(db.Integer, default=0)
    created_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)

class Feedback(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), default=0)
    status = db.Column(db.Integer, default=0)
    vote = db.Column(db.Integer, default=0)
    reason = db.Column(db.Text, default='')
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    ip_address = db.Column(db.Text, default=0)
    created_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)

class ow_base_user(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), default=0)
    username = db.Column(db.String(32), default=0)
    password = db.Column(db.String(64), default=0)

class Stopwords(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(100), unique=True)

class ham_count(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    qty = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), default=1)
    created_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)

class hoax_count(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    qty = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), default=1)
    created_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)

# class Entry(db.Model):
#     STATUS_PUBLIC = 0
#     STATUS_DRAFT = 1
#     STATUS_DELETED = 2

#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100))
#     slug = db.Column(db.String, unique=True)
#     body = db.Column(db.Text)
#     status = db.Column(db.SmallInteger, default=STATUS_PUBLIC)
#     create_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
#     modified_timestamp = db.Column(
#         db.DateTime,
#         default = datetime.datetime.now,
#         onupdate = datetime.datetime.now)
#     author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
#     tags = db.relationship('Tag', secondary=entry_tags, backref=db.backref('entries', lazy='dynamic'))
#     comments = db.relationship('Comment', backref='entry', lazy='dynamic')

#     def __init__(self, *args, **kwargs):
#         super(Entry, self).__init__(*args, **kwargs)
#         self.generate_slug()
    
#     def generate_slug(self):
#         self.slug = ''
#         if self.title:
#             self.slug = slugify(self.title)
    
#     def __repr__(self):
#         return '<Entry : %s>' % self.title

#     @property
#     def tag_list(self):
#         return ', '.join(tag.name for tag in self.tags)

#     @property
#     def tease(self):
#         return self.body[:100]

# class Tag(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64))
#     slug = db.Column(db.String(64), unique=True)
    
#     def __init__(self, *args, **kwargs):
#         super(Tag, self).__init__(*args, **kwargs)
#         self.slug = slugify(self.name)

#     def __repr__(self):
#         return '<Tag %s>' % self.name

# class User(db.Model):
    
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(64), unique=True)
#     password_hash = db.Column(db.String(255))
#     name = db.Column(db.String(64))
#     slug = db.Column(db.String(64), unique=True)
#     active = db.Column(db.Boolean, default=True)
#     admin = db.Column(db.Boolean, default=False)
#     created_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
#     entries = db.relationship('Entry', backref='author', lazy='dynamic')
    
#     def __init__(self, *args, **kwargs):
#         super(User, self).__init__(*args, **kwargs)
#         self.generate_slug()
    
#     def is_admin(self):
#         return self.admin

#     def generate_slug(self):
#         if self.name:
#             self.slug = slugify(self.name)

#     # Flask-Login interface..
#     def get_id(self):
#         return str(self.id)

#     def is_authenticated(self):
#         return True
    
#     def is_active(self):
#         return self.active

#     def is_anonymous(self):
#         return False

#     @staticmethod
#     def make_password(plaintext):
#         password_hash = bcrypt.generate_password_hash(plaintext).decode('utf-8')
#         return password_hash
    
#     def check_password(self, raw_password):
#         return bcrypt.check_password_hash(self.password_hash, raw_password)
    
#     @classmethod
#     def create(cls, email, password, **kwargs):
#         return User(
#             email=email,
#             password_hash=User.make_password(password),
#             **kwargs)

#     @staticmethod
#     def authenticate(email, password):
#         users = User.query.filter(User.email == email).first()
#         if users and users.check_password(password):
#             return users
#         return False

# class Comment(db.Model):
#     STATUS_PENDING_MODERATION = 0
#     STATUS_PUBLIC = 1
#     STATUS_SPAM = 8
#     STATUS_DELETED = 9
    
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64))
#     email = db.Column(db.String(64))
#     url = db.Column(db.String(100))
#     ip_address = db.Column(db.String(64))
#     body = db.Column(db.Text)
#     status = db.Column(db.SmallInteger, default=STATUS_PUBLIC)
#     created_timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
#     entry_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    
#     def __repr__(self):
#         return '<Comment from %r>' % (self.name,)

#     def gravatar(self, size=75):
#         return 'http://www.gravatar.com/avatar.php?%s' % urllib.parse.urlencode({
#             'gravatar_id': hashlib.md5(self.email.encode('utf-8')).hexdigest(),
#             'size': str(size)})


#     class SearchImage(db.Model):
#         id = db.Column(db.Integer, primary_key=True)
#         keyword = db.Column(db.String(100))
#         name = db.Column(db.String(150))
#         dataPublished = db.Column(db.DateTime, default=datetime.datetime.now)
#         contentSize = db.Column(db.Integer)
#         thumbnailUrl = db.Column(db.String)
#         contentUrls = db.Column(db.String)
#         encodingFormat = db.Column(db.String(20))
        
#         def __repr__(self):
#             return '<Image From from %r>' % (self.name,)

#         def gravatar(self, size=75):
#             return 'http://www.gravatar.com/avatar.php?%s' % urllib.parse.urlencode({
#                 'gravatar_id': hashlib.md5(self.email.encode('utf-8')).hexdigest(),
#                 'size': str(size)})