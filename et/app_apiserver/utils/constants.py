# 配置文件环境变量名
GLOBAL_SETTING_ENV_NAME = 'haozhuan'

# 会员数据表
MEMBERS_TABLE = 'et_members'

# 任务数据表
TASKS_TABLE = 'et_tasks'

# 用户信息扩展表
ET_MEMBER_EXTEND = "et_member_extend"

# 任务订单表
ET_TASK_ORDERS = 'et_task_orders'

# 用户提现表
ET_MEMBER_WITHDRAWAL = 'et_member_withdrawal'

# 用户资金收益表
ET_MEMBER_EARNINGS = 'et_member_earnings'

# 用户分销关系表
ET_MEMBER_RELATIONS = 'et_member_relations'

# 运营后台分销配置
ET_DRP_CONFIG = 'et_drp_config'

# 运营后台APP发布版本列表
ET_APPS_PUB_HISTORY = 'et_apps_pub_history'

# 运营后台全局设置
ET_GLOBAL_CONFIG = 'et_global_config'

# 用户反馈表
ET_FEEDBACKS = 'et_feedbacks'

# 老用户数据表
ET_OLD_MEMBER = 'et_old_member'

# 活动数据表
ACTIVITY_REWARDS = "activity_rewards"

# 短信验证码有效期, 秒
SMS_VERIFICATION_CODE_EXPIRES = 5 * 60

# 图片验证码有效期, 秒
IMAGES_VERIFICATION_CODE_EXPIRES = 3 * 60

# 根据IP限制访问图片验证码频次
LIMIT_SMS_VERIFICATION_CODE_BY_IP = '10/minutes'

# 根据ip限制访问上传用户app版本接口
LIMIT_APP_VERSION__BY_IP = '10/minutes'

# 根据ip限制访问提现接口限制
LIMIT_TX_CODE_BY_IP = '20/minutes'
