#!/usr/bin/env python3
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
possible_hashtags = set(
    "#лбкиїв_компліт #лбкиїв_підвіси #лбкиїв_колеса #лбкиїв_дека #лбкиїв_інше #лбкиїв_захист".split(' '))
green_check_mark = '✔'
red_x = '❌'
remove_markup = {'remove_keyboard': True}


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
    default_tags = ' '.join([red_x + x for x in possible_hashtags])
    cur.execute(
        "INSERT OR REPLACE INTO stock_sessions (chat_id, step, hashtags) VALUES ({}, '/title', '".format(
            chat_id) + default_tags + "');")


def update_session_step(conn, chat_id, step, *args):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET step = '{}' WHERE chat_id = {};".format(step, chat_id))


def ask_for_title(conn, chat_id, *args):
    send_message(chat_id, "Отправьте заголовок для вашего объявления", reply_markup=remove_markup)
    update_session_step(conn, chat_id, '/title')


def ask_for_hashtags(conn, chat_id, *args):
    send_message(chat_id,
                 "Отправьте в одном сообщении хештеги через пробел\nВозможные хештеги:\n" + ' '.join(possible_hashtags),
                 reply_markup=remove_markup)
    update_session_step(conn, chat_id, '/hashtags')


def ask_for_price(conn, chat_id, *args):
    send_message(chat_id, "Отправьте примерную цену в гривнах (это должно быть число а не диапазон от и до)",
                 reply_markup=remove_markup)
    update_session_step(conn, chat_id, '/price')


def ask_for_description(conn, chat_id, *args):
    send_message(chat_id, "Отправьте описание в одном сообщении для вашего объявления", reply_markup=remove_markup)
    update_session_step(conn, chat_id, '/description')


def ask_for_images(conn, chat_id, *args):
    send_message(chat_id, "Отправьте картинки файлами", reply_markup=remove_markup)
    update_session_step(conn, chat_id, '/images')


def build_telegraph_and_return_link(conn, chat_id, *args):
    session = get_session(conn, chat_id)
    if not is_ready_to_finish(session):
        missing_values = get_missing_values(session)
        send_message(chat_id, 'Зполните пожалуйсте следующие поля:\n' + ', '.join(missing_values),
                     remove_markup=remove_markup)
        return
    links_to_download = [FILE_URL + x for x in session['images']]
    image_binaries = [requests.get(x).content for x in links_to_download]
    paths = [x['src'] for x in requests.post('https://telegra.ph/upload',
                                             files={str(k): ('file', v, 'image/jpeg') for k, v in
                                                    enumerate(image_binaries)}).json()]
    images_content = '\n'.join(["<img src = '{}' />".format(x) for x in paths])
    html_content = images_content + '<p>Цена: ' + str(session['price']) + '</p>\n<p>' + session['description'] + '</p>'
    response = telegraph.create_page(session['title'], html_content=html_content)
    clear_session(conn, chat_id)  # clear order data
    send_message(chat_id, response['url'] + '\n' + ' '.join([x[1:] for x in session['hashtags'].split(' ') if
                                                             x[0] == green_check_mark]) + '\n@' + str(args[0]),
                 reply_markup=remove_markup)


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
/finish - Отправить объявление на рассмотрение""", reply_markup=remove_markup)


def set_title(conn, chat_id, title, *args):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET step = '/description', title = '" + title.replace('\'',
                                                                                             '\'\'') + "' WHERE chat_id = " + str(
        chat_id))
    send_message(chat_id, "Отлично, а описание?", reply_markup=remove_markup)


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


def get_hashtags_markup(conn, chat_id, existing_tags):
    mark = list(batch([{'text': x} for x in existing_tags], 2))
    mark.append([{'text': 'Готово'}])
    reply_markup = {'one_time_keyboard': False,
                    'keyboard': mark,
                    'resize_keyboard': True}
    return reply_markup


def get_inverted_emoji(char):
    if char == red_x:
        return green_check_mark
    else:
        return red_x


def toggle_hashtag(conn, chat_id, hashtag, *args):  # todo: react to single hashtag, update it's check status
    cur = conn.cursor()
    tags = get_session(conn, chat_id)['hashtags']
    if tags is not None:
        existing_tags = get_session(conn, chat_id)['hashtags'].split(' ')
    else:
        existing_tags = []
    if hashtag in existing_tags:
        existing_tags.remove(hashtag)
    existing_tags.append(get_inverted_emoji(hashtag[0]) + hashtag[1:])
    res = ' '.join(existing_tags)
    if not res.strip():
        send_message(chat_id, 'Я не знаю таких хештегов, выбери из списка',
                     reply_markup=get_hashtags_markup(conn, chat_id, existing_tags))
    else:
        cur.execute(
            "UPDATE stock_sessions SET hashtags = '" + res + "' WHERE chat_id = " + str(chat_id))
        send_message(chat_id, hashtag, reply_markup=get_hashtags_markup(conn, chat_id, existing_tags))


def set_price(conn, chat_id, price, *args):
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE stock_sessions SET step = '/hashtags', price = " + price + " WHERE chat_id = " + str(chat_id))
    except sqlite3.OperationalError as e:
        print(type(e))
        send_message(chat_id, 'Не получилось сохранить цену, отправь ещё раз. Вот пример: 840.00',
                     reply_markup=remove_markup)
        return
    send_message(chat_id, 'Цена сохранена, выбери хештеги',
                 get_hashtags_markup(conn, chat_id, get_session(conn, chat_id)['hashtags'].split(' ')))


def set_description(conn, chat_id, description, *args):
    cur = conn.cursor()
    cur.execute("UPDATE stock_sessions SET step = '/images', description = '" + description.replace('\'',
                                                                                                    '\'\'') + "' WHERE chat_id = " + str(
        chat_id))
    send_message(chat_id, "Отличное описание, выгрузи теперь картинки файлами", reply_markup=remove_markup)


def add_image(conn, chat_id, file_path, *args):
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO images (image_path, chat_id) VALUES ('" + file_path + "', " + str(chat_id) + ");")
    send_message(chat_id, "Круто, картинка добавлена", reply_markup={'one_time_keyboard': True, 'keyboard': [
        [{'text': 'Я добавил все картинки, перейти дальше'}]], 'resize_keyboard': True})


options = {'/title': (ask_for_title, set_title),
           '/hashtags': (ask_for_hashtags, toggle_hashtag),
           '/price': (ask_for_price, set_price),
           '/description': (ask_for_description, set_description),
           '/images': (ask_for_images, add_image),
           '/finish': (build_telegraph_and_return_link, None),  # some crutches here, nvm
           '/help': send_available_options,
           '/ready': (None)}  # TODO show preview and submit buttons on this stem


def send_message(chat_id, ans, reply_markup=None):
    message_url = BOT_URL + 'sendMessage'
    data = {
        'chat_id': chat_id,
        'text': ans
    }
    if reply_markup is not None:
        data['reply_markup'] = reply_markup
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
    print(data['message'])
    if 'text' in data['message'] and data['message']['text'] == '/new':
        create_session(conn, chat_id)
        send_message(chat_id, "Какой будет заголовок?", reply_markup=remove_markup)
        conn.commit()
        conn.close()
        return Response('Duck says meow')
    session = get_session(conn, chat_id)
    if session is None:
        send_message(chat_id, "Сначала создайте новое объявление с помощью /new", reply_markup=remove_markup)
        conn.close()
        return Response('Duck says meow')
    if session['step'] == '/images' and 'document' in data['message']:
        file_id = data['message']['document']['file_id']
        file_path = requests.get(BOT_URL + 'getFile?file_id=' + file_id).json()['result']['file_path']
        add_image(conn, chat_id, file_path)
        conn.commit()
        conn.close()
        return Response('Duck says meow')
    elif session['step'] == '/images' and 'text' in data['message'] and data['message'][
        'text'] == 'Я добавил все картинки, перейти дальше':
        update_session_step(conn, chat_id, '/price')
        send_message(chat_id, 'Такс, и сколько ты за это хочешь?',
                     reply_markup=remove_markup)
    elif session['step'] == '/hashtags' and 'text' in data['message'] and data['message']['text'] == 'Готово':
        update_session_step(conn, chat_id, '/ready')
        send_message(chat_id, "Готово!", reply_markup={'one_time_keyboard': True, 'keyboard': [
            [{'text': 'Посмотреть'}, {'text': 'Отправить'}]], 'resize_keyboard': True})
    elif session['step'] == '/ready' and 'text' in data['message'] and data['message']['text'] == 'Посмотреть':
        build_telegraph_and_return_link(conn, chat_id, data['message']['from']['username'])
        send_message(chat_id, None, reply_markup={'one_time_keyboard': True, 'keyboard': [
            [{'text': 'Отправить'}]], 'resize_keyboard': True})
    elif session['step'] == '/ready' and 'text' in data['message'] and data['message']['text'] == 'Отправить':
        # todo forward post to admins
        pass
    else:
        options[session['step']][1](conn, chat_id, data['message']['text'])

    # text = session['step']
    # if text in options:
    #     if text == '/help':
    #         send_available_options(chat_id)
    #     else:
    #         update_session_step(conn, chat_id, step=text)
    #         options[text][0](conn, chat_id, data['message']['from']['username'])
    # elif session['step'] != '/new':
    #     options[session['step']][1](conn, chat_id, text)
    #     # send_message(chat_id, "Отлично, что дальше?")
    # else:
    #     send_message(chat_id, "Я не знаю такой команды как {}".format(text))
    #     conn.commit()
    conn.commit()
    conn.close()
    return Response('Duck says meow')


if __name__ == '__main__':
    app.run(ssl_context=('secrets/public.pem', 'secrets/private.key'), host='0.0.0.0', port=8443)
