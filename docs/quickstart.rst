快速开始
==============

安装
----

使用pip

.. code-block:: python

    sudo pip install python-wechat

使用easy_install

.. code-block:: python

    sudo easy_install python-wechat

安装开发版本

.. code-block:: python

    sudo pip install git+https://github.com/catroll/python-wechat@dev

功能
----

-  微信登陆
-  微信支付
-  微信公众号
-  微信消息

用法
----

异常
~~~~~~~~~~

父异常类名为 ``WechatError`` 子异常类名分别为 ``WechatAuthError``
``WechatPayError`` ``WechatMPError`` ``WechatMsgError``

参数
~~~~~~~~~~

-  ``WXN_TOKEN`` 必填，微信主动推送消息的TOKEN
-  ``WXN_SENDER`` 选填，微信发送消息的发送者
-  ``WXN_EXPIRES_IN`` 选填，微信推送消息的有效时间
-  ``WXN_MCH_ID`` 必填，微信商户ID，纯数字
-  ``WXN_MCH_KEY`` 必填，微信商户KEY
-  ``WXN_NOTIFY_URL`` 必填，微信回调地址
-  ``WXN_MCH_KEY_FILE`` 可选，如果需要用退款等需要证书的api，必选
-  ``WXN_MCH_CERT_FILE`` 可选
-  ``WXN_APP_ID`` 必填，微信公众号appid
-  ``WXN_APP_SECRET`` 必填，微信公众号appkey

上面参数的必填都是根据具体开启的功能有关,
如果你只需要微信登陆，就只要选择 ``WXN_APP_ID`` ``WXN_APP_SECRET``

-  微信消息

   -  ``WXN_TOKEN``
   -  ``WXN_SENDER``
   -  ``WXN_EXPIRES_IN``

-  微信登陆

   -  ``WXN_APP_ID``
   -  ``WXN_APP_SECRET``

-  微信公众平台

   -  ``WXN_APP_ID``
   -  ``WXN_APP_SECRET``

-  微信支付

   -  ``WXN_APP_ID``
   -  ``WXN_MCH_ID``
   -  ``WXN_MCH_KEY``
   -  ``WXN_NOTIFY_URL``
   -  ``WXN_MCH_KEY_FILE``
   -  ``WXN_MCH_CERT_FILE``

初始化
~~~~~~~

如果使用flask

.. code-block:: python

    # -*- coding: utf-8 -*-


    from datetime import datetime, timedelta
    from flask import Flask, jsonify, request, url_for
    from wechat import Wechat, WechatError


    app = Flask(__name__)
    app.debug = True


    # 具体导入配
    # 根据需求导入仅供参考
    app.config.fromobject(dict(WXN_APP_ID='', WXN_APP_SECRET=''))


    # 初始化微信
    wechat = Wechat()
    wechat.init_app(app)
    # 或者
    # wechat = Wechat(app)

如果不使用flask

.. code-block:: python

    # 根据需求导入仅供参考
    config = dict(WXN_APP_ID='', WXN_APP_SECRET='')
    wechat = Wechat(config)

微信消息
~~~~~~~~

如果使用django，添加视图函数为

.. code-block:: python

    url(r'^/$', wechat.django_view_func(), name='index'),

如果为flask，添加视图函数为

.. code-block:: python

    app.add_url_rule("/", view_func=wechat.view_func)

.. code-block:: python

    @wechat.all
    def all(**kwargs):
        """
        监听所有没有更特殊的事件
        """
        return wechat.reply(kwargs['sender'], sender=kwargs['receiver'], content='all')


    @wechat.text()
    def hello(**kwargs):
        """
        监听所有文本消息
        """
        return "hello too"


    @wechat.text("help")
    def world(**kwargs):
        """
        监听help消息
        """
        return dict(content="hello world!")


    @wechat.subscribe
    def subscribe(**kwargs):
        """
        监听订阅消息
        """
        print kwargs
        return "欢迎订阅我们的公众号"

微信登陆
~~~~~~~~

.. code-block:: python

    @app.route("/login")
    def login():
        """登陆跳转地址"""
        openid = request.cookies.get("openid")
        next = request.args.get("next") or request.referrer or "/",
        if openid:
            return redirect(next)

        callback = url_for("authorized", next=next, _external=True)
        url = wechat.authorize(callback, "snsapi_base")
        return redirect(url)


    @app.route("/authorized")
    def authorized():
        """登陆回调函数"""
        code = request.args.get("code")
        if not code:
            return "ERR_INVALID_CODE", 400
        next = request.args.get("next", "/")
        data = wechat.access_token(code)
        openid = data.openid
        resp = redirect(next)
        expires = datetime.now() + timedelta(days=1)
        resp.set_cookie("openid", openid, expires=expires)
        return resp

微信支付
~~~~~~~~

注意: 微信网页支付的timestamp参数必须为字符串

.. code-block:: python


    @app.route("/pay/jsapi")
    def pay_jsapi():
        """微信网页支付请求发起"""
        try:
            out_trade_no = wechat.nonce_str
            raw = wechat.jsapi(openid="openid", body=u"测试", out_trade_no=out_trade_no, total_fee=1)
            return jsonify(raw)
        except WechatError, e:
            print e.message
            return e.message, 400


    @app.route("/pay/notify")
    def pay_notify():
        """
        微信异步通知
        """
        data = wechat.to_dict(request.data)
        if not wechat.check(data):
            return wechat.reply("签名验证失败", False)
        # 处理业务逻辑
        return wechat.reply("OK", True)


    if __name__ == '__main__':
        app.run(host="0.0.0.0", port=9900)

微信公众号
~~~~~~~~~~

**注意**:
如果使用分布式，需要自己实现\ ``access_token``\ 跟\ ``jsapi_ticket``\ 函数

``access_token``\ 默认保存在\ ``~/.access_token``
``jsapi_ticket``\ 默认保存在\ ``~/.jsapi_ticket``

默认在(HOME)目录下面，如果需要更改到指定的目录，可以导入库之后修改，如下

.. code-block:: python

    import wechat

    DEFAULT_DIR = "/tmp"

获取公众号唯一凭证

.. code-block:: python

    wechat.access_token

获取ticket

.. code-block:: python

    wechat.jsapi_ticket

创建临时qrcode

.. code-block:: python

    data = wechat.qrcode_create(123, 30)
    print wechat.qrcode_show(data.ticket)

创建永久性qrcode

.. code-block:: python

    # scene_id类型
    wechat.qrcode_create_limit(123)
    # scene_str类型
    wechat.qrcode_create_limit("456")

长链接变短链接

.. code-block:: python

    wechat.shorturl("http://example.com/test")

