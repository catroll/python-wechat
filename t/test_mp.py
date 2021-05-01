import logging

from wechat.mp import WechatMP, WechatError

import settings

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s #%(lineno)s %(message)s')
logging.getLogger('urllib3').setLevel(logging.DEBUG)

mp = WechatMP(settings.WXN_APP_ID, settings.WXN_APP_SECRET, debug=True)


def create_qr():
    print('\n' + ('=' * 60) + '\n')

    data = {"expire_seconds": 604800, "action_name": "QR_SCENE", "action_info": {"scene": {"scene_id": 123}}}
    mp.request('/qrcode/create', json=data)

    print('\n' + ('=' * 60) + '\n')

    # 创建带参数的零时qrcode, 30秒过期
    data = mp.qrcode_create(123456, 30)
    mp.qrcode_show(data.ticket)

    print('\n' + ('=' * 60) + '\n')

    # 创建带参数永久性qrcode
    data = mp.qrcode_create_limit(123456)
    mp.qrcode_show(data.ticket)


def pull_menu():
    mp.menu_get()


def create_menu():
    # 创建菜单
    data = [
        {
            "type": "view",
            "name": "测试",
            "url": "http://code.show/",
        },
    ]
    mp.menu_create(data)


def delete_menu():
    # 删除菜单
    mp.menu_delete()


def short_link():
    # 短连接
    mp.shorturl("http://baidu.com")


def user_info():
    mp.user_info('oqYElwNfp2b53SXW6q7M1YRLKavP')


user_info()
# short_link()
# pull_menu()
