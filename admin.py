from flask import g, url_for, redirect, request
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.fileadmin import FileAdmin
from wtforms.fields import SelectField, PasswordField
from app import app, db
from models import User, Feedback, hoax_training_set, hoax_count, ham_training_set, ham_count, Stopwords, Feedback
from TrainingSetsUtil import make_training_set

class AdminAuthentication(object):
    def is_accessible(self):
        return g.user.is_authenticated and g.user.is_admin()
    
class IndexView(AdminIndexView):
    @expose('/')
    def index(self):
        # print(g.user.is_authenticated, g.user.is_admin)
        if not (g.user.is_authenticated and g.user.is_admin()):
            return redirect(url_for('login', next=request.path))
        return self.render('admin/index.html')

class BlogFileAdmin(AdminAuthentication, FileAdmin):
    pass

class BaseModelView(AdminAuthentication, ModelView):
    pass

class SlugModelView(BaseModelView):
    def on_model_change(self, form, model, is_created):
        model.generate_slug()
        return super(SlugModelView, self).on_model_change(form, model, is_created)


class UserModelView(ModelView):
    column_filters = ('email', 'name', 'admin', 'active')
    column_list = ['email', 'name', 'active', 'admin', 'created_timestamp']
    column_searchable_list = ['email', 'name']
    
    form_columns = ['email', 'password', 'name', 'active', 'admin']
    form_extra_fields = {
        'password': PasswordField('New password'),
    }

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password_hash = User.make_password(form.password.data)
        return super(UserModelView, self).on_model_change(form, model, is_created)

class FeedbackModelView(ModelView):
    column_filters = ('url', 'vote', 'status', 'reason', 'user_id', 'ip_address', 'created_timestamp')
    column_list = ['url', 'vote', 'status', 'reason', 'user_id', 'ip_address', 'created_timestamp']
    column_searchable_list = ['url', 'status', 'user_id']
    
    form_columns = ['url', 'vote', 'status', 'reason', 'user_id']

    def on_model_change(self, form, model, is_created):   
        if(form.status.data == 1):
            check = Feedback.query.filter_by(url=form.url.data, status=1).first()
            
            if(form.vote.data == 1):
                make_training_set(form.url.data, "ham")
                if check==None:
                    hasil = ham_count(qty=1)
                    db.session.add(hasil)
            elif(form.vote.data == 0):
                make_training_set(form.url.data, "hoax")
                if check==None:
                    hasil = hoax_count(qty=1)
                    db.session.add(hasil)
            db.session.commit()
            print(form.url.data)
            # model.password_hash = User.make_password(form.password.data)
            return super(FeedbackModelView, self).on_model_change(form, model, is_created)

class HamTrainingModelView(ModelView):
    column_filters = ('term', 'value', 'created_timestamp')
    column_list = ['term', 'value', 'created_timestamp']
    column_searchable_list = ['term', 'value', 'created_timestamp']
    form_columns = ['term', 'value', 'created_timestamp']

class HoaxTrainingModelView(ModelView):
    column_filters = ('term', 'value', 'created_timestamp')
    column_list = ['term', 'value', 'created_timestamp']
    column_searchable_list = ['term', 'value', 'created_timestamp']
    form_columns = ['term', 'value', 'created_timestamp']

class HamCountModelView(ModelView):
    column_filters = ('qty', 'created_timestamp', 'user_id')
    column_list = ['qty', 'created_timestamp', 'user_id']
    column_searchable_list = ['qty', 'created_timestamp', 'user_id']
    form_columns = ['qty', 'created_timestamp', 'user_id']

class HoaxCountModelView(ModelView):
    column_filters = ('qty', 'created_timestamp', 'user_id')
    column_list = ['qty', 'created_timestamp', 'user_id']
    column_searchable_list = ['qty', 'created_timestamp', 'user_id']
    form_columns = ['qty', 'created_timestamp', 'user_id']

class StopwordsModelView(ModelView):
    column_filters = ('id','term')
    column_list = ['id','term']
    column_searchable_list = ['id','term']
    form_columns = ['id','term']

    
admin = Admin(app, 'Blog Admin', index_view=IndexView())
# admin.add_view(EntryModelView(Entry, db.session))
admin.add_view(FeedbackModelView(Feedback, db.session))
admin.add_view(HoaxTrainingModelView(hoax_training_set, db.session))
admin.add_view(HamTrainingModelView(ham_training_set, db.session))
admin.add_view(HamCountModelView(ham_count, db.session))
admin.add_view(HoaxCountModelView(hoax_count, db.session))
admin.add_view(StopwordsModelView(Stopwords, db.session))
admin.add_view(UserModelView(User, db.session))
admin.add_view(BlogFileAdmin(app.config['STATIC_DIR'], '/static/', name='StaticFiles'))