# -*- coding: utf-8 -*-


from .msg import WechatMsg
from .pay import WechatPay
from .login import WechatLogin
from .mp import WechatMP
from .base import WechatError

from collections import namedtuple


__all__ = ('Wechat')
__author__ = 'Weicheng Zou <zwczou@gmail.com>'
__version__ = '0.5.7'


StandaloneApplication = namedtuple('StandaloneApplication', ['config'])


class Wechat(WechatLogin, WechatPay, WechatMP, WechatMsg):
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
            WechatLogin.__init__(self, app_id, app_secret)
            WechatMP.__init__(self, app_id, app_secret)

        # 兼容老版本
        if app_id and mch_id and mch_key and notify_url:
            self.pay = WechatPay(app_id, mch_id, mch_key, notify_url, mch_key_file, mch_cert_file)
        if token:
            self.msg = WechatMsg(token, sender, expires_in)
        if app_id and app_secret:
            self.login = WechatLogin(app_id, app_secret)
            self.mp = WechatMP(app_id, app_secret)
