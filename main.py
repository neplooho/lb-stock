#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Flask, Response, redirect, request
from sqlite3 import Error
import sqlite3
import requests
import json


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
    cur.close()
    if row is not None:
        return {'chat_id': row[0],
                'title': row[1].encode('ascii', 'ignore') if row[1] is not None else None,
                'hashtags': row[2].encode('ascii', 'ignore') if row[2] is not None else None,
                'price': row[3],
                'description': row[4].encode('ascii', 'ignore') if row[4] is not None else None,
                'images': row[5],
                'step': row[6]}
    else:
        return None


def create_session(conn, chat_id):
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO stock_sessions (chat_id, step) VALUES ({}, '/new');".format(chat_id))


def update_session_step(conn, chat_id, step):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET step = '{}' WHERE chat_id = {};".format(step, chat_id))


def ask_for_title(conn, chat_id):
    send_message(chat_id, "Отправьте заголовок для вашего объявления")
    update_session_step(conn, chat_id, '/title')


def ask_for_hashtags(conn, chat_id):
    send_message(chat_id, "Отправьте в одном сообщении хештеги через пробел")
    update_session_step(conn, chat_id, '/hashtags')


def ask_for_price(conn, chat_id):
    send_message(chat_id, "Отправьте примерную цену в гривнах (это должно быть число а не диапазон от и до)")
    update_session_step(conn, chat_id, '/price')


def ask_for_description(conn, chat_id):
    send_message(chat_id, "Отправьте описание в одном сообщении для вашего объявления")
    update_session_step(conn, chat_id, '/description')


def ask_for_images(conn, chat_id):
    send_message(chat_id, "Отправьте в одном сообщении картинки для вашего объявления")
    update_session_step(conn, chat_id, '/images')


def build_telegraph_and_return_link(conn, chat_id):
    send_message(chat_id, json.dumps(get_session(conn, chat_id)))
    # print(get_session(conn, chat_id))  # TODO


def send_available_options(chat_id):
    send_message(chat_id, """Список доступных команд:
    /new - Создать новое объявление (если есть незаконченное старое то оно сотрется)
    /help - Показать доступные команды
    /title - Добавить заголовок
    /hashtags - Добавить хештеги
    /price - Указать цену
    /description - Добавить описание
    /images - Добавить картинки (в одном сообщении)
    /finish - Отправить объявление на рассмотрение""")


def set_title(conn, chat_id, title):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET title = '{}' WHERE chat_id = {}".format(title, chat_id))


def set_hashtags(conn, chat_id, hashtags):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET hashtags = '{}' WHERE chat_id = {}".format(hashtags, chat_id))


def set_price(conn, chat_id, price):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET price = {} WHERE chat_id = {}".format(price, chat_id))


def set_description(conn, chat_id, description):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET description = '{}' WHERE chat_id = {}".format(description, chat_id))


def set_images(conn, chat_id, images):
    pass


options = {'/title': (ask_for_title, set_title),
           '/hashtags': (ask_for_hashtags, set_hashtags),
           '/price': (ask_for_price, set_price),
           '/description': (ask_for_description, set_description),
           '/images': (ask_for_images, set_images),
           '/finish': (build_telegraph_and_return_link, None), #some crutches here, nvm
           '/help': send_available_options}

app = Flask(__name__)
BOT_URL = 'https://api.telegram.org/bot{0}/'.format(open('secrets/bot_token', 'r').read()[:-1])
database_path = r"database/db.sqlite"


def send_message(chat_id, ans):
    message_url = BOT_URL + 'sendMessage'
    data = {
        'chat_id': chat_id,
        'text': ans
    }
    requests.post(message_url, json=data)


@app.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@app.route('/', methods=['POST'])
def main():
    conn = create_connection(database_path)
    data = request.get_json()
    chat_id = int(data['message']['chat']['id'])
    text = data['message']['text']#.encode('utf-8') #should fix UnicodeEncodeError
    if text == '/new':
        create_session(conn, chat_id)
        send_message(chat_id, "Отправь /help чтобы посмотреть список доступных команд")
    session = get_session(conn, chat_id)
    if session is None:
        send_message(chat_id, 'Чтобы создать новое объявление отправь /new')
        conn.commit()
        conn.close()
        return Response('Duck says meow')
    if text in options:
        if text == '/help':
            send_available_options(chat_id)
        else:
            update_session_step(conn, chat_id, step=text)
            options[text][0](conn, chat_id)
    elif session['step'] != '/new':
        options[session['step']][1](conn, chat_id, text.encode('utf-8'))
        send_message(chat_id, "Отлично, что дальше?")
    else:
        send_message(chat_id, "Я не знаю такой команды как {}".format(text))
        conn.commit()
    conn.commit()
    conn.close()
    return Response('Duck says meow')


if __name__ == '__main__':
    app.run(ssl_context=('secrets/public.pem', 'secrets/private.key'), host='0.0.0.0', port=8443)
