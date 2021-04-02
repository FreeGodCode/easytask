

class DefaultConfig(object):
    """
    Flask默认配置
    """

    # JWT
    JWT_SECRET = 'TPmi4aLWRbyVq8zu9v82dWYW17/z+UvRnYTt4P6fAXA'
    JWT_EXPIRY_HOURS = 2
    JWT_REFRESH_DAYS = 14

    # hashids
    HASHIDS_SECRET = 'TPmi4aLWRbyVq8zu9v82dWYW17/z+UvRnYTt4P6fAXA'

    # redis配置
    REDIS_URL = 'redis://127.0.0.1:6379/0'

    # 阿里云实名配置
    ALIAPPCODE = '06fdc8950e974fc88102f699c621b70b'

    # 日志
    LOGGING_LEVEL = 'DEBUG'
    LOGGING_FILE_DIR = 'log'
    LOGGING_FILE_MAX_BYTES = 300 * 1024 * 1024
    LOGGING_FILE_BACKUP = 10  # 备份
