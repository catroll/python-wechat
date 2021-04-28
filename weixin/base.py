# -*- coding: utf-8 -*-


__all__ = ('WechatError',)


class WechatError(Exception):

    def __init__(self, msg):
        super(WechatError, self).__init__(msg)
