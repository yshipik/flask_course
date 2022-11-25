import sqlite3, os, datetime
from hashlib import sha256
from app import app


class Database:
    _conn: sqlite3.Connection
    _cursor: sqlite3.Cursor
    __PAGE_SIZE = 15
    def __init__(self, file=""):
        if not file:
            self._conn = sqlite3.connect(app.config['DATABASE'])
        else:
            self._conn = sqlite3.connect(file)
        self._conn.row_factory = sqlite3.Row
        self._cursor = self._conn.cursor()

    def add_menu(self, name: str, url: str, category: str):
        try:
            self._cursor.execute("insert into menu values (NULL, ?, ?, ?)", (name, url, category))
            self._conn.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления в меню БД" + str(e))
            return False
        return True

    def add_user(self, username: str, password: str, is_stuff=False):
        tm = datetime.datetime.now()
        try:
            self._cursor.execute("insert into users values (NULL, ?, ?, ?, ?)", (username, password, tm, is_stuff))
            self._conn.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления пользователя в БД: " + str(e))
            return False
        return True

    def get_menu(self):
        try:
            self._cursor.execute("select * from menu")
            res = self._cursor.fetchall()
            if res: return res
        except sqlite3.Error as e:
            print("Ошибка получения информации в бд", str(e))
        return []

    def login(self, username: str, password: str):
        try:
            self._cursor.execute("select * from users where username = ? and password = ?", (username, password))
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
    def add_stuff(self, title: str, description: str, picture: str, price: int):
        tm = datetime.datetime.now()
        try:
            self._cursor.execute("insert into stuff values(NULL, ?, ?, ?, ?,?)",
                                 (title, description, price, tm, picture))
            self._conn.commit()
            return True
        except sqlite3.Error as e:
            print("Произошла ошибка при добавлении поста" + str(e))
        return False

    def get_stuff(self, page: int):
        try:
            self._cursor.execute("select * from stuff limit ?, ?", (page * self.__PAGE_SIZE, (page + 1) * self.__PAGE_SIZE ) )
            res = self._cursor.fetchall()
            print(res)
            if res: return res
        except sqlite3.Error as e:
            print("Произошла ошибка при попытке получить товары из магазина " + str(e))
        return False
    def add_purchase(self, username: str, itemid: int):
        tm = datetime.datetime.now()
        try:
            self._cursor.execute("select * from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res:
                user_id = res["id"]
                self._cursor.execute("insert into purchases values(NULL, ?, ?, ?, ?)", (tm, itemid, user_id, "await"))
                self._conn.commit()
                return True
        except sqlite3.Error as e:
            print("Произошла ошибка во время покупки товара")
        return False
    def get_bucket(self, username: str):
        try:
            self._cursor.execute("select * from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res:
                user_id = res["id"]
                self._cursor.execute("select * from purchases, stuff where purchases.itemid = stuff.id and purchases.userid = ?", (user_id,))
                res = self._cursor.fetchall()
                return res
        except sqlite3.Error as e:
            print("Произошла ошибка во время покупки товара" + str(e))
        return []
    def add_complaint(self, title: str, content: str, username: str):
        tm = datetime.datetime.now()
        try:
            self._cursor.execute("select * from users where username = ?", (username,))
            res = self._cursor.fetchone()
            if res:
                user_id = res["id"]
                self._cursor.execute("insert into complaints values(NULL, ?, ?, ?, ?, ?)", (title, content, tm, user_id, "await"))
                self._conn.commit()
                return True
        except sqlite3.Error as e:
            print("Произошла ошибка во время покупки товара")
        return False
    def get_complaints(self):
        try:
            self._cursor.execute("select complaints.id, complaints.time, complaints.title, complaints.content, users.username from complaints, users where complaints.userid = users.id")
            res = self._cursor.fetchall()
            if res: return res
        except sqlite3.Error as e:
            print("Не удается получить жалобы" + str(e))
        return []

