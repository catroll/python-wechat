import logging
import os

from flask import (Blueprint, Flask, render_template, send_from_directory,
                   url_for)

import views
from wechat import Wechat

HOST = '0.0.0.0'
PORT = 19888

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)
app.config.from_pyfile('settings.py', silent=True)
app.logger.setLevel(logging.DEBUG)
app.app_context().push()

# Attempted to generate a URL without the application context being pushed.
# This has to be executed when application context is available.
# app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.route('/MP_verify_<verify_str>.txt', methods=['GET'])
def wechat_verify(verify_str):
    return verify_str


@app.route('/')
def index():
    app.logger.debug('welcome')
    return render_template('index.html', links=[
        url_for('pay.view_wechat_demo_test'),
        url_for('pay.view_wechat_demo'),
        url_for('pay.view_wechat_jsbridge'),
        url_for('pay.view_wechat_show_bridge'),
        url_for('mp.view_wechat_share'),
        url_for('mp.view_wechat_mp_login'),
        url_for('mp.view_wechat_mp_login_progress'),
        url_for('msg.view_wechat_receive_msg'),
    ])


def main():
    app.wechat = Wechat(app, debug=True)
    views.initialize()
    app.config['WXN_NOTIFY_URL'] = url_for('pay.view_wechat_notify', _external=True)
    app.run(host=HOST, port=PORT, debug=True)


if __name__ == '__main__':
    main()
