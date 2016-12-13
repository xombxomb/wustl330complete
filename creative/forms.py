from flask_wtf import Form
from wtforms import StringField, HiddenField
from wtforms.validators import DataRequired

class MessageForm(Form):
    number = StringField('number', validators=[DataRequired()])
    media = StringField('media')
