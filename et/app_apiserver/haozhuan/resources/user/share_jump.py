from flask_restplus import reqparse, Resource
from utils.http_status import HttpStatus
from flask import request, current_app, redirect, g

class ShareJumpView(Resource):
    def get(self):
        parser_form = reqparse.RequestParser()
        parser_form.add_argument('td', type=str, required=True, location='args')
        parser_form.add_argument('ref', type=str, required=True, location='args')
        parser_form.add_argument('fromu', type=str, required=True, location='args')
        args = parser_form.parse_args()
        if not all([args.td, args.ref]):
            return {'code': 4002, 'msg': '请提供参数'}, HttpStatus.OK.value
        # 获取用户ip
        try:
            ip = request.headers['X-Forwarded-For'].split(',')[0]
            # 判断Ip是否存在在集合中 TODO 需增加集合key, enterip_from_task_{mid}
            rc = current_app.redis_cli
            res = rc.zscore(f'enterip_from_task_{args.td}', ip)
            res1 = rc.zscore(f'enterip_from_task_{args.fromu}_{args.td}', ip)
            if res is None:
                data = ip
                score = 1
                # 添加当前的member_id到redis集合中
                rc.zadd(f'enterip_from_task_{args.td}', {data: score})
            else:
                # 如果在增加该Ip分数
                rc.zincrby(f'enterip_from_task_{args.td}', 1, ip)
            if res1 is None:
                data = ip
                score = 1
                rc.zadd(f'enterip_from_task_{args.fromu}_{args.td}', {data: score})
            else:
                # 如果在增加该Ip分数
                rc.zincrby(f'enterip_from_task_{args.fromu}_{args.td}', 1, ip)
        except Exception as e:
            print(f"Exception: {e}")
            current_app.logger.error(f"Exception {e}")
        url = 'http://' + args.ref
        return redirect(url, 302)


