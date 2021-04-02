import re

def mobile(mobile_str):
    """
    检验手机号格式
    :param mobile_str: str 被检验字符串
    :return: mobile_str
    """
    if re.match(r'^1([34589][0-9]{9}|(6[01234689]{1})[0-9]{8}|(7[2-9]{1})[0-9]{8})$', mobile_str):
        return mobile_str
    else:
        raise ValueError('请输入正确手机号码格式')


def id_car(idcar_str):
    if re.match(r'[^\u4e00-\u9fa5]', idcar_str):
        return idcar_str
    else:
        return ValueError('输入正确身份证格式')


def name_str(namestr):
    if re.match(r'[\u4e00-\u9fa5]', namestr):
        return namestr
    else:
        raise ValueError('输入正确中文名称')

def email(email_str):
    """
    检验邮箱格式
    :param email_str: str 被检验字符串
    :return: email_str
    """
    if re.match(r'^([A-Za-z0-9_\-\.\u4e00-\u9fa5])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,8})$', email_str):
        return email_str
    else:
        raise ValueError('请输入正确邮箱格式')


def regex(pattern):
    """
    正则检验
    :param pattern: str 正则表达式
    :return:  检验函数
    """
    def validate(value_str):
        """
        检验字符串格式
        :param value_str: str 被检验字符串
        :return: bool 检验是否通过
        """
        if re.match(pattern, value_str):
            return value_str
        else:
            raise ValueError('Invalid params.')

    return validate


