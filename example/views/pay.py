"""
微信支付测试流程

1. 打开 http://www.example.com/wechat.demo.action
2. 点击 “立即购买”
3. 跳转到：http://www.example.com/wechat.pay.action
    如果有用户 openid，直接跳到第 6 步
4. 跳转到微信授权页面，获取 access_token（含 openid）
5. 回跳到之前的支付页面
6. 生成订单
7. 调用微信下单接口
8. 如果是 H5，跳转到微信支付页面，触发微信支付
   如果是 JSAPI，跳转到自定义的支付页面，JS 触发微信支付
"""

import base64
import json
from datetime import datetime, timedelta

from flask import (Blueprint, Response, current_app, redirect, render_template,
                   request, url_for)
from wechat.base import random_string

app = Blueprint('pay', __name__)


@app.route('/wechat.auth.action')
def view_wechat_demo_test():
    # 获取当前微信账号的 openid
    openid = request.cookies.get(current_app.config.get('WXN_ID'))
    if not openid:
        next_step = base64.b64encode(request.url.encode('utf-8')).decode('ascii')
        redirect_uri = url_for('pay.view_wechat_auth_redirect', ns=next_step, _external=True)
        authorize_uri = current_app.wechat.auth.authorize(redirect_uri)
        current_app.logger.info('goto %s', authorize_uri)
        return redirect(authorize_uri)
    return openid


@app.route('/wechat.jsbridge.action')
def view_wechat_jsbridge():
    """
    页面来自：https://www.cnblogs.com/txw1958/p/WeixinJSBridge-api.html
    """
    return render_template('web_wechat_bridge_test.html')


@app.route('/wechat.demo.action')
def view_wechat_demo():
    """
    HTML
    用户点击支付，跳转到 wechat_pay
    """
    return render_template('web_wechat_demo.html')


@app.route('/wechat.pay.action', methods=['POST'])
def view_wechat_pay():
    order_no = random_string(16)

    current_app.logger.debug('UA: %r', request.user_agent.string)
    is_wechat = request.user_agent.string.find('MicroMessenger') != -1
    current_app.logger.debug('POST data: %r', request.form)

    ### 如果没有 openid 先获取之 ###
    openid = request.cookies.get(current_app.config.get('WXN_ID'))
    if not openid and is_wechat:
        next_step = base64.b64encode(request.url.encode('utf-8')).decode('ascii')
        redirect_uri = url_for('pay.view_wechat_auth_redirect', ns=next_step, _external=True)
        authorize_uri = current_app.wechat.auth.authorize(redirect_uri, state=order_no)
        current_app.logger.info('goto %s', authorize_uri)
        return redirect(authorize_uri)

    ### 生成订单 ###
    fake_order = {
        'order_no': order_no,
        'amount': int(float(request.form['amount']) * 100),  # 单位：分
    }

    #### 微信下单 ###
    # 外网可访问地址，不能带任何参数
    notify_url = url_for('pay.view_wechat_notify', _external=True)
    params = {
        'out_trade_no': fake_order['order_no'],
        'body': '微信支付接口测试',
        'total_fee': fake_order['amount'],
        'spbill_create_ip': request.remote_addr,
    }
    if is_wechat:
        params['openid'] = openid
        data = current_app.wechat.pay.order_jsapi(**params)
        current_app.logger.debug('open bridge, params: %s', data)
        return render_template('web_wechat_bridge_pay.html', bridge_params=json.dumps(data))

    data = current_app.wechat.pay.order_h5(**params)
    return redirect(data['mweb'])


@app.route('/wechat.showBridge.action')
def view_wechat_show_bridge():
    params = request.args.get('params', '')
    if not params:
        return 'need params (json)'
    return render_template('web_wechat_bridge_pay.html', bridge_params=json.dumps(data))


@app.route('/wechat.auth.redirect.action')
def view_wechat_auth_redirect():
    """
    如果用户同意授权，页面将跳转至
    redirect_uri/?code=CODE&state=STATE

    code说明：
    code作为换取access_token的票据，每次用户授权带上的code将不一样，code只能使用一次，5分钟未被使用自动过期。

    code 写到用户信息中
    """
    wxn_openid_code = request.args.get('code', '')
    wxn_openid_state = request.args.get('state', '')
    current_app.logger.info('wechat.auth.redirect: code %r, state %r',
                    wxn_openid_code, wxn_openid_state)

    token = current_app.wechat.auth.access_token(wxn_openid_code)

    next_step = request.args.get('ns', '')
    if next_step:
        url = base64.b64decode(next_step).decode('utf-8')
        resp = redirect(url)
    else:
        resp = Response('', 200, mimetype="text/html")

    expires = datetime.now() + timedelta(days=1)
    resp.set_cookie(current_app.config.get('WXN_ID'), token['openid'], expires=expires)

    return resp


@app.route('/wechat.pay.notify.action', methods=['POST'])
def view_wechat_notify():
    """
    15s/15s/30s/3m/10m/20m/30m/30m/30m/60m/3h/3h/3h/6h/6h - 总计 24h4m
    """
    current_app.logger.debug(request.data)
    from wechat.base import xml2dict, dict2xml
    data = xml2dict(request.data)
    current_app.logger.info('wechat.pay.notify: %r', data)
    return dict2xml({'return_code': 'SUCCESS', 'return_msg': 'OK'})
