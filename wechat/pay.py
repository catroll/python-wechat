import logging
import time

import requests

from .base import WechatError, dict2xml, xml2dict, md5, hmac_sha256, random_string

LOG = logging.getLogger(__name__)

__all__ = 'WechatPayError', 'WechatPay'


class WechatPayError(WechatError):
    def __init__(self, msg):
        super(WechatPayError, self).__init__(msg)


FAIL = 'FAIL'
SUCCESS = 'SUCCESS'
SIGN_METHODS = {
    'md5': 'MD5',
    'hmac_sha256': 'HMAC-SHA256',
}


class WechatPay(object):
    PAY_HOST = 'https://api.mch.weixin.qq.com'

    def __init__(self, app_id, mch_id, mch_key, notify_url, key=None, cert=None,
                 sign_method='hmac_sha256'):
        self.app_id = app_id
        self.mch_id = mch_id
        self.mch_key = mch_key  # 商户平台 --> 账户设置 --> API安全 --> 密钥设置
        self.notify_url = notify_url
        self.key = key
        self.cert = cert
        self.sign_method = sign_method
        self.sess = requests.Session()

    @property
    def timestamp(self):
        return str(int(time.time()))

    @property
    def nonce_str(self):
        return random_string(32)

    def sign(self, raw, sign_method=None):
        sign_method = sign_method or self.sign_method
        raw = [(k, str(raw[k]) if isinstance(raw[k], int) else raw[k])
               for k in sorted(raw.keys())]
        s = '&'.join('='.join(kv) for kv in raw if kv[1])
        s += '&key=%s' % self.mch_key
        sign = getattr(self, '_sign_%s' % sign_method)(s)
        LOG.debug('签名 %s : %s => %s', sign_method, s, sign)
        return sign

    def _sign_md5(self, content):
        return md5(content)

    def _sign_hmac_sha256(self, content):
        return hmac_sha256(self.mch_key.encode('utf-8'), content.encode('utf-8'))

    def check(self, data):
        sign = data.pop('sign')
        return sign == self.sign(data)

    def _fetch(self, url, data, use_cert=False, appid=True):
        if appid:
            data.setdefault('appid', self.app_id)
        data.setdefault('mch_id', self.mch_id)
        data.setdefault('nonce_str', self.nonce_str)
        data.setdefault('sign', self.sign(data))
        data_xml = dict2xml(data)
        LOG.debug('Request %s: %s', url, data_xml)
        if use_cert:
            resp = self.sess.post(url, data=data_xml.encode('utf-8'), cert=(self.cert, self.key))
        else:
            resp = self.sess.post(url, data=data_xml.encode('utf-8'))
        content = resp.content.decode('utf-8')
        LOG.debug('Response: %s\n%s', '=' * 30, content)
        if 'return_code' in content:
            data = xml2dict(content)
            if data['return_code'] == FAIL:
                raise WechatPayError(data['return_msg'], resp=data)
            if 'result_code' in data and data['result_code'] == FAIL:
                raise WechatPayError(data['err_code_des'], resp=data)
            return data
        return content

    def reply(self, msg, ok=True):
        code = SUCCESS if ok else FAIL
        return dict2xml(dict(return_code=code, return_msg=msg))

    def unified_order(self, **data):
        """
        统一下单
        out_trade_no、body、total_fee、trade_type、spbill_create_ip必填
        app_id, mchid, nonce_str自动填写
        """
        url = self.PAY_HOST + '/pay/unifiedorder'

        # 必填参数
        if 'out_trade_no' not in data:
            raise WechatPayError('缺少统一支付接口必填参数out_trade_no')
        if 'body' not in data:
            raise WechatPayError('缺少统一支付接口必填参数body')
        if 'total_fee' not in data:
            raise WechatPayError('缺少统一支付接口必填参数total_fee')
        if 'trade_type' not in data:
            raise WechatPayError('缺少统一支付接口必填参数trade_type')
        if 'spbill_create_ip' not in data:
            raise WechatPayError('缺少统一支付接口必填参数spbill_create_ip')

        # 关联参数
        if data['trade_type'] == 'JSAPI' and 'openid' not in data:
            raise WechatPayError('trade_type为JSAPI时，openid为必填参数')
        if data['trade_type'] == 'NATIVE' and 'product_id' not in data:
            raise WechatPayError('trade_type为NATIVE时，product_id为必填参数')

        data.setdefault('notify_url', self.notify_url)

        raw = self._fetch(url, data)
        return raw

    def order_jsapi(self, **kwargs):
        """
        生成给JavaScript调用的数据
        详细规则参考 https://pay.weixin.qq.com/wiki/doc/api/jsapi.php?chapter=7_7&index=6
        """
        kwargs.setdefault('trade_type', 'JSAPI')
        raw = self.unified_order(**kwargs)
        package = 'prepay_id=%s' % raw['prepay_id']
        raw = dict(appId=self.app_id, timeStamp=self.timestamp,
                   nonceStr=self.nonce_str, package=package,
                   signType=SIGN_METHODS[self.sign_method])
        sign = self.sign(raw)
        raw['paySign'] = sign
        return raw

    def order_h5(self, **kwargs):
        kwargs.setdefault('trade_type', 'MWEB')
        return self.unified_order(**kwargs)

    def order_qr(self, **kwargs):
        kwargs.setdefault('trade_type', 'NATIVE')
        return self.unified_order(**kwargs)

    def qrcode_url(self, product_id, shorten=False):
        params = {
            'appid': self.app_id,
            'mch_id': self.mch_id,
            'product_id': product_id,
            'time_stamp': self.timestamp,
            'nonce_str': self.nonce_str,
        }
        params['sign'] = self.sign(params)
        text = ('weixin://wxpay/bizpayurl?sign=%(sign)s&appid=%(appid)s&mch_id=%(mch_id)s'
                '&product_id=%(product_id)s&time_stamp=%(time_stamp)s&nonce_str=%(nonce_str)s') % params
        if shorten:
            return self.qrcode_url_shorten(long_url=urlencode(text))
        return text

    def qrcode_url_shorten(self, **data):
        url = self.PAY_HOST + '/tools/shorturl'
        if 'long_url' not in data:
            raise WechatPayError('缺少转换短链接接口必填参数long_url')
        return self._fetch(url, data)['short_url']

    def order_query(self, **data):
        """
        订单查询
        out_trade_no, transaction_id至少填一个
        appid, mchid, nonce_str不需要填入
        """
        url = self.PAY_HOST + '/pay/orderquery'
        if 'out_trade_no' not in data and 'transaction_id' not in data:
            raise WechatPayError('订单查询接口中，out_trade_no、transaction_id至少填一个')
        return self._fetch(url, data)

    def close_order(self, out_trade_no, **data):
        """
        关闭订单
        out_trade_no必填
        appid, mchid, nonce_str不需要填入
        """
        url = self.PAY_HOST + '/pay/closeorder'
        data.setdefault('out_trade_no', out_trade_no)
        return self._fetch(url, data)

    def refund(self, **data):
        """
        申请退款
        out_trade_no、transaction_id至少填一个且
        out_refund_no、total_fee、refund_fee、op_user_id为必填参数
        appid、mchid、nonce_str不需要填入
        """
        url = self.PAY_HOST + '/secapi/pay/refund'
        if not self.key or not self.cert:
            raise WechatPayError('退款申请接口需要双向证书')
        if 'out_trade_no' not in data and 'transaction_id' not in data:
            raise WechatPayError('退款申请接口中，out_trade_no、transaction_id至少填一个')
        if 'out_refund_no' not in data:
            raise WechatPayError('退款申请接口中，缺少必填参数out_refund_no')
        if 'total_fee' not in data:
            raise WechatPayError('退款申请接口中，缺少必填参数total_fee')
        if 'refund_fee' not in data:
            raise WechatPayError('退款申请接口中，缺少必填参数refund_fee')
        return self._fetch(url, data, True)

    def refund_query(self, **data):
        """
        查询退款
        提交退款申请后，通过调用该接口查询退款状态。退款有一定延时，
        用零钱支付的退款20分钟内到账，银行卡支付的退款3个工作日后重新查询退款状态。
        out_refund_no、out_trade_no、transaction_id、refund_id四个参数必填一个
        appid、mchid、nonce_str不需要填入
        """
        url = self.PAY_HOST + '/pay/refundquery'
        if 'out_refund_no' not in data and 'out_trade_no' not in data \
                and 'transaction_id' not in data and 'refund_id' not in data:
            raise WechatPayError('退款查询接口中，out_refund_no、out_trade_no、transaction_id、refund_id四个参数必填一个')
        return self._fetch(url, data)

    def download_bill(self, bill_date, bill_type='ALL', **data):
        """
        下载对账单
        bill_date、bill_type为必填参数
        appid、mchid、nonce_str不需要填入
        """
        url = self.PAY_HOST + '/pay/downloadbill'
        data.setdefault('bill_date', bill_date)
        data.setdefault('bill_type', bill_type)
        if 'bill_date' not in data:
            raise WechatPayError('对账单接口中，缺少必填参数bill_date')
        return self._fetch(url, data)

    def pay_individual(self, **data):
        """
        企业付款到零钱
        """
        url = self.PAY_HOST + '/mmpaymkttransfers/promotion/transfers'
        if not self.key or not self.cert:
            raise WechatPayError('企业接口需要双向证书')
        if 'partner_trade_no' not in data:
            raise WechatPayError('企业付款接口中, 缺少必要的参数partner_trade_no')
        if 'openid' not in data:
            raise WechatPayError('企业付款接口中，缺少必填参数openid')
        if 'amount' not in data:
            raise WechatPayError('企业付款接口中，缺少必填参数amount')
        if 'desc' not in data:
            raise WechatPayError('企业付款接口中，缺少必填参数desc')
        data.setdefault('check_name', 'NO_CHECK')
        return self._fetch_pay(url, data, True)

    def pay_individual_to_card(self, **data):
        """
        企业付款到银行卡
        """
        url = self.PAY_HOST + '/mmpaysptrans/pay_bank'
        if not self.key or not self.cert:
            raise WechatPayError('企业接口需要双向证书')
        if 'partner_trade_no' not in data:
            raise WechatPayError('企业付款接口中, 缺少必要的参数partner_trade_no')
        if 'enc_bank_no' not in data:
            raise WechatPayError('企业付款接口中，缺少必填参数enc_bank_no')
        if 'enc_true_name' not in data:
            raise WechatPayError('企业付款接口中，缺少必填参数enc_true_name')
        if 'bank_code' not in data:
            raise WechatPayError('企业付款接口中，缺少必填参数bank_code')
        if 'amount' not in data:
            raise WechatPayError('企业付款接口中，缺少必填参数amount')
        return self._fetch(url, data, True, False)

    def pay_individual_bank_query(self, **data):
        """
        企业付款到银行卡查询
        """
        url = self.PAY_HOST + '/mmpaysptrans/query_bank'
        if not self.key or not self.cert:
            raise WechatPayError('企业接口需要双向证书')
        if 'partner_trade_no' not in data:
            raise WechatPayError('企业付款接口中, 缺少必要的参数partner_trade_no')
        return self._fetch(url, data, True, False)

    def pay_individual_query(self, **data):
        """
        企业付款到零钱查询
        """
        url = self.PAY_HOST + '/mmpaymkttransfers/gettransferinfo'
        if not self.key or not self.cert:
            raise WechatPayError('企业接口需要双向证书')
        if 'partner_trade_no' not in data:
            raise WechatPayError('企业付款接口中, 缺少必要的参数partner_trade_no')
        return self._fetch(url, data, True)

    def _fetch_pay(self, url, data, use_cert=False):
        data.setdefault('mch_appid', self.app_id)
        data.setdefault('mchid', self.mch_id)
        data.setdefault('nonce_str', self.nonce_str)
        data.setdefault('sign', self.sign(data))
        if use_cert:
            resp = self.sess.post(url, data=dict2xml(data), cert=(self.cert, self.key))
        else:
            resp = self.sess.post(url, data=dict2xml(data))
        content = resp.content.decode('utf-8')
        if 'return_code' in content:
            data = xml2dict(content)
            if data['return_code'] == FAIL:
                raise WechatPayError(data['return_msg'])
            if 'result_code' in content and data['result_code'] == FAIL:
                raise WechatPayError(data['err_code_des'])
            return data
        return content
