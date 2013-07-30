# coding=utf-8

import utils


class AppConfig(object):
    SECRET_KEY = utils.get_env_variable('SECRET_KEY')

# Число итераций в тесте
ITERATIONS_COUNT = 100
