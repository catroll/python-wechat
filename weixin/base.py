# -*- coding: utf-8 -*-


__all__ = ('WechatError',)


try:
    unicode = unicode
except NameError:
    # python 3
    basestring = (str, bytes)
else:
    # python 2
    bytes = str


class WechatError(Exception):

    def __init__(self, msg):
        super(WechatError, self).__init__(msg)
