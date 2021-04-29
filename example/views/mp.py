from flask import (Blueprint, Response, current_app, redirect, render_template,
                   request, url_for)
from wechat.base import random_string

app = Blueprint('mp', __name__)
SCENE_PREFIX = 'mp-login-'


@app.route('/wechat.mp.follow.action')
def view_wechat_mp_follow():
    # 扫描二维码，关注公众号
    # img_url = 'https://login.weixin.qq.com/qrcode/gbXPB3iomg=='
    scene = SCENE_PREFIX + random_string(5)
    expire_time = 300
    data = {"expire_seconds": expire_time, "action_name": "QR_SCENE", "action_info": {"scene": {"scene_str": scene}}}
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
    return render_template('web_wechat_mp_qr.html', img_url=img_url)
