#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Flask, Response, redirect, request
from sqlite3 import Error
import sqlite3
import requests
from telegraph import Telegraph

telegraph = Telegraph()
telegraph.create_account(short_name='Барахолка')
app = Flask(__name__)
BOT_URL = 'https://api.telegram.org/bot{0}/'.format(open('secrets/bot_token', 'r').read()[:-1])
FILE_URL = 'https://api.telegram.org/file/bot{0}/'.format(open('secrets/bot_token', 'r').read()[:-1])
database_path = r"database/db.sqlite"
possible_hashtags = set("#лбкиїв_компліт #лбкиїв_підвіси #лбкиїв_колеса #лбкиїв_дека #лбкиїв_інше #лбкиїв_захист".split(' '))

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
    cur.execute("SELECT image_path FROM images WHERE chat_id = {};".format(chat_id))
    images = [x[0] for x in cur.fetchall()]
    cur.close()
    if row is not None:
        return {'chat_id': row[0],
                'title': row[1],
                'hashtags': row[2],
                'price': row[3],
                'description': row[4],
                'step': row[5],
                'images': images}
    else:
        return None


def clear_session(conn, chat_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM images WHERE chat_id = {};".format(chat_id))
    cur.execute("DELETE FROM stock_sessions WHERE chat_id = {};".format(chat_id))
    cur.close()


def format_session_to_text(session):
    return 'Chat: ' + str(session['chat_id']) + ' \nTitle: ' + (session[
                                                                    'title'] or u'None') + ' \nHashtags: ' + (
                   session['hashtags'] or u'None') + ' \nPrice: ' + str(
        session['price']) + ' \nDescription: ' + \
           (session['description'] or u'None') + ' \nImages: ' + ','.join(session['images']) + ' \nStep: ' + (
                   session['step'] or u'None')


def create_session(conn, chat_id, *args):
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO stock_sessions (chat_id, step) VALUES ({}, '/new');".format(chat_id))


def update_session_step(conn, chat_id, step, *args):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET step = '{}' WHERE chat_id = {};".format(step, chat_id))


def ask_for_title(conn, chat_id, *args):
    send_message(chat_id, "Отправьте заголовок для вашего объявления")
    update_session_step(conn, chat_id, '/title')


def ask_for_hashtags(conn, chat_id, *args):
    send_message(chat_id, "Отправьте в одном сообщении хештеги через пробел\nВозможные хештеги:\n" + ' '.join(possible_hashtags))
    update_session_step(conn, chat_id, '/hashtags')


def ask_for_price(conn, chat_id, *args):
    send_message(chat_id, "Отправьте примерную цену в гривнах (это должно быть число а не диапазон от и до)")
    update_session_step(conn, chat_id, '/price')


def ask_for_description(conn, chat_id, *args):
    send_message(chat_id, "Отправьте описание в одном сообщении для вашего объявления")
    update_session_step(conn, chat_id, '/description')


def ask_for_images(conn, chat_id, *args):
    send_message(chat_id, "Отправьте картинки файлами")
    update_session_step(conn, chat_id, '/images')


def build_telegraph_and_return_link(conn, chat_id, *args):
    session = get_session(conn, chat_id)
    if not is_ready_to_finish(session):
        missing_values = get_missing_values(session)
        send_message(chat_id, 'Зполните пожалуйсте следующие поля:\n' + ', '.join(missing_values))
        return
    links_to_download = [FILE_URL + x for x in session['images']]
    image_binaries = [requests.get(x).content for x in links_to_download]
    paths = [x['src'] for x in requests.post('https://telegra.ph/upload',
                                             files={str(k): ('file', v, 'image/jpeg') for k, v in
                                                    enumerate(image_binaries)}).json()]
    images_content = '\n'.join(["<img src = '{}' />".format(x) for x in paths])
    html_content = images_content + '<p>Цена: ' + str(session['price']) + '</p>\n<p>' + session['description'] + '</p>'
    response = telegraph.create_page(session['title'], html_content=html_content)
    clear_session(conn, chat_id) #clear order data
    send_message(chat_id, response['url'] + '\n' + session['hashtags'] + '\n' + args[0])


def is_ready_to_finish(session):
    for key, value in session.items():
        if value is None:
            return False
        if key == 'images' and len(value) == 0:
            return False
    return True


options_to_text = {'title': 'заголовок',
                   'hashtags': 'хештеги',
                   'price': 'цена',
                   'description': 'описание',
                   'images': 'картинки'}


def get_missing_values(session):
    missing_values = []
    for k, v in options_to_text.items():
        if session[k] is None:
            missing_values.append(v)
        if k == 'images' and len(session[k]) == 0:
            missing_values.append(v)
    return missing_values


def send_available_options(chat_id):
    send_message(chat_id, """Список доступных команд:
/new - Создать новое объявление (если есть незаконченное старое то оно сотрется)
/help - Показать доступные команды
/title - Добавить заголовок
/hashtags - Добавить хештеги
/price - Указать цену
/description - Добавить описание
/images - Добавить картинки
/finish - Отправить объявление на рассмотрение""")


def set_title(conn, chat_id, title, *args):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET title = '" + title.replace('\'', '\'\'') + "' WHERE chat_id = " + str(chat_id))


def set_hashtags(conn, chat_id, hashtags, *args):
    cur = conn.cursor()
    new_hashtags = set(hashtags.strip().split(' '))
    res = ' '.join([x for x in new_hashtags if x in possible_hashtags])
    if not res.strip():
        send_message(chat_id, 'Я не знаю таких хештегов, выбери из списка')
    else:
        cur.execute("UPDATE stock_sessions SET hashtags = '" + res + "' WHERE chat_id = " + str(chat_id))


def set_price(conn, chat_id, price, *args):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET price = " + price + " WHERE chat_id = " + str(chat_id))


def set_description(conn, chat_id, description, *args):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET description = '" + description.replace('\'', '\'\'') + "' WHERE chat_id = " + str(chat_id))


def add_image(conn, chat_id, file_path, *args):
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO images (image_path, chat_id) VALUES ('" + file_path + "', " + str(chat_id) + ");")


options = {'/title': (ask_for_title, set_title),
           '/hashtags': (ask_for_hashtags, set_hashtags),
           '/price': (ask_for_price, set_price),
           '/description': (ask_for_description, set_description),
           '/images': (ask_for_images, add_image),
           '/finish': (build_telegraph_and_return_link, None),  # some crutches here, nvm
           '/help': send_available_options}


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
    if 'text' in data['message'] and data['message']['text'] == '/new':
        create_session(conn, chat_id)
        send_message(chat_id, "Отправь /help чтобы посмотреть список доступных команд")
        conn.commit()
        conn.close()
        return Response('Duck says meow')
    session = get_session(conn, chat_id)
    if session is None:
        send_message(chat_id, "Сначала создайте новое объявление с помощью /new")
        conn.close()
        return Response('Duck says meow')
    if session['step'] == '/images' and 'document' in data['message']:
        file_id = data['message']['document']['file_id']
        file_path = requests.get(BOT_URL + 'getFile?file_id=' + file_id).json()['result']['file_path']
        add_image(conn, chat_id, file_path)
        conn.commit()
        conn.close()
        send_message(chat_id, "Картинка добавлена")
        return Response('Duck says meow')
    text = data['message']['text']
    if text in options:
        if text == '/help':
            send_available_options(chat_id)
        else:
            update_session_step(conn, chat_id, step=text)
            options[text][0](conn, chat_id, data['message']['from']['id'])
    elif session['step'] != '/new':
        options[session['step']][1](conn, chat_id, text)
        send_message(chat_id, "Отлично, что дальше?")
    else:
        send_message(chat_id, "Я не знаю такой команды как {}".format(text))
        conn.commit()
    conn.commit()
    conn.close()
    return Response('Duck says meow')


if __name__ == '__main__':
    app.run(ssl_context=('secrets/public.pem', 'secrets/private.key'), host='0.0.0.0', port=8443)
