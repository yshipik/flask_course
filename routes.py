from flask import flash, render_template, url_for, redirect, request, session, abort,  g
from app import app
from database import Database
from hashlib import sha256

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

@app.route("/account")
def account():
    db = Database()
    if "user" in session:
        if db.verify_user(session["user"], session["session_key"]):
            # все нормально
            yourgroup = "Пользователь" if session["group"] == "user" else "Администратор"
            items = db.get_bucket(session["user"])
            return render_template("account.html", username=session["user"], menu_data=db.get_menu(), menu_category=save_tuple(session, "group"),  group=yourgroup, count_items=len(items), bucket=items)
        abort(401)
@app.route("/register", methods=["GET", "POST"])
def register():
    db = Database()
    if request.method == "POST":
        if db.register(request.form["username"]):
            res = db.add_user(request.form["username"], request.form["password"])
            session["user"] = request.form["username"]
            session["session_key"] = sha256( bytes(request.form["username"] + request.form["password"], encoding="utf-8") ).hexdigest()
            session["group"] = db.get_group(request.form["username"])
            if not res:
                flash("Возникла непредвиденная ошибка", category="error")
            else:
                flash("Вы успешно зарегистрировались вернитесь на главную")
        else:
            flash("Такой пользователь уже существует!", category="error")
    if session["user"]:
        return redirect(url_for("index"))
    return render_template("register.html", title="Регистрация", menu_data = db.get_menu())
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
    return render_template("login.html", title="Логин", menu_data = db.get_menu())
@app.route("/shop", methods=["GET", "POST"])
def shop():
    db = Database()
    if request.method == "POST" and "user" in session:
        if db.verify_user(session["user"], session["session_key"]):
            res = db.add_purchase(session["user"], request.form["item-id"])
            if res:
                flash("Товар добавлен в корзину. Более подробную информацию вы можете посмотреть перейдя в аккаунт", category="success")
            else:
                flash("Возникла ошибка", category="error")
    elif "user" not in session:
        flash("Для того чтобы использовать эту опцию вам необходимо зарегистрироваться", category="error")
    return  render_template("shop.html", title="Магазин", menu_data=db.get_menu(), items=db.get_stuff(0), menu_category=save_tuple(session, "group"))
@app.route("/complaints", methods=["GET", "POST"])
def complaints():
    db = Database()
    if request.method == "POST":
        if "user" in session:
            if db.verify_user(session["user"], session["session_key"]):
                # все нормально
                res = db.add_complaint(request.form["title"], request.form["content"], session["user"])
                if res: flash("Жалобы успешно добавлена", category="success")
                else:
                    flash("Возникла ошибка при добавлении жалобы", category="error")
        else:
            flash("Пользователь не авторизован", category="error")
    return render_template("create_complaint.html", title="Добавить жалобу", menu_data = db.get_menu(), menu_category=save_tuple(session, "group"))
@app.route("/view_complaints")
def view():
    db = Database()
    return render_template("view.html", complaints=db.get_complaints() ,title="Жалобы", menu_data=db.get_menu(), menu_category=save_tuple(session, "group"))
@app.route("/create", methods=["GET", "POST"])
def create():
    db = Database()
    if "user" in session:
        if db.verify_admin(session["user"], session["session_key"]):
            if request.method == "POST":
                # проверка на плохие вещи
                if len(request.form["title"]) > 3 and len(request.form["description"]) > 5:
                    res = db.add_stuff(request.form["title"], request.form["description"], request.form["picture"], request.form["price"])
                    if not res:
                        flash("Возникла ошибка при обработке вашего запроса на сервере", category="error")
                    else:
                        flash("Успех", category="success")
                else:
                    flash("Слишком короткий заголовок или описание")
            return render_template("create.html", title="Новый товар", menu_data=db.get_menu(), menu_category=save_tuple(session, "group"))
    abort(401)
@app.errorhandler(404)
def pagenotfound(error):
    db = Database()
    return render_template("404.html", title="Страница не найдена", menu_data=db.get_menu(), menu_category=save_tuple(session, "group"))
@app.errorhandler(401)
def autherror(error):
    return render_template("401.html", title="Ошибка 401", menu_data=db.get_menu(), menu_category=save_tuple(session, "group"))