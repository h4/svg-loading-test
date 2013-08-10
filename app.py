# coding=utf-8

import urllib2
import random
import base64
import json
import uuid
from flask import Flask, make_response, render_template, request, session
from pymongo import MongoClient
from numpy import amin, amax, average, median, array
from time import time
from itertools import groupby

from settings import ITERATIONS_COUNT, ADMINS

app = Flask('svg')
app.config.from_object('settings.AppConfig')


def getImage(fname, mode=None):
    """
    Получить содержимое файла изображения или ссылку на него

    :param fname: имя файла
    :param mode: вернуть имя файла или его содержимое
    :return: str
    """
    if mode is None:
        return '/{}'.format(fname)
    f = open(fname, 'r')
    return f.read()


def getRand(data, mode):
    """
    Добавление случайной порции данных для запрета кеширования

    :param data: строка данных
    :param mode: режим кодирования
    :return: str
    """
    rand = random.random() * time()
    if mode == 'external':
        return "{}?v={}".format(data, rand)
    return '{}<!--{}-->'.format(data,rand)


def formatData(data, mode):
    """
    Установка префикса для data-uri

    :param data: строка данных
    :param mode: режим кодирования
    :return: str
    """
    if mode == 'external':
        return data
    res = 'data:image/svg+xml;utf8,{}'.format(data)
    if mode == 'encoded':
        res = 'data:image/svg+xml,{}'.format(urllib2.quote(data))
    if mode == 'base64':
        res = 'data:image/svg+xml;base64,{}'.format(base64.b64encode(data))
    return res


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/test/<mode>/<preventCache>/')
def test(mode, preventCache='0'):
    """
    Вывод страницы теста

    :param mode: режим вывода: external | embedded | encoded | base64
    :param preventCache: запрет кеширования
    """
    if 'uid' not in session:
        session['uid'] = uuid.uuid4()

    imageName = 'static/tiger.svg'
    if mode == 'external':
        res = getImage(imageName)
    else:
        res = getImage(imageName, mode)

    if preventCache == '0':
        sources = [res for n in xrange(0, 15)]
    else:
        sources = [getRand(res, mode) for n in xrange(0, 15)]
    return render_template("base.html", sources=map(lambda x: formatData(x, mode), sources),
                           iterCount=ITERATIONS_COUNT)


@app.route('/stat/', methods=['POST',])
def stat():
    """
    Сохранение статистических данных в MongoDB
    """
    user_agent = request.user_agent.string
    client = MongoClient('localhost', 27017)
    db = client.svg
    stat = db.stat
    data = {
        "time": request.form['time'],
        "path": request.form['path'],
        "user_agent": user_agent,
        "created": time(),
        "uid": session['uid']
    }
    stat.insert(data)

    count = stat.find({"path": request.form['path'], "uid": session['uid']}).count()

    if count >= ITERATIONS_COUNT:
        session.clear()

    res = json.dumps({'time':request.form['time'], 'count': count})

    return make_response(res)


@app.route('/result/')
def result_page():
    return render_template("result.html")
    pass


@app.route('/result/data/')
def result():
    """
    Получение результатов сбора статистики
    """
    client = MongoClient('localhost', 27017)
    db = client.svg
    stat = db.stat

    data = stat.find({"path": {"$exists": True}, "uid": {"$exists": True}}, fields={"_id": False}).sort([('user_agent', 1), ('path', 1)])
    res = []
    for elem in data:
        elem['uid'] = str(elem['uid'])
        res.append(elem)

    res = groupby(res, key=lambda x: x['user_agent'])

    data = {}

    for k, v in res:
        ua_dict = {}
        for ua, x in groupby(list(v), key=lambda x: x['path']):
            arr = [int(t['time']) for t in x]
            ua_dict[ua] = int(average(arr))
        data[k] = ua_dict

    res = [
        ["ua", "ext", "emb", "base64", "enc", "ext+rand", "emb+rand", "base64+rand", "enc+rand", ],
    ]

    def parse_data(elem):
        ret = []
        keys = [
            "/test/external/0/",
            "/test/embedded/0/",
            "/test/base64/0/",
            "/test/encoded/0/",
            "/test/external/1/",
            "/test/embedded/1/",
            "/test/base64/1/",
            "/test/encoded/1/",
            ]
        print elem

        for key in keys:
            ret.append(elem.get(key) or 0)
        return ret

    for k in data.keys():
        row = [k,] + parse_data(data[k])
        res.append(row)

    response = json.dumps(res)

    return make_response(response)

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler('127.0.0.1',
                               'server-error@svg.brnv.ru',
                               ADMINS, 'YourApplication Failed')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

if __name__ == '__main__':
    app.debug = True
    app.run()
