import json

from flask import Blueprint, Response, current_app, render_template, request

app = Blueprint('share', __name__)


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
