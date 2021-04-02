import random
import re

import requests
from flask import current_app, Response
from flask_limiter.util import get_remote_address
from flask_restplus import Resource, reqparse, Namespace, fields
import base64
from haozhuan.resources.user import user_api
from utils import constants, parser
from utils.captcha.captcha import captcha
from utils.send_sms import SendSMS
from utils.limiter import limiter as lmt
from utils.http_status import HttpStatus

generate = Namespace('sms_code',description='获取手机短信验证码 请求方式:json')
generate_code = Namespace('verification',description='生成验证码图片 请求方式:关键字')
user_api.add_namespace(generate)
user_api.add_namespace(generate_code)

sms_code_model = user_api.model('sms_code', {
        'mobile': fields.String(required=True, description='手机号码'),
        'uuid': fields.String(required=True, description='在图片验证码哪里生成的uuid'),
        'v_code': fields.String(required=True, description='用户输入的验证码'),
        '返回信息': fields.String(description='验证码获取的状态'),
})

image_code_model = user_api.model('verification', {
        'uuid': fields.Integer(required=True, description='要生成一个uuid给我作为图片验证码唯一识别'),
        '返回信息': fields.String(description='验证码图片/jpeg'),
})

@generate_code.route('')
class GenerateCodeView(Resource):

    error_message = 'Too many requests.'

    decorators = [
        lmt.limit(constants.LIMIT_SMS_VERIFICATION_CODE_BY_IP,
                  key_func=get_remote_address,
                  error_message=error_message)
    ]
    @generate_code.expect(image_code_model)
    def get(self):
        """生成图片验证码"""
        parser_data = reqparse.RequestParser()
        parser_data.add_argument('uuid', type=str, required=True)
        args = parser_data.parse_args()
        # 生成图片验证码
        data = captcha.generate_captcha()
        text = data[1]
        image = data[2]
        # 保存图片验证码
        current_app.redis_cli.setex('img_{}'.format(args.uuid), constants.IMAGES_VERIFICATION_CODE_EXPIRES, text)
        # 响应图片验证码
        # base_image = base64.b64encode(image).decode()
        # return {'data':  base_image}
        resp = Response(image, mimetype="image/jpeg")
        return resp

@generate.route('')
class MobileCodeView(Resource):
    @generate.expect(sms_code_model)
    def post(self):
        """短信验证码"""
        parser_data = reqparse.RequestParser()
        parser_data.add_argument('mobile', type=str, required=True, location='json')
        parser_data.add_argument('uuid', type=str, required=True, location='json')
        parser_data.add_argument('v_code', type=str, required=True, location='json')
        args = parser_data.parse_args()
        current_app.logger.debug(args)
        v_code = args.v_code.upper()
        redis_code = current_app.redis_cli.get('img_{}'.format(args.uuid))
        if not re.match(r'^1([34589][0-9]{9}|(6[01234689]{1})[0-9]{8}|(7[2-9]{1})[0-9]{8})$', args.mobile):
            return {'error': '手机号码格式错误'}, HttpStatus.OK.value
        if redis_code:
            redis_v_code = redis_code.decode()
        else:
            return {'error': '图片验证码已过期'}, HttpStatus.OK.value
        if v_code:
            if v_code == redis_v_code:
                code = '{:0>6d}'.format(random.randint(0, 999999))
                current_app.redis_cli.setex('app:code:{}'.format(args.mobile), constants.SMS_VERIFICATION_CODE_EXPIRES, code)
                SendSMS().send(args.mobile, code)
                return {'data': '成功获取验证码'}, HttpStatus.OK.value
            elif v_code != redis_v_code:
                return {'error': '验证码错误'}, HttpStatus.OK.value
