# Главный файл приложения app.py
from flask import Flask, render_template, redirect, url_for, request, abort, flash
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from data import db_session
from data.news import News
from data.category import Category
from data.users import User
from forms.news_form import NewsForm
from forms.category_form import CategoryForm
from forms.register_form import RegisterForm
from forms.login_form import LoginForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    from data.users import User

    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route("/logout")
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    return redirect(url_for("news_list"))


@app.route("/")
@app.route("/news")
def news_list():
    """Все новости"""
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_private == False).all()
    return render_template("news_list.html", news_list=news)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Регистрация нового пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for("news_list"))

    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        # Проверка, что email уникален
        if db_sess.query(User).filter(User.email == form.email.data).first():
            flash("Такой email уже зарегистрирован", "danger")
            return render_template("register.html", form=form, title="Регистрация")

        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        # После успешной регистрации сразу авторизуем пользователя
        login_user(user)
        return redirect(url_for("news_list"))

    return render_template("register.html", form=form, title="Регистрация")


@app.route("/news/<int:news_id>")
def news_detail(news_id):
    """Одна новость"""
    db_sess = db_session.create_session()
    news = db_sess.get(News, news_id)
    if not news:
        abort(404)
    return render_template("news_detail.html", news=news)


@app.route("/news/add", methods=["GET", "POST"])
@login_required
def add_news():
    """Добавление новости"""
    db_sess = db_session.create_session()
    form = NewsForm()
    form.categories.choices = [(c.id, c.name) for c in db_sess.query(Category).all()]

    if form.validate_on_submit():
        news = News(
            title=form.title.data,
            content=form.content.data,
            is_private=form.is_private.data,
            user=current_user,
        )
        for cat_id in form.categories.data:
            category = db_sess.get(Category, cat_id)
            news.categories.append(category)
        db_sess.add(news)
        db_sess.commit()
        return redirect(url_for("news_list"))

    return render_template("news_form.html", form=form, title="Добавить новость")


@app.route("/news/edit/<int:news_id>", methods=["GET", "POST"])
@login_required
def edit_news(news_id):
    """Редактирование новости"""
    db_sess = db_session.create_session()
    news = db_sess.get(News, news_id)
    if not news or news.user != current_user:
        abort(404)

    form = NewsForm()
    form.categories.choices = [(c.id, c.name) for c in db_sess.query(Category).all()]

    if request.method == "GET":
        form.title.data = news.title
        form.content.data = news.content
        form.is_private.data = news.is_private
        form.categories.data = [c.id for c in news.categories]

    if form.validate_on_submit():
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        news.categories = [db_sess.get(Category, cid) for cid in form.categories.data]
        db_sess.commit()
        return redirect(url_for("news_list"))

    return render_template("news_form.html", form=form, title="Редактировать новость")


@app.route("/news/delete/<int:news_id>", methods=["POST"])
@login_required
def delete_news(news_id):
    """Удаление новости"""
    db_sess = db_session.create_session()
    news = db_sess.get(News, news_id)
    if not news or news.user != current_user:
        abort(404)
    db_sess.delete(news)
    db_sess.commit()
    return redirect(url_for("news_list"))


# --- Категории (админка) ---


@app.route("/categories")
@login_required
def category_list():
    """Список всех категорий"""
    db_sess = db_session.create_session()
    categories = db_sess.query(Category).all()
    return render_template("category_list.html", categories=categories)


@app.route("/categories/add", methods=["GET", "POST"])
@login_required
def add_category():
    """Добавление категории"""
    form = CategoryForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        category = Category(name=form.name.data)
        db_sess.add(category)
        db_sess.commit()
        return redirect(url_for("category_list"))
    return render_template("category_form.html", form=form, title="Добавить категорию")


@app.route("/categories/edit/<int:cat_id>", methods=["GET", "POST"])
@login_required
def edit_category(cat_id):
    """Редактирование категории"""
    db_sess = db_session.create_session()
    category = db_sess.get(Category, cat_id)
    if not category:
        abort(404)

    form = CategoryForm()
    if request.method == "GET":
        form.name.data = category.name

    if form.validate_on_submit():
        category.name = form.name.data
        db_sess.commit()
        return redirect(url_for("category_list"))

    return render_template(
        "category_form.html", form=form, title="Редактировать категорию"
    )


@app.route("/categories/delete/<int:cat_id>", methods=["POST"])
@login_required
def delete_category(cat_id):
    """Удаление категории"""
    db_sess = db_session.create_session()
    category = db_sess.get(Category, cat_id)
    if not category:
        abort(404)
    db_sess.delete(category)
    db_sess.commit()
    return redirect(url_for("category_list"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Авторизация пользователя"""
    if current_user.is_authenticated:
        return redirect(url_for("news_list"))

    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(request.args.get("next") or url_for("news_list"))
        flash("Неверный логин или пароль", "danger")

    return render_template("login.html", form=form, title="Вход")


if __name__ == "__main__":
    # Подключаем БД
    db_session.global_init("db/blog.db")
    app.run(host="localhost", port=5000, debug=False)
    
