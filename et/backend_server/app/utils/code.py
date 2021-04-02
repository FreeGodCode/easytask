class ResponseCode:
    Success = 20000  # 请求成功
    Fail = -1  # 请求失败
    LoginSuccess = 20000 # 登录成功
    LoginFail = 40004  # 登录失败
    NoResourceFound = 40001  # 未找到资源
    InvalidParameter = 40002  # 参数无效
    AccountOrPassWordErr = 40003  # 账户或密码错误
    VerificationCodeError = 40005  # 验证码错误
    PleaseSignIn = 40005  # 请登陆
    WeChatAuthorizationFailure = 40006  # 微信授权失败
    InvalidOrExpired = 40007  # 验证码过期
    MobileNumberError = 40008  # 手机号错误
    FrequentOperation = 40009  # 操作频繁,请稍后再试
    TokenExpired = 500014 #Access Token过期

class ResponseMessage:
    Success = "成功"
    Fail = "失败"
    LoginSuccess = "登录成功"
    LoginFail = "登录失败"
    NoResourceFound = "未找到资源"
    InvalidParameter = "参数无效"
    AccountOrPassWordErr = "账户或密码错误"
    VerificationCodeError = "验证码错误"
    PleaseSignIn = "请登陆"
    TokenExpired = "Access Token过期"