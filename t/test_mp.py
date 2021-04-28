import logging

from wechat.mp import WechatMP, WechatError

import settings

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s #%(lineno)s %(message)s')
logging.getLogger('urllib3').setLevel(logging.DEBUG)

mp = WechatMP(settings.WXN_APP_ID, settings.WXN_APP_SECRET, debug=True)
data = {"expire_seconds": 604800, "action_name": "QR_SCENE", "action_info": {"scene": {"scene_id": 123}}}
resp = mp.request('/qrcode/create', json=data)

print()
print('=' * 60)
print()
print(resp)
print()

# 获取菜单
try:
    print mp.menu_get()
except WechatError:
    pass

# 创建菜单
data = [
    {
        "type": "view",
        "name": "测试",
        "url": "http://code.show/",
    },
]
print mp.menu_create(data)

# 删除菜单
print mp.menu_delete()

# 短连接
print mp.shorturl("http://baidu.com").short_url

# 创建带参数的零时qrcode, 30秒过期
data = mp.qrcode_create(123456, 30)
print mp.qrcode_show(data.ticket)

# 创建带参数永久性qrcode
data = mp.qrcode_create_limit(123456)
print mp.qrcode_show(data.ticket)
