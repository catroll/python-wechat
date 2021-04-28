import logging

from wechat.mp import WechatMP

import settings

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s #%(lineno)s %(message)s')
logging.getLogger('urllib3').setLevel(logging.DEBUG)

c = WechatMP(settings.WXN_APP_ID, settings.WXN_APP_SECRET, debug=True)
data = {"expire_seconds": 604800, "action_name": "QR_SCENE", "action_info": {"scene": {"scene_id": 123}}}
resp = c.request('/qrcode/create', json=data)

print()
print('=' * 60)
print()
print(resp)
print()
