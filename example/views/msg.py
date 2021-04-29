import json

from flask import Blueprint, Response, current_app, request

app = Blueprint('msg', __name__)


@app.route('/wechat.receive.msg.action', methods=['GET', 'POST'])
def view_wechat_receive_msg():
    current_app.logger.debug(request.args)
    current_app.logger.debug(request.data)

    if request.method == 'GET':
        return request.args.get('echostr', '')

    signature = request.args.get('signature')
    timestamp = request.args.get('timestamp')
    nonce = request.args.get('nonce')
    current_app.logger.debug([signature, timestamp, nonce])
    is_test_mode = signature == timestamp == nonce == None
    if not is_test_mode and not current_app.wechat.msg.validate(signature, timestamp, nonce):
        return 'signature failed', 400

    try:
        data, result = current_app.wechat.msg.handle(request.data)
    except Exception as error:
        current_app.logger.exception(error)
        return 'invalid', 400
    current_app.logger.debug(data)
    current_app.logger.debug(result)

    content = ''
    if isinstance(result, str):
        if result.startswith('<xml>'):
            content = result
        elif result:
            current_app.logger.info('回复测试 str: %r', result)
            content = current_app.wechat.msg.reply(
                username=data['sender'],
                sender=data['receiver'],
                content=result,
            )
    elif isinstance(result, dict):
        current_app.logger.info('回复测试 dict: %r', result)
        result.setdefault('username', data['sender'])
        result.setdefault('sender', data['receiver'])
        content = current_app.wechat.msg.reply(**result)
    else:
        current_app.logger.warning('Error result: %r', result)

    return Response(content, content_type='text/xml; charset=utf-8')


def initialize():
    @current_app.wechat.msg.all
    def handle_all(**kwargs):
        current_app.logger.debug('all, %r', kwargs)
        return '我家住在桃花山'

    @current_app.wechat.msg.text
    def handle_text(**kwargs):
        current_app.logger.debug('text, %r', kwargs)
        return dict(content='hello too!', type='text')

    @current_app.wechat.msg.command('hello')
    def handle_hello(**kwargs):
        current_app.logger.debug('hello, %r', kwargs)
        return current_app.wechat.msg.reply(
            kwargs['sender'], sender=kwargs['receiver'], content='nice to meet you!'
        )

    @current_app.wechat.msg.image
    def handle_image(**kwargs):
        current_app.logger.debug('image, %r', kwargs)
        return ''

    @current_app.wechat.msg.subscribe
    def handle_subscribe(**kwargs):
        current_app.logger.debug('subscribe, %r', kwargs)
        if 'event_key' in kwargs and kwargs['event_key'].startswith('mp-login-'):
            path = '/tmp/.gatsby-' + kwargs['event_key']
            with open(path, 'w+') as fp:
                json.dump(kwargs, fp)
        return ''

    @current_app.wechat.msg.scan
    def handle_scan(**kwargs):
        current_app.logger.debug('scan, %r', kwargs)
        if 'event_key' in kwargs and kwargs['event_key'].startswith('mp-login-'):
            path = '/tmp/.gatsby-' + kwargs['event_key']
            with open(path, 'w+') as fp:
                json.dump(kwargs, fp)
        return ''

    @current_app.wechat.msg.unsubscribe
    def handle_unsubscribe(**kwargs):
        current_app.logger.debug('unsubscribe, %r', kwargs)
        return ''
