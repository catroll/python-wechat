from flask import Blueprint, Response, request

app = Blueprint('msg', __name__)


@app.route('/', methods=['GET', 'POST'])
def view_func():
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    if not app.wechat.msg.validate(signature, timestamp, nonce):
        return 'signature failed', 400
    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        return echostr

    try:
        ret = app.wechat.msg.parse(request.data)
    except ValueError:
        return 'invalid', 400

    func = None
    _registry = app.wechat.msg._registry.get(ret['type'], dict())
    if ret['type'] == 'text':
        if ret['content'] in _registry:
            func = _registry[ret['content']]
    elif ret['type'] == 'event':
        if ret['event'].lower() in _registry:
            func = _registry[ret['event'].lower()]

    if func is None and '*' in _registry:
        func = _registry['*']
    if func is None and '*' in app.wechat.msg._registry:
        func = app.wechat.msg._registry.get('*', dict()).get('*')

    text = ''
    if func is None:
        text = 'failed'

    if callable(func):
        text = func(**ret)

    content = ''
    if isinstance(text, basestring):
        if text:
            content = app.wechat.msg.reply(
                username=ret['sender'],
                sender=ret['receiver'],
                content=text,
            )
    elif isinstance(text, dict):
        text.setdefault('username', ret['sender'])
        text.setdefault('sender', ret['receiver'])
        content = app.wechat.msg.reply(**text)

    return Response(content, content_type='text/xml; charset=utf-8')



# @app.wechat.msg.all
# def all_test(**kwargs):
#     LOG.debug(kwargs)
#     # 或者直接返回
#     # return 'all'
#     return app.wechat.msg.reply(
#         kwargs['sender'], sender=kwargs['receiver'], content='all'
#     )


# @app.wechat.msg.text()
# def hello(**kwargs):
#     return dict(content='hello too!', type='text')


# @app.wechat.msg.text('world')
# def world(**kwargs):
#     return app.wechat.msg.reply(
#         kwargs['sender'], sender=kwargs['receiver'], content='hello world!'
#     )


# @app.wechat.msg.image
# def image(**kwargs):
#     LOG.debug(kwargs)
#     return ''


# @app.wechat.msg.subscribe
# def subscribe(**kwargs):
#     LOG.debug(kwargs)
#     return ''


# @app.wechat.msg.unsubscribe
# def unsubscribe(**kwargs):
#     LOG.debug(kwargs)
#     return ''
