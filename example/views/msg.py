from flask import Blueprint, Response, current_app, request

app = Blueprint('msg', __name__)


@app.route('/wechat.receive.msg.action', methods=['GET', 'POST'])
def view_wechat_receive_msg():
    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    if not current_app.wechat.msg.validate(signature, timestamp, nonce):
        return 'signature failed', 400
    if request.method == 'GET':
        echostr = request.args.get('echostr', '')
        return echostr

    try:
        ret = current_app.wechat.msg.parse(request.data)
    except ValueError:
        return 'invalid', 400

    func = None
    _registry = current_app.wechat.msg._registry.get(ret['type'], dict())
    if ret['type'] == 'text':
        if ret['content'] in _registry:
            func = _registry[ret['content']]
    elif ret['type'] == 'event':
        if ret['event'].lower() in _registry:
            func = _registry[ret['event'].lower()]

    if func is None and '*' in _registry:
        func = _registry['*']
    if func is None and '*' in current_app.wechat.msg._registry:
        func = current_app.wechat.msg._registry.get('*', dict()).get('*')

    text = ''
    if func is None:
        text = 'failed'

    if callable(func):
        text = func(**ret)

    content = ''
    if isinstance(text, basestring):
        if text:
            content = current_app.wechat.msg.reply(
                username=ret['sender'],
                sender=ret['receiver'],
                content=text,
            )
    elif isinstance(text, dict):
        text.setdefault('username', ret['sender'])
        text.setdefault('sender', ret['receiver'])
        content = current_app.wechat.msg.reply(**text)

    return Response(content, content_type='text/xml; charset=utf-8')


@current_app.wechat.msg.all
def all_test(**kwargs):
    current_app.logger.debug(kwargs)
    # 或者直接返回
    # return 'all'
    return current_app.wechat.msg.reply(
        kwargs['sender'], sender=kwargs['receiver'], content='all'
    )


@current_app.wechat.msg.text()
def hello(**kwargs):
    return dict(content='hello too!', type='text')


@current_app.wechat.msg.text('world')
def world(**kwargs):
    return current_app.wechat.msg.reply(
        kwargs['sender'], sender=kwargs['receiver'], content='hello world!'
    )


@current_app.wechat.msg.image
def image(**kwargs):
    current_app.logger.debug(kwargs)
    return ''


@current_app.wechat.msg.subscribe
def subscribe(**kwargs):
    current_app.logger.debug(kwargs)
    return ''


@current_app.wechat.msg.unsubscribe
def unsubscribe(**kwargs):
    current_app.logger.debug(kwargs)
    return ''
