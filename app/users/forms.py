from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, FormField, FieldList, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from wtforms.fields.html5 import DateField
from flask import request
from flask_babel import lazy_gettext as _l


class UpdateTriggerForm(FlaskForm):
  shaving = IntegerField('How many cans of shaving foam do you use in a month?', validators=[DataRequired()])
  t_hold = IntegerField(validators=[NumberRange(min=0, max=100, message="Must be a number between 0 and 100 G")])
  friend = IntegerField()
  id = IntegerField('iden')
  submit = SubmitField('Update')

class TriggersForm(FlaskForm):
    triggers = FieldList(FormField(UpdateTriggerForm), min_entries=1)





class registrationForm(FlaskForm):
  username = StringField(_l('Username'), 
                          validators=[DataRequired(), 
                          Length(min=2, max = 20)])

  email = StringField('Email', 
                      validators = [DataRequired(), Email()])
  
  password = PasswordField(_l('Password'), validators=[DataRequired()])
  confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

  submit = SubmitField('Sign Up')

  def validate_username(self, username):
    user = User.query.filter_by(username=username.data).first()
    if user:
      raise ValidationError('bruh, This user already exists')
  
  def validate_email(self, email):
    user = User.query.filter_by(email=email.data).first()
    if user:
      raise ValidationError('bruh, This email has already been registered')



class loginForm(FlaskForm):
  email = StringField('Email', 
                      validators = [DataRequired(), Email()])
  remember = BooleanField('Remember Me')
  password = PasswordField('Password', validators=[DataRequired()])
  submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
  username = StringField('Username', 
                          validators=[DataRequired(), 
                          Length(min=2, max = 20)])

  email = StringField('Email', 
                      validators = [DataRequired(), Email()])
  
  picture = FileField('Update Profile Picture', validators = [FileAllowed(['jpg', 'png'])])
  

  submit = SubmitField('Update')

  def validate_username(self, username):
    if username.data != current_user.username:
      user = User.query.filter_by(username=username.data).first()
      if user:
        raise ValidationError('bruh, This user already exists')
    
  def validate_email(self, email):
    if email.data != current_user.email:
      user = User.query.filter_by(email=email.data).first()
      if user:
        raise ValidationError('bruh, This email has already been registered')

class RequestResetForm(FlaskForm):
  email = StringField('Email', 
                      validators = [DataRequired(), Email()])
  submit = SubmitField('Request Password Reset')

  def validate_email(self, email):
    user = User.query.filter_by(email=email.data).first()
    if user is None:
      raise ValidationError('bruh, No account with this email G...register your balls')

class ResetPasswordForm(FlaskForm):
  password = PasswordField('Password', validators=[DataRequired()])
  confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
  
  submit = SubmitField('Reset Password')

class TodoForm(FlaskForm):
  complete = BooleanField('Complete?')
  text = StringField("Enter your to do item here")
  date_due = DateField('DatePicker')
  submit = SubmitField('Submit')
  iden = IntegerField('iden')

class TodosForm(FlaskForm):
    todos = FieldList(FormField(TodoForm), min_entries=1)
    new_todo = FieldList(FormField(TodoForm), min_entries=1)

class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)

class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))