from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    BooleanField,
    SelectMultipleField,
    SubmitField,
)
from wtforms.validators import DataRequired


class NewsForm(FlaskForm):
    title = StringField("Заголовок", validators=[DataRequired()])
    content = TextAreaField("Содержание", validators=[DataRequired()])
    is_private = BooleanField("Только для меня")
    categories = SelectMultipleField("Категории", coerce=int)
    submit = SubmitField("Сохранить")
