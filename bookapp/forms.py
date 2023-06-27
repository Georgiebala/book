from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,TextAreaField,PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo

from flask_wtf.file import FileField,FileAllowed, FileRequired


class SignupForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired(message="Hello, your fullname is required")])

    email = StringField("Your Email",validators=[Email()])

    password=PasswordField("password",validators=[DataRequired()])

    confirm_password= PasswordField("confirm password",validators=[EqualTo('password',message="Confirm Password must be equal to password")])
    
    btn = SubmitField("Sign up")



class ProfileForm(FlaskForm):
    fullname = StringField("Fullname",validators=[DataRequired(message="Hello, your fullname is required")])
    pix = FileField('display picture',validators=[FileRequired(),FileAllowed(['jpg','png'],'Images only!')])
    btn = SubmitField(" Update Profile ")
    
 
  
    
    
    
    
    
     
    

