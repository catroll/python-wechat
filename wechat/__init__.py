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


class Wechat(WechatAuth, WechatPay, WechatMP, WechatMsg):
    """
    微信SDK

    :param app 如果非flask，传入字典配置，如果是flask直接传入app实例
    """

    def __init__(self, app=None):
        if app is not None:
            if isinstance(app, dict):
                app = StandaloneApplication(config=app)
            self.init_app(app)
            self.app = app

    def init_app(self, app):
        if isinstance(app, dict):
            app = StandaloneApplication(config=app)

        token = app.config.get('WEIXIN_TOKEN')
        sender = app.config.get('WEIXIN_SENDER', None)
        expires_in = app.config.get('WEIXIN_EXPIRES_IN', 0)
        mch_id = app.config.get('WEIXIN_MCH_ID')
        mch_key = app.config.get('WEIXIN_MCH_KEY')
        notify_url = app.config.get('WEIXIN_NOTIFY_URL')
        mch_key_file = app.config.get('WEIXIN_MCH_KEY_FILE')
        mch_cert_file = app.config.get('WEIXIN_MCH_CERT_FILE')
        app_id = app.config.get('WEIXIN_APP_ID')
        app_secret = app.config.get('WEIXIN_APP_SECRET')

        if token:
            WechatMsg.__init__(self, token, sender, expires_in)
        if app_id and mch_id and mch_key and notify_url:
            WechatPay.__init__(self, app_id, mch_id, mch_key, notify_url, mch_key_file, mch_cert_file)
        if app_id and app_secret:
            WechatAuth.__init__(self, app_id, app_secret)
            WechatMP.__init__(self, app_id, app_secret)
