# coding=utf-8

import urllib2
import random
import base64
import json
import uuid
from flask import Flask, make_response, render_template, request, session
from pymongo import MongoClient
from time import time
from settings import ITERATIONS_COUNT

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


if __name__ == '__main__':
    app.debug = True
    app.run()
