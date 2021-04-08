from flask import Blueprint
from flask_restplus import Api

user_bp = Blueprint('user', __name__)
user_api = Api(user_bp, title='好赚API列表')

from haozhuan.resources.user import loggin, tasks, user_authentication, bind_aliplay, generate_code, user_withdraw, \
    user_center, user_earnings, user_draw_task, user_add_task, user_apprentice, user_carry_money, update_api, \
    bind_wechat, app_config, noob_award, update_link, generate_qiniu_token, user_task_earnings, go_to_link, \
    user_opinion, \
    user_invitation, go_to_test

# 登录
user_api.add_resource(loggin.LoginView, '/login', endpoint='login')

# 获取所有任务列表
user_api.add_resource(tasks.TasksView, '/tasks', endpoint='tasks')

# 获取任务详情
user_api.add_resource(tasks.TasksDetailsView, '/tasks_detail', endpoint='tasks_detail')

# 获取用户任务列表
user_api.add_resource(tasks.UserTasksView, '/user_tasks', endpoint='user_tasks')

# 用户实名认证
user_api.add_resource(user_authentication.User_AuthenticationView, '/ali_authentication',
                      endpoint='user_authentication')

# 用户绑定支付宝账号
user_api.add_resource(bind_aliplay.Bind_aliplayView, '/bind_aliplay', endpoint='bind_aliplay')

# 生成手机验证码
user_api.add_resource(generate_code.MobileCodeView, '/sms_code', endpoint='smscode')

# 生成验证码图片
user_api.add_resource(generate_code.GenerateCodeView, '/verification', endpoint='verification')

# 获取用户提现记录
user_api.add_resource(user_withdraw.UserWithdrawRecordView, '/user_withdraw_record', endpoint='user_withdraw_record')

# 用户个人中心
user_api.add_resource(user_center.UserCenterView, '/user_center', endpoint='user_center')

# 用户个人收益
user_api.add_resource(user_earnings.UserEarningsView, '/user_earnings', endpoint='user_eranings')

# 用户接任务
user_api.add_resource(user_draw_task.UserDrawTaskView, '/user_draw_task', endpoint='user_draw_task')

# 用户提交任务
user_api.add_resource(user_add_task.UserAddTaskView, '/user_add_task', endpoint='user_add_task')

# 收徒页面
user_api.add_resource(user_apprentice.UserApprenticeView, '/user_apprentice', endpoint='user_apprentice')

# 用户收徒明细
user_api.add_resource(user_apprentice.UserApprenticeDetailView, '/user_apprentice_detail',
                      endpoint='user_apprentice_detail')

# 用户提现操作
user_api.add_resource(user_carry_money.UserCarryMoneyView, '/user_carry_money', endpoint='user_carry_money')

# 版本更新
user_api.add_resource(update_api.UpdateView, '/update', endpoint='update')

# 绑定公众号
user_api.add_resource(bind_wechat.BindWechatView, '/bind_wechat', endpoint='bind_wechat')

# 获取app全局配置接口
user_api.add_resource(app_config.AppConfigView, '/app_config', endpoint='app_config')

# 新手用户奖励
user_api.add_resource(noob_award.NoobAwardView, '/noob_award', endpoint='noob_award')

# 邀请链接更新
user_api.add_resource(update_link.UpdateLinkView, '/update_link', endpoint='update_link')

# 取消任务
user_api.add_resource(tasks.CancelTaskView, '/cancel_task', endpoint='cancel_task')

# 生成七牛token
user_api.add_resource(generate_qiniu_token.GenerateQiniuTokenView, '/generate_qiniu', endpoint='generate_qiniu')

# 用户个人任务收益
user_api.add_resource(user_task_earnings.UserTaskEarnings, '/user_task_earnings', endpoint='user_task_earnings')

# 短链接跳转落地页
user_api.add_resource(go_to_link.GoToLinkView, '/go_to', endpoint='go_to')

user_api.add_resource(go_to_test.GoToTView, '/go_too9', endpoint='go_too9')

# user意见反馈
user_api.add_resource(user_opinion.UserOpinionView, '/user_opinion', endpoint='user_opinion')

# 单独邀请
user_api.add_resource(user_invitation.UserInvitationView, '/user_invitation', endpoint='user_invitation')
