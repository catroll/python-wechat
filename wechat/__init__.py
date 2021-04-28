# -*- coding: utf-8 -*-


from collections import namedtuple

from .auth import WechatAuth
from .base import WechatError
from .mp import WechatMP
from .msg import WechatMsg
from .pay import WechatPay

__all__ = ('Wechat',)
__author__ = 'Weicheng Zou <zwczou@gmail.com>'
__version__ = '2021.04.29'


StandaloneApplication = namedtuple('StandaloneApplication', ['config'])


class Wechat:
    """
    微信SDK

    :param app 如果非flask，传入字典配置，如果是flask直接传入app实例
    """

    def __init__(self, app=None, debug=False):
        if app is not None:
            if isinstance(app, dict):
                app = StandaloneApplication(config=app)
            self.init_app(app, debug=debug)
            self.app = app

    def init_app(self, app, debug=False):
        if isinstance(app, dict):
            app = StandaloneApplication(config=app)

        token = app.config.get('WXN_TOKEN')
        sender = app.config.get('WXN_SENDER', None)
        expires_in = app.config.get('WXN_EXPIRES_IN', 0)
        mch_id = app.config.get('WXN_MCH_ID')
        mch_key = app.config.get('WXN_MCH_KEY')
        notify_url = app.config.get('WXN_NOTIFY_URL')
        mch_key_file = app.config.get('WXN_MCH_KEY_FILE')
        mch_cert_file = app.config.get('WXN_MCH_CERT_FILE')
        app_id = app.config.get('WXN_APP_ID')
        app_secret = app.config.get('WXN_APP_SECRET')

        if token:
            self.msg = WechatMsg(token, sender, expires_in, debug=debug)
        if app_id and mch_id and mch_key and notify_url:
            self.pay = WechatPay(app_id, mch_id, mch_key, notify_url, mch_key_file, mch_cert_file, debug=debug)
        if app_id and app_secret:
            self.auth = WechatAuth(app_id, app_secret, debug=debug)
            self.mp = WechatMP(app_id, app_secret, debug=debug)
