from django.conf.urls import url
from django.db import connection


def show_user(request, username):
    with connection.cursor() as cursor:
        # BAD -- Using string formatting
        cursor.execute("SELECT * FROM users WHERE username = '%s'" % username)
        user = cursor.fetchone()

        # GOOD -- Using parameters
        cursor.execute("SELECT * FROM users WHERE username = %s", username)
        user = cursor.fetchone()

        # BAD -- Manually quoting placeholder (%s)
        cursor.execute("SELECT * FROM users WHERE username = '%s'", username)
        user = cursor.fetchone()

urlpatterns = [url(r'^users/(?P<username>[^/]+)$', show_user)]

from flask import Flask
from flask import request
from django.utils.log import request_logger
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

@app.route('/bad1')
def bad1():
    name = request.args.get('name')
    app.logger.info('User name: ' + name) # Bad
    return 'bad1'

@app.route('/bad2')
def bad2():
    name = request.args.get('name')
    logging.info('User name: ' + name) # Bad
    return 'bad2'

@app.route('/bad3')
def bad3():
    name = request.args.get('name')
    request_logger.warn('User name: ' + name) # Bad
    return 'bad3'

@app.route('/bad4')
def bad4():
    name = request.args.get('name')
    logtest = logging.getLogger('test')
    logtest.debug('User name: ' + name) # Bad
    return 'bad4'

if __name__ == '__main__':
    app.debug = True
    handler = logging.FileHandler('log')
    app.logger.addHandler(handler)
    app.run()
