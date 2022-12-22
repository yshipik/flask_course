import sqlite3, os, datetime
from hashlib import sha256

from app import app


class Database:
    _conn: sqlite3.Connection
    _cursor: sqlite3.Cursor
    __PAGE_SIZE = 15

    def __init__(self, file=""):
        # конструктор класса Базы данных
        if not file:
            # создание соединения с бд
            self._conn = sqlite3.connect(app.config['DATABASE'])
        else:
            self._conn = sqlite3.connect(file)
        self._conn.row_factory = sqlite3.Row
        # создание курсора базы данных
        self._cursor = self._conn.cursor()

    def state_db_function(errormessage):
        # декоратор для функций, которые не возвращают результаты из бд
        def wrap(fn):
            def wrapper(*args, **kwargs):
                try:
                    fn(*args, **kwargs)
                    return True
                except sqlite3.Error as e:
                    print(errormessage, str(e))
                return False
            return wrapper

        return wrap
    @state_db_function("Ошибка при добавлении пункта в меню")
    def add_menu(self, name: str, url: str, category: str):
        # добавление пункта в меню
        self._cursor.execute("insert into menu values (NULL, ?, ?, ?)", (name, url, category))
        self._conn.commit()
    def add_user(self, username: str, password: str, is_stuff=False):
        # получение текущего времени
        tm = datetime.datetime.now()
        # получение хэша пароля
        realpass = sha256(bytes(password, encoding="utf-8")).hexdigest()
        try:
            # добавление пользователя
            self._cursor.execute("insert into users values (NULL, ?, ?, ?, ?)", (username, realpass, tm, is_stuff))
            self._conn.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления пользователя в БД: " + str(e))
            return False
        return True

    def get_menu(self):
        '''Получение списка меню'''
        try:
            self._cursor.execute("select * from menu")
            res = self._cursor.fetchall()
            if res: return res
        except sqlite3.Error as e:
            print("Ошибка получения информации в бд", str(e))
        return []

    def login(self, username: str, password: str):
        '''Проверяет, существует ли пользователь с таким именем и паролем'''
        realpass = sha256(bytes(password, encoding="utf-8")).hexdigest()
        try:
            self._cursor.execute("select * from users where username = ? and password = ?", (username, realpass))
            res = self._cursor.fetchone()
            if res: return True
        except sqlite3.Error as e:
            print("Ошибка базы данных", str(e))
        return False

    def register(self, username: str):
        '''Проверяет есть ли пользователь в базе данных, чтобы не было одинаковых имен пользователей'''
        try:
            self._cursor.execute("select * from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res: return False
        except sqlite3.Error as e:
            print("Ошибка базы данных при регистрации нового пользователя " + str(e))
        return True

    def get_hash(self, username: str):
        '''Получение хэша пользователя для дополнительной безопасности'''
        try:
            self._cursor.execute("select * from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res:
                hash = sha256(bytes(res["username"] + res["password"], encoding="utf-8")).hexdigest()
                return hash
        except sqlite3.Error as e:
            print("Ошибка при получении хэша пользователя")
        return None

    def get_group(self, username: str):
        '''Получаем информацию о том, в какую группу входит пользователь, обычных или привилегированных'''
        try:
            self._cursor.execute("select * from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res:
                if res["is_stuff"] == 1:
                    return "admin"
                else:
                    return "user"
        except sqlite3.Error as e:
            print("Ошибка при получении ")
        return "unlogged"

    def verify_admin(self, username: str, hash: str):
        '''Проверям что данный пользователь является администратором'''
        try:
            self._cursor.execute("select * from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res:
                if res["is_stuff"] == 1 and sha256(
                        bytes(res["username"] + res["password"], encoding="utf-8")).hexdigest() == hash:
                    return True
                else:
                    return False
        except sqlite3.Error as e:
            print("Произошла ошибка при верификации пользователя" + str(e))
        return False

    def verify_user(self, username: str, hash: str):
        '''Дополнительная мера проверки безопасности, на случай если был раскрыт секретный ключ'''
        try:
            self._cursor.execute("select * from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res:
                if sha256(bytes(res["username"] + res["password"], encoding="utf-8")).hexdigest() == hash:
                    return True
                else:
                    return False
        except sqlite3.Error as e:
            print("Произошла ошибка при верификации пользователя" + str(e))
        return False
    @state_db_function("Ошибка при добавлении предмета в базу данных")
    def add_stuff(self, title: str, description: str, picture: str, price: int):
        '''Добавление предмета в базу данных'''
        tm = datetime.datetime.now()
        self._cursor.execute("insert into stuff values(NULL, ?, ?, ?, ?,?)",
                            (title, description, price, tm, picture))
        self._conn.commit()

    def get_stuff(self, page: int):
        '''Получение предметов из базы данных'''
        try:
            self._cursor.execute("select * from stuff limit ?, ?",
                                 (page * self.__PAGE_SIZE, (page + 1) * self.__PAGE_SIZE))
            res = self._cursor.fetchall()
            print(res)
            if res: return res
        except sqlite3.Error as e:
            print("Произошла ошибка при попытке получить товары из магазина " + str(e))
        return False
    @state_db_function("Произошла ошибка при добавлении покупки")
    def add_purchase(self, username: str, itemid: int):
        '''Добавление покупки'''
        tm = datetime.datetime.now()
        self._cursor.execute("select * from users where username = ?", (username,))
        res = self._cursor.fetchone()
        if res:
            user_id = res["id"]
            self._cursor.execute("insert into purchases values(NULL, ?, ?, ?, ?, NULL)",
                                (tm, itemid, user_id, "await",))
            self._conn.commit()

    def get_bucket(self, username: str):
        '''Получение товаров добавленных в корзину и заказанных пользователем'''
        try:
            self._cursor.execute("select * from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res:
                user_id = res["id"]
                self._cursor.execute(
                    "select purchases.id as mainid, * from purchases, stuff "
                    "where purchases.itemid = stuff.id and purchases.userid = ? and purchases.state = 'await'",
                    (user_id,))
                res = self._cursor.fetchall()
                return res
        except sqlite3.Error as e:
            print("Произошла ошибка во время покупки товара" + str(e))
        return []

    @state_db_function("Ошибка при удалении элемента из корзины")
    def safe_delete_from_bucket(self, username, id):
        '''Удаление элемента из корзины'''
        self._cursor.execute("select * from users where username = ?", (username,))
        res = self._cursor.fetchone()
        if res:
            user_id = res["id"]
            self._cursor.execute("delete from purchases where id = ? and userid = ?", (id, user_id))
            self._conn.commit()
    @state_db_function("Ошибка при добавлении жалобы")
    def add_complaint(self, title: str, content: str, username: str):
        '''Добавление жалобы'''
        tm = datetime.datetime.now()

        self._cursor.execute("select * from users where username = ?", (username,))
        res = self._cursor.fetchone()
        if res:
            user_id = res["id"]
            self._cursor.execute("insert into complaints values(NULL, ?, ?, ?, ?, ?)",
                                (title, content, tm, user_id, "await"))
            self._conn.commit()

    def get_complaints(self):
        '''Получение жалоб из Базы данных'''
        try:
            self._cursor.execute(
                "select complaints.id, complaints.time, complaints.title, complaints.content, users.username from complaints, users where complaints.userid = users.id")
            res = self._cursor.fetchall()
            if res: return res
        except sqlite3.Error as e:
            print("Не удается получить жалобы" + str(e))
        return []

    def get_registration_time(self, username):
        '''Возвращает время регистрации пользователя'''
        try:
            self._cursor.execute("select register_date from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res: return res
        except sqlite3.Error as e:
            print("Не удается получить дату:" + str(e))
        return []
    @state_db_function("Ошибка при удалении заказа")
    def add_order(self, location: str):
        tm = datetime.datetime.now()
        # добавление заказа в базу данных
        self._cursor.execute("insert into orders values (NULL, ?, 'await', ?, NULL)", (tm, location))
        self._conn.commit()
    def get_user_id(self, username: str):
        # получение id пользователя
        try:
            self._cursor.execute("select id from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res:
                return res["id"]
        except sqlite3.Error as e:
            print("Не удалось получить id пользователя")
    @state_db_function("Ошибка при добавлении функции")
    def send_to_order(self, username: str, location: str):
        # получение пользователя
        self._cursor.execute("select * from users where username = ?", (username,))
        user = self._cursor.fetchone()
        self._cursor.execute("select count(*) as times from purchases where userid = ? and state = 'await'", (user["id"],))
        # считаем количество заказов
        res = self._cursor.fetchone()
        if res["times"] != 0:

            tm = datetime.datetime.now()
            self._cursor.execute("insert into orders values (NULL, ?, 'await', ?, NULL)", (tm, location))
            # изменяем те заказы, которые находятся в магазине
            self._conn.commit()
            self._cursor.execute("select * from orders where timestamp = ?", (tm,))
            order = self._cursor.fetchone()
            if order:
                # даем этим заказам id пользователя
                if user:
                    self._cursor.execute("update purchases set orderid = ?, state = ? where userid = ? and state = ?",
                                        (order["id"], "done", user["id"], "await"))
                    self._conn.commit()
            return True
        return False
    def get_all_orders(self):
        try:
            # получаем все заказы из базы данных
            self._cursor.execute('select orderid, status, price, title, time, '
                                 'description, timestamp, workstamp from purchases, orders, stuff '
                                 'where (orderid >= 0 and orderid = orders.id and itemid = stuff.id) '
                                 'group by purchases.id')
            result = self._cursor.fetchall()

            print(result)
            # возвращаем из функции
            if result:
                return result
        except sqlite3.Error as e:
            print("Ошибка при получении всех заказов " + str(e))
        return []
    def get_orders(self, username: str):
        try:
            id_ = self.get_user_id(username)
            # получаем заказы для определенного пользователя
            self._cursor.execute('select orderid, status, price, title, time, description, timestamp, workstamp '
                                 'from purchases, orders, stuff'
                                 ' where (orderid >= 0 and orderid = orders.id and userid = ? and itemid = stuff.id) '
                                 'group by purchases.id', (id_,))
            result = self._cursor.fetchall()
            print(result)
            if result:
                return result
        except sqlite3.Error as e:
            print("Ошибка при получении заказа: " + str(e))
        return []
    @state_db_function("Ошибка при удалении отзываы")
    def remove_complaint(self, id: int):
        # удаление жалобы, и обновление бд
        self._cursor.execute("delete from complaints where id = ?", (id,))
        self._conn.commit()
    @state_db_function("Ошибка при удалении удалении товара из магазина")
    def remove_stuff(self, id: int):
        # удаление товара, и обновление бд
        self._cursor.execute("delete from stuff where id = ?", (id,))
        self._conn.commit()
    @state_db_function("Ошибка при изменении статуса заказа")
    def change_order_state(self, id: int, status: str):
        # изменение статуса заказа  и обновление бд
        tm = datetime.datetime.now()
        self._cursor.execute("update orders set status = ?, workstamp = ? where id = ?", (status, tm, id))
        self._conn.commit()
