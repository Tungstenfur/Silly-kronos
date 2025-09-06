import sqlite3
db = sqlite3.connect('main.db')
cursor = db.cursor()
cursor.execute('CREATE TABLE points (user_id INTEGER UNIQUE, points INTEGER)')