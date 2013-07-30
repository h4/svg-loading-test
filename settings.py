# coding=utf-8

import utils


class AppConfig(object):
    SECRET_KEY = utils.get_env_variable('SECRET_KEY')

ITERATIONS_COUNT = 100
