import os.path
import time

import werkzeug.utils
from flask import flash, render_template, url_for, redirect, request, session, abort, g, send_from_directory
from app import app
from database import Database
from hashlib import sha256
from werkzeug.utils import secure_filename

EXTENSION = {'png', 'jpg', 'jpeg', 'bmp'}


def save_tuple(obj, key):
    if key in obj:
        return obj[key]
    else:
        return None


@app.route('/')
def base():
    return redirect(url_for("index"))


@app.route('/index')
def index():
    db = Database()
    return render_template("index.html", title="Главная страница", menu_data=db.get_menu(),
                           menu_category=save_tuple(session, "group"))


@app.route("/account", methods=["GET", "POST"])
def account():
    db = Database()
    if "user" in session:
        if db.verify_user(session["user"], session["session_key"]):
            if request.method == "POST":
                if "id" in request.form:
                    db.safe_delete_from_bucket(session["user"], request.form['id'])
                elif "address" in request.form:
                    db.send_to_order(session["user"], request.form["address"])

            # все нормально
            yourgroup = "Пользователь" if session["group"] == "user" else "Администратор"
            items = db.get_bucket(session["user"])
            return render_template("account.html", username=session["user"], menu_data=db.get_menu(),
                                   date=db.get_registration_time(session["user"])["register_date"],
                                   menu_category=save_tuple(session, "group"), group=yourgroup, count_items=len(items),
                                   bucket=items)
        abort(401)


@app.route("/register", methods=["GET", "POST"])
def register():
    db = Database()
    if request.method == "POST":
        if db.register(request.form["username"]):
            res = db.add_user(request.form["username"], request.form["password"])
            session["user"] = request.form["username"]
            session["session_key"] = sha256(
                bytes(request.form["username"] + request.form["password"], encoding="utf-8")).hexdigest()
            session["group"] = db.get_group(request.form["username"])
            if not res:
                flash("Возникла непредвиденная ошибка", category="error")
        else:
            flash("Такой пользователь уже существует!", category="error")
    if "user" in session:
        if session["user"]:
            return redirect(url_for("index"))
    return render_template("register.html", title="Регистрация", menu_data=db.get_menu())


@app.route("/login", methods=["GET", "POST"])
def login():
    db = Database()
    if "user" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        # логин
        if db.login(request.form["username"], request.form["password"]):
            test_hash = db.get_hash(request.form["username"])
            if test_hash != None:
                session["user"] = request.form["username"]
                session["session_key"] = test_hash
                session["group"] = db.get_group(request.form["username"])
                return redirect(url_for("index"))
            else:
                flash("Возникла внезапная ошибка")
    return render_template("login.html", title="Логин", menu_data=db.get_menu())


@app.route("/shop", methods=["GET", "POST"])
def shop():
    db = Database()
    if request.method == "POST" and "user" in session:
        if "item-id" in request.form:
            if db.verify_user(session["user"], session["session_key"]):
                res = db.add_purchase(session["user"], request.form["item-id"])
                if res:
                    flash("Товар добавлен в корзину. Более подробную информацию вы можете посмотреть перейдя в аккаунт",
                          category="success")
                else:
                    flash("Возникла ошибка", category="error")
        elif "delete-id" in request.form:
            res = db.remove_stuff(request.form["delete-id"])
            if res:
                flash("Товар удален. Удачи в администрировании")
            else:
                flash("Возникла ошибка", category="error")
    elif "user" not in session:
        flash("Для того чтобы в полную меру использовать эту страницу вам необходимо зарегистрироваться",
              category="error")
    return render_template("shop.html", title="Магазин", menu_data=db.get_menu(), items=db.get_stuff(0),
                           menu_category=save_tuple(session, "group"))


@app.route("/complaints", methods=["GET", "POST"])
def complaints():
    db = Database()
    if request.method == "POST":
        if "user" in session:
            if db.verify_user(session["user"], session["session_key"]):
                # все нормально
                res = db.add_complaint(request.form["title"], request.form["content"], session["user"])
                if res:
                    flash("отзыв успешно добавлен", category="success")
                else:
                    flash("Возникла ошибка при добавлении отзыва", category="error")
        else:
            flash("Пользователь не авторизован", category="error")
    return render_template("create_complaint.html", title="Добавить отзыв", menu_data=db.get_menu(),
                           menu_category=save_tuple(session, "group"))


@app.route("/view_complaints", methods=["GET", "POST"])
def view():
    db = Database()
    if "user" in session and request.method == "POST":
        if db.verify_admin(session["user"], session["session_key"]):
            db.remove_complaint(request.form["id"])

    return render_template("view.html", complaints=db.get_complaints(), title="Отзывы", menu_data=db.get_menu(),
                           menu_category=save_tuple(session, "group"))


@app.route("/create", methods=["GET", "POST"])
def create():
    db = Database()
    if "user" in session:
        if db.verify_admin(session["user"], session["session_key"]):
            if request.method == "POST":
                # проверка на плохие вещи
                if len(request.form["title"]) > 3 and len(request.form["description"]) > 5:
                    print(request.files)
                    if "file" in request.files:
                        print("file herer")
                        f = request.files['file']
                        if f.filename.split(".")[-1] in EXTENSION and "image" in f.mimetype:
                            filename = str(time.time()).replace(".", "_") + "." + f.filename.split(".")[-1]
                            print(os.path.join(app.config["DOWNLOADS"], filename))
                            f.save(os.path.join(app.config["DOWNLOADS"], filename))

                            res = db.add_stuff(request.form["title"], request.form["description"], filename,
                                               request.form["price"])
                            if not res:
                                flash("Возникла ошибка при обработке вашего запроса на сервере", category="error")
                            else:
                                flash("Успех", category="success")
                else:
                    flash("Слишком короткий заголовок или описание")
            return render_template("create.html", title="Новый товар", menu_data=db.get_menu(),
                                   menu_category=save_tuple(session, "group"))
    abort(401)


@app.route("/logout")
def logout():
    # выход из аккаунта, путем очистки переменной сессии
    session.clear()
    return redirect(url_for("index"))


@app.route("/downloads/<filename>")
def get_file(filename):
    return send_from_directory(app.config["DOWNLOADS"], filename)


@app.route("/static/images/<filename>")
def get_image(filename):
    return send_from_directory("static/images/", filename)


@app.errorhandler(404)
def pagenotfound(error):
    # обработик ошибки 404
    db = Database()
    return render_template("404.html", title="Страница не найдена", menu_data=db.get_menu(),
                           menu_category=save_tuple(session, "group"))


@app.errorhandler(401)
def autherror(error):
    # обработик ошибки 401
    db = Database()
    return render_template("401.html", title="Ошибка 401", menu_data=db.get_menu(),
                           menu_category=save_tuple(session, "group"))
