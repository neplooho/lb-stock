from sqlite3 import Error
import sqlite3


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


def get_session(conn, chat_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM stock_sessions WHERE chat_id = {};".format(chat_id))
    row = cur.fetchone()

    return row


def create_session(conn, chat_id):
    cur = conn.cursor()
    cur.execute("INSERT INTO stock_sessions (chat_id) VALUES ({});".format(chat_id))


database_path = r"database/db.sqlite"
conn = create_connection(database_path)
chat_id = 123
session = get_session(conn, chat_id)
if session is None:
    create_session(conn, chat_id)
    session = get_session(conn, chat_id)

print(session)