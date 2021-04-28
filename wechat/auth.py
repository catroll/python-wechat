import logging

import requests

from .base import WechatError, urlencode

LOG = logging.getLogger(__name__)

__all__ = 'WechatAuthError', 'WechatAuth'


class WechatAuthError(WechatError):
    def __init__(self, msg):
        super(WechatAuthError, self).__init__(msg)


class WechatAuth(object):
    """微信网页授权

    1、微信网页授权是通过 OAuth2.0 机制实现的，
        在用户授权给公众号后，公众号可以获取到一个网页授权特有的接口调用凭证（网页授权access_token），
        通过网页授权 access_token 可以进行授权后接口调用，如获取用户基本信息；
    2、其他微信接口，需要通过基础支持中的 “获取 access_token” 接口来获取到的普通 access_token 调用。

    第一步：用户同意授权，获取code
    第二步：通过code换取网页授权 access_token
    第三步：刷新 access_token（如果需要）
    第四步：拉取用户信息(需scope为 snsapi_userinfo)
    附：检验授权凭证（access_token）是否有效
    """

    AUTH_HOST = 'https://api.weixin.qq.com'

    def __init__(self, app_id, app_secret, debug_mode=False):
        self.sess = requests.Session()
        self.app_id = app_id
        self.app_secret = app_secret
        self.debug = debug_mode

    def _get(self, url, params):
        if self.debug:
            LOG.debug('request %s, params: %r', url, params)
        resp = self.sess.get(url, params=params)
        data = resp.json()
        if self.debug:
            LOG.debug('request %s, response: %r', url, data)
        if 'errcode' in data and data['errcode']:
            msg = '%(errcode)d %(errmsg)s' % data
            LOG.debug('request %s, error: %s', url, msg)
            raise WechatAuthError(msg)
        return data

    def authorize(self, redirect_uri, scope='snsapi_base', state=None):
        """
        生成微信认证地址并且跳转

        注意：文档中特意强调参数传递顺序！
        > 尤其注意：由于授权操作安全等级较高，所以在发起授权请求时，
        > 微信会对授权链接做正则强匹配校验，如果链接的参数顺序不对，授权页面将无法正常访问

        ERROR_CODES = {
            10003: 'redirect_uri域名与后台配置不一致',
            10004: '此公众号被封禁',
            10005: '此公众号并没有这些scope的权限',
            10006: '必须关注此测试号',
            10009: '操作太频繁了，请稍后重试',
            10010: 'scope不能为空',
            10011: 'redirect_uri不能为空',
            10012: 'appid不能为空',
            10013: 'state不能为空',
            10015: '公众号未授权第三方平台，请检查授权状态',
            10016: '不支持微信开放平台的Appid，请使用公众号Appid',
        }

        :param redirect_uri: 跳转地址（应该是 HTTPS 协议），urlEncode 编码
        :param scope: 微信认证方式，有`snsapi_base`跟`snsapi_userinfo`两种
        :param state: 认证成功后会原样带上此字段
        """
        url = (
                  'https://open.weixin.qq.com/connect/oauth2/authorize'
                  '?appid=%(appid)s'
                  '&redirect_uri=%(redirect_uri)s'
                  '&response_type=code'
                  '&scope=%(scope)s'
                  '&state=%(state)s'
                  '#wechat_redirect'
              ) % {
                  'appid': self.app_id,
                  'redirect_uri': urlencode(redirect_uri),
                  'scope': scope,
                  'state': state,
              }
        LOG.debug('an authorize url has been generated: %s', url)
        return url

    def access_token(self, code):
        """
        获取令牌
        """
        LOG.info('fetch access token, use code %s', code)
        result = self._get(self.AUTH_HOST + '/sns/oauth2/access_token', {
            'appid': self.app_id,
            'secret': self.app_secret,
            'code': code,
            'grant_type': 'authorization_code',
        })
        # LOG.debug('fetch access token, result: %r', result)
        return result

    def auth(self, access_token, openid):
        """
        检验授权凭证
        :param access_token: 授权凭证
        :param openid: 唯一id
        """
        LOG.info('check access token, %s for openid %s', access_token, openid)
        result = self._get(self.AUTH_HOST + '/sns/auth', {
            'access_token': access_token,
            'openid': openid,
        })
        # LOG.debug('check access token, result: %r', result)
        return result

    def refresh_token(self, refresh_token):
        """
        重新获取access_token
        :param refresh_token: 刷新令牌
        """
        LOG.info('refresh access token, use refresh token %s', refresh_token)
        result = self._get(self.AUTH_HOST + '/sns/oauth2/refresh_token', {
            'appid': self.app_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        })
        # LOG.debug('refresh access token, result: %r', result)
        return result

    def userinfo(self, access_token, openid):
        """
        获取用户信息
        :param access_token: 令牌
        :param openid: 用户id，每个应用内唯一
        """
        LOG.info('get userinfo of openid %s use access token %s', openid, access_token)
        result = self._get(self.AUTH_HOST + '/sns/userinfo', {
            'access_token': access_token,
            'openid': openid,
            'lang': 'zh_CN',
        })
        # LOG.debug('get userinfo, result: %r', result)
        return result

    def jscode2session(self, js_code):
        """
        小程序获取 session_key 和 openid
        """
        LOG.info('jscode2session, %s', js_code)
        result = self._get(self.AUTH_HOST + '/sns/jscode2session', {
            'appid': self.app_id,
            'secret': self.app_secret,
            'js_code': js_code,
            'grant_type': 'authorization_code',
        })
        # LOG.debug('jscode2session, result: %r', result)
        return result
