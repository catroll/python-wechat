import json
import os

from flask import (Blueprint, Response, current_app, redirect, render_template,
                   request, url_for)
from wechat.base import random_string

app = Blueprint('mp', __name__)


@app.route('/wechat.share.action')
def view_wechat_share():
    """
    1. access_token
    2. jsapi_ticket
    3. jsapi_ticket + noncestr + timestamp + url => signature
    """
    sign = current_app.wechat.mp.jsapi_sign(url=request.url)
    current_app.logger.debug('jsapi sign: %r', sign)
    data = {
        # 开启调试模式，调用的所有api的返回值会在客户端alert出来，
        # 若要查看传入的参数，可以在pc端打开，参数信息会通过log打出，仅在pc端时才会打印。
        'debug': True,
        'appId': sign['appId'],
        'timestamp': sign['timestamp'],
        'nonceStr': sign['noncestr'],
        'signature': sign['sign'],
        'jsApiList': ['updateAppMessageShareData', 'updateTimelineShareData'],
    }
    current_app.logger.debug('wx config: %r', data)
    return render_template('web_wechat_share.html', bridge_params=json.dumps(data))


@app.route('/wechat.mp.login.action')
def view_wechat_mp_login():
    # 扫描二维码，关注公众号
    # img_url = 'https://login.weixin.qq.com/qrcode/gbXPB3iomg=='
    scene = 'mp-login-' + random_string(5)
    expire_time = 3600
    data = {"expire_seconds": expire_time, "action_name": "QR_STR_SCENE", "action_info": {"scene": {"scene_str": scene}}}
    try:
        # raise Exception('test error.png')
        result = current_app.wechat.mp.request('/qrcode/create', json=data)
        assert 'ticket' in result
        img_url = 'https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=' + result['ticket']
    except Exception as error:
        current_app.logger.exception(error)
        # 错误图片来源：英文维基百科
        # https://upload.wikimedia.org/wikipedia/commons/thumb/2/20/Ireland_road_sign_W_120.svg/480px-Ireland_road_sign_W_120.svg.png
        img_url = url_for('static', filename='img/error.png')
    return render_template('web_wechat_mp_qr.html', img_url=img_url, scene=scene)


@app.route('/wechat.mp.login.progress.action')
def view_wechat_mp_login_progress():
    scene = request.args.get('scene', '')
    if not scene:
        return '0'
    path = '/tmp/.gatsby-' + scene
    return '1' if os.path.exists(path) else '0'
