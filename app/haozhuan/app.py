import sys
from flask import Flask
sys.path.append("..")

from haozhuan.config import global_config


def create_flask_app(config, enable_config_file=False):
    """
    创建Flask应用
    :param config: 配置信息对象
    :param enable_config_file: 是否允许运行环境中的配置文件覆盖已加载的配置信息
    :return: Flask应用
    """
    app = Flask(__name__)
    app.config.from_object(config)
    if enable_config_file:
        sys.path.append('..')

        from utils import constants
        app.config.from_envvar(constants.GLOBAL_SETTING_ENV_NAME, silent=True)

    return app

def create_app(config, enable_config_file=False):
    """
    创建应用
    :param config: 配置信息对象
    :param enable_config_file: 是否允许运行环境中的配置文件覆盖已加载的配置信息
    :return: 应用
    """
    app = create_flask_app(config, enable_config_file)

    # 注册url转换器
    sys.path.append('..')
    from utils.converters import register_converters
    register_converters(app)

    # Redis配置
    from flask_redis import FlaskRedis
    app.config['REDIS_URL'] = global_config.getRaw('redis', 'REDIS_URL')
    app.redis_cli = FlaskRedis(app)

    # 配置限流器
    from utils.limiter import limiter as lmt
    lmt.init_app(app)

    # 添加请求钩子
    from utils.middlewares import jwt_authentication
    app.before_request(jwt_authentication)

    # 配置日志
    from utils.logging import create_logger
    create_logger(app)

    # 注册用户模块蓝图
    from haozhuan.resources.user import user_bp
    app.register_blueprint(user_bp)

    return app

