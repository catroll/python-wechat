from flask import Flask, Response, request
from wechat.msg import WechatMsg

app = Flask(__name__)
msg = WechatMsg('e10adc3949ba59abbe56e057f20f883e', None, 0)


@app.route('/', methods=['GET', 'POST'])
def view_func():
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    if not msg.validate(signature, timestamp, nonce):
        return 'signature failed', 400
    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        return echostr

    try:
        ret = msg.parse(request.data)
    except ValueError:
        return 'invalid', 400

    func = None
    _registry = msg._registry.get(ret['type'], dict())
    if ret['type'] == 'text':
        if ret['content'] in _registry:
            func = _registry[ret['content']]
    elif ret['type'] == 'event':
        if ret['event'].lower() in _registry:
            func = _registry[ret['event'].lower()]

    if func is None and '*' in _registry:
        func = _registry['*']
    if func is None and '*' in msg._registry:
        func = msg._registry.get('*', dict()).get('*')

    text = ''
    if func is None:
        text = 'failed'

    if callable(func):
        text = func(**ret)

    content = ''
    if isinstance(text, basestring):
        if text:
            content = msg.reply(
                username=ret['sender'],
                sender=ret['receiver'],
                content=text,
            )
    elif isinstance(text, dict):
        text.setdefault('username', ret['sender'])
        text.setdefault('sender', ret['receiver'])
        content = msg.reply(**text)

    return Response(content, content_type='text/xml; charset=utf-8')


@msg.all
def all_test(**kwargs):
    print kwargs
    # 或者直接返回
    # return 'all'
    return msg.reply(
        kwargs['sender'], sender=kwargs['receiver'], content='all'
    )


@msg.text()
def hello(**kwargs):
    return dict(content='hello too!', type='text')


@msg.text('world')
def world(**kwargs):
    return msg.reply(
        kwargs['sender'], sender=kwargs['receiver'], content='hello world!'
    )


@msg.image
def image(**kwargs):
    print kwargs
    return ''


@msg.subscribe
def subscribe(**kwargs):
    print kwargs
    return ''


@msg.unsubscribe
def unsubscribe(**kwargs):
    print kwargs
    return ''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9900)
