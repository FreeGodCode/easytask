from flask_restplus import Resource
from utils.http_status import HttpStatus
from utils.qiniu_token import generate_token

class GenerateQiniuTokenView(Resource):
    def get(self):
        if generate_token():
            res = generate_token()
            return {'data': res}, HttpStatus.OK.value
        else:
            return {'error': '请重试'}, HttpStatus.OK.value
