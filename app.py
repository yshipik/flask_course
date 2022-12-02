from flask import Flask
import os
from config import Config
app = Flask(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, "db.db")))
app.config.update(dict(DOWNLOADS=os.path.join(app.root_path, "downloads")))
app.config.from_object(Config)
import routes