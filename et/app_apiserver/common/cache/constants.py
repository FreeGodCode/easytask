import random


class BaseCacheTTL(object):
    """
    缓存有效期
    为防止缓存雪崩，在设置缓存有效期时采用设置不同有效期的方案
    通过增加随机值实现
    """
    TTL = 0  # 由子类设置
    MAX_DELTA = 10 * 60  # 随机的增量上限

    @classmethod
    def get_val(cls):
        return cls.TTL + random.randrange(0, cls.MAX_DELTA)


class UserInfoCacheTTL(BaseCacheTTL):
    """
    用户资料数据缓存时间, 秒
    """
    TTL = 1440 * 60


class TasksCacheTTL(BaseCacheTTL):
    """
    任务列表数据缓存时间, 秒
    """
    TTL = 30 * 60


class TasksDetailCacheTTL(BaseCacheTTL):
    """
    任务详情数据缓存时间, 秒
    """
    TTL = 30 * 60


class UpdateApiCacheTTL(BaseCacheTTL):
    """
    app更新数据缓存时间, 秒
    """
    TTL = 7680 * 60


class UserApprenticeCacheTTL(BaseCacheTTL):
    """
    用户收徒页面数据缓存时间, 秒
    """
    TTL = 1440 * 60


class UserApprenticeDetailCacheTTL(BaseCacheTTL):
    """
    用户收徒详情数据缓存时间, 秒
    """
    TTL = 1440 * 60


class UserCenterCacheTTL(BaseCacheTTL):
    """
    用户个人中心数据缓存时间, 秒
    """
    TTL = 1440 * 60


class UserEarningsCacheTTL(BaseCacheTTL):
    """
    用户个人收益数据缓存时间, 秒
    """
    TTL = 30 * 60


class UserExtendCacheTTL(BaseCacheTTL):
    """
    用户任务数据缓存时间, 秒
    """
    TTL = 30 * 60


class UserTasksCacheTTL(BaseCacheTTL):
    """
    用户任务数据缓存时间, 秒
    """
    TTL = 30 * 60


class UserWithdrawCacheTTL(BaseCacheTTL):
    """
    用户提现数据缓存时间, 秒
    """
    TTL = 30 * 60


class UserTaskEarningsCacheTTl(BaseCacheTTL):
    """
    用户提现数据缓存时间, 秒
    """
    TTL = 30 * 60
