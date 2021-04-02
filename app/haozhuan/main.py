import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))


from flask import jsonify
import logging
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from app import create_app
from settings.default import DefaultConfig



app = create_app(DefaultConfig, enable_config_file=True)


@app.route('/route_map')
def route_map():
    """
    主视图，返回所有视图网址
    """
    rules_iterator = app.url_map.iter_rules()
    return jsonify({rule.endpoint: rule.rule for rule in rules_iterator if rule.endpoint not in ('route_map', 'static')})

if __name__ == '__main__':
    
    app.run('0.0.0.0',port=5006,debug=True)


if __name__ != '__main__':
    # 如果不是直接运行，则将日志输出到 gunicorn 中
    gunicorn_logger = logging.getLogger('gunicorn.debug')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
