# 微信 SDK

提供微信登陆，公众号管理，微信支付，微信消息的全套功能

原项目地址: <https://github.com/zwczou/weixin-python>, 采用 BSD 协议分发。  

~~不过，看起来是不怎么维护的，所以，我自己 fork 了一份，自己维护。~~  
抱歉！原项目在维护中，我提交的 PR 很快就处理了。  
但是，我还是决定按照自己的意思维护一个新的版本：  

1. 项目名称从 weixin-python 改成 python-wechat
1. 版本从 0.5.7 修改成 2021.04.28
1. 放弃对 Python 2.x 的兼容，只支持 3.6 以上版本！！！
1. 放弃对原有版本的兼容

## 目录

* [安装](#安装)
* [功能](#功能)
* [异常](#异常)
* [用法](#用法)
	* [参数](#参数)
	* [初始化](#初始化)
	* [微信消息](#微信消息)
	* [微信登陆](#微信登陆)
	* [微信支付](#微信支付)
	* [微信公众号](#微信公众号)

## 安装

使用pip

`sudo pip install python-wechat`

使用easy_install

`sudo easy_install python-wechat`

## 功能

* 微信登陆
* 微信支付
* 微信公众号
* 微信消息

## 异常

父异常类名为 `WechatError`
子异常类名分别为 `WechatAuthError` `WechatPayError` `WechatMPError` `WechatMsgError`

## 用法

### 参数

* `WEIXIN_TOKEN` 必填，微信主动推送消息的TOKEN
* `WEIXIN_SENDER` 选填，微信发送消息的发送者
* `WEIXIN_EXPIRES_IN` 选填，微信推送消息的有效时间
* `WEIXIN_MCH_ID` 必填，微信商户ID，纯数字
* `WEIXIN_MCH_KEY` 必填，微信商户KEY
* `WEIXIN_NOTIFY_URL` 必填，微信回调地址
* `WEIXIN_MCH_KEY_FILE` 可选，如果需要用退款等需要证书的api，必选
* `WEIXIN_MCH_CERT_FILE` 可选
* `WEIXIN_APP_ID` 必填，微信公众号appid
* `WEIXIN_APP_SECRET` 必填，微信公众号appkey

上面参数的必填都是根据具体开启的功能有关, 如果你只需要微信登陆，就只要选择 `WEIXIN_APP_ID` `WEIXIN_APP_SECRET`

* 微信消息
   * `WEIXIN_TOKEN`
   * `WEIXIN_SENDER`
   * `WEIXIN_EXPIRES_IN`

* 微信登陆
    * `WEIXIN_APP_ID`
    * `WEIXIN_APP_SECRET`

* 微信公众平台
    * `WEIXIN_APP_ID`
    * `WEIXIN_APP_SECRET`

* 微信支付
    * `WEIXIN_APP_ID`
    * `WEIXIN_MCH_ID`
    * `WEIXIN_MCH_KEY`
    * `WEIXIN_NOTIFY_URL`
    * `WEIXIN_MCH_KEY_FILE`
    * `WEIXIN_MCH_CERT_FILE`

### 初始化

如果使用flask

```py
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from flask import Flask, jsonify, request, url_for
from wechat import Wechat, WechatError

app = Flask(__name__)
app.debug = True

# 具体导入配
# 根据需求导入仅供参考
app.config.from_object(dict(WEIXIN_APP_ID='', WEIXIN_APP_SECRET=''))

# 初始化微信
wechat = Wechat()
wechat.init_app(app)
# 或者
# wechat = Wechat(app)
```

如果不使用flask

```py
# 根据需求导入仅供参考
config = dict(WEIXIN_APP_ID='', WEIXIN_APP_SECRET='')
wechat = Wechat(config)
```

### 微信消息

如果使用django，添加视图函数为

```py
url(r'^/$', wechat.django_view_func(), name='index'),
```

如果为flask，添加视图函数为

```py
app.add_url_rule("/", view_func=wechat.view_func)
```


```py
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
```

### 微信登陆

```py
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
```

### 微信支付

注意: 微信网页支付的timestamp参数必须为字符串

```py
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


@app.route("/pay/notify, methods=['POST'])
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
```

### 微信公众号

**注意**: 如果使用分布式，需要自己实现`access_token`跟`jsapi_ticket`函数

`access_token`默认保存在`~/.access_token`
`jsapi_ticket`默认保存在`~/.jsapi_ticket`

默认在(HOME)目录下面，如果需要更改到指定的目录，可以导入库之后修改，如下

```py
import wechat

DEFAULT_DIR = "/tmp"
```

获取公众号唯一凭证

```py
wechat.access_token
```

获取ticket

```py
wechat.jsapi_ticket
```

创建临时qrcode

```py
data = wechat.qrcode_create(123, 30)
print wechat.qrcode_show(data.ticket)
```

创建永久性qrcode

```py
# scene_id类型
wechat.qrcode_create_limit(123)
# scene_str类型
wechat.qrcode_create_limit("456")
```

长链接变短链接

```py
wechat.shorturl("http://example.com/test")
```
