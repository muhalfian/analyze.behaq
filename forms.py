import wtforms
from wtforms import validators
from models import User

class LoginForm(wtforms.Form):
    email = wtforms.StringField("Email",
    validators=[validators.DataRequired()])
    password = wtforms.PasswordField("Password", validators=[validators.DataRequired()])
    remember_me = wtforms.BooleanField("Remember me?", default=True)

    def validate(self):
        # if not super(LoginForm, self).validate():
        #     return False
        
        self.user = User.authenticate(self.email.data, self.password.data)
        if not self.user:
            self.email.errors.append("Invalid email or password.")
            return False
        return True

class SearchForm(wtforms.Form):
    q = wtforms.StringField("Keyword", validators=[validators.DataRequired()])
    
    def validate(self):
        # if not super(LoginForm, self).validate():
        #     return False
        
        self.user = User.authenticate(self.email.data, self.password.data)  
        if not self.user:
            self.email.errors.append("Invalid email or password.")
            return False
        return True