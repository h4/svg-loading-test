# coding=utf-8

import urllib2
import random
import base64
import json
from flask import Flask, make_response, render_template, request
from pymongo import MongoClient
from time import time

app = Flask('svg')


def getImage(fname, mode=None):
    if mode is None:
        return '/{}'.format(fname)
    f = open(fname, 'r')
    return f.read()


def getRand(data, mode):
    rand = random.random() * time()
    if mode == 'external':
        return "{}?v={}".format(data, rand)
    return '{}<!--{}-->'.format(data,rand)


def formatData(data, mode):
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


@app.route('/test/<mode>/<cached>/')
def test(mode, cached='0'):
    imageName = 'static/tiger.svg'
    if mode == 'external':
        res = getImage(imageName)
    else:
        res = getImage(imageName, mode)

    if cached == '0':
        sources = [res for n in xrange(0, 15)]
    else:
        sources = [getRand(res, mode) for n in xrange(0, 15)]
    return render_template("base.html", sources=map(lambda x: formatData(x, mode), sources))


@app.route('/stat/', methods=['POST',])
def stat():
    user_agent = request.user_agent.string
    client = MongoClient('localhost', 27017)
    db = client.svg
    stat = db.stat
    data = {
        "time": request.form['time'],
        "path": request.form['path'],
        "user_agent": user_agent,
        "created": time(),
    }
    stat.insert(data)

    count = stat.find({"user_agent": user_agent, "path": request.form['path']}).count()
    res = json.dumps({'time':request.form['time'], 'count': count})

    return make_response(res)


if __name__ == '__main__':
    app.debug = True
    app.run()
