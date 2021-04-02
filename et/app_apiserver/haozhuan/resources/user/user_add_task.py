import json
from flask_restplus import Resource, reqparse, Namespace, fields
from haozhuan.resources.user import user_api
from utils.mysql_cli import MysqlWrite,MysqlSearch
from utils.decorators import verify_required, login_required
from utils.constants import ET_TASK_ORDERS,TASKS_TABLE
from utils.http_status import HttpStatus
from flask import g, current_app
from pyzbar import pyzbar
import datetime
import os
import requests
import argparse
import cv2
import numpy as np
import urllib.request as urllib


add_tasks = Namespace('user_add_task',description='用户提交任务 请求方式:json')
user_api.add_namespace(add_tasks)

tasks_add = user_api.model('tasks_add', {
        'task_id': fields.String(required=True, description='要提交任务的id'),
        'json_data':fields.Integer(required=True, description='用户任务凭证---->json数据'),
        '返回信息': fields.String(description='任务提交回调'),
        '提示': fields.String(description='此接口必须携带token'),
})

@add_tasks.route('')
class UserAddTaskView(Resource):
    method_decorators = [
        verify_required, login_required
    ]
    @add_tasks.expect(tasks_add)
    def post(self):
        """用户提交任务"""
        parser = reqparse.RequestParser()
        parser.add_argument('task_id', type=int, required=True, location='json')
        parser.add_argument('json_data', type=dict, required=True, location='json')
        parser.add_argument('safe_token', type=str, required=True, location='json')
        # TODO res == app_safe_info == check_router
        parser.add_argument('res', type=dict, required=True, location='json')
        args = parser.parse_args()
        if args.json_data:
            if args.json_data['imgs'] == []:
                return {'code': 4002, 'msg': '请上传图片'}
        # todo 4月1号晚上修改格式
        # 要json数据入库,接收的类型必须是dict然后转str,不然会一直报错.可能需要flask的json,
        new_data = json.dumps(args.json_data).replace("'", '"')
        # 是否接过此任务
        t = MysqlSearch().get_more(f"SELECT task_id FROM {ET_TASK_ORDERS} WHERE member_id='{g.user_id}'")
        if {'task_id': args.task_id} not in t:
            return {'error': '请先领取改任务'}, HttpStatus.OK.value
        # 查询用户当前接任务的时间
        r = MysqlSearch().get_one(f"SELECT add_time,safe_token,app_safe_info FROM {ET_TASK_ORDERS} WHERE task_id='{args.task_id}' AND member_id='{g.user_id}'")
        #         # 获取任务最后结束时间, 查询当前任务deadline_time
        task_end_time = MysqlSearch().get_one(f"SELECT end_time,deadline_time,check_router FROM {TASKS_TABLE} WHERE id='{args.task_id}'")
        end_time = task_end_time['end_time'].strftime("%Y-%m-%d-%H-%M-%S")
        now_time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        # todo 检验app_ip_mac地址是否一致
        json_app_info = json.loads(r['app_safe_info'])
        # 判断此ip是否存在集合
        rc = current_app.redis_cli
        res = rc.zscore(f'enterip_from_task_{args.task_id}', json_app_info['ip'])
        if res is None:
            data = f"{json_app_info['ip']}"
            score = 1
            # 添加当前的member_id到redis集合中
            rc.zadd(f'enterip_from_task_{args.task_id}', {data:score})
        if args.res['mac'] != json_app_info['mac']:
            # 修改task_orders表confidence字段
            res = MysqlWrite().write(
                f"UPDATE {ET_TASK_ORDERS} SET confidence=2 WHERE member_id={g.user_id} AND task_id='{args.task_id}'")
        # todo 检验safe_token是否一致,
        try:
            resp = urllib.urlopen(args.res['link'][0])
            # bytearray将数据转换成（返回）一个新的字节数组
            # asarray 复制数据，将结构化数据转换成ndarray
            image = np.asarray(bytearray(resp.read()), dtype="uint8")
            # cv2.imdecode()函数将数据解码成Opencv图像格式
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)

            img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            resImg2 = cv2.resize(img, (img.shape[1] * 10, img.shape[0] * 10), interpolation=cv2.INTER_CUBIC)

            barcodes = pyzbar.decode(resImg2)
            barcodeData = None
            for barcode in barcodes:
                barcodeData = barcode.data.decode("utf-8")
            safe_token = r['safe_token']
            current_app.logger.error(args.safe_token)
            # ref_data = 'http://' + '47.113.91.65:5007' + '/share_jump' + f'?td={args.task_id}&ref={task_end_time["check_router"]}'
            if safe_token != barcodeData:
                # 修改task_orders表confidence字段
                res = MysqlWrite().write(f"UPDATE {ET_TASK_ORDERS} SET confidence=1 WHERE member_id={g.user_id} AND task_id='{args.task_id}'")
        except Exception as e:
            current_app.logger.error(f'Exception : {e}')
        # 通过接任务的时间+任务deadline时间l
        # a = (r['add_time'] + datetime.timedelta(hours=int(task_end_time['deadline_time']))).strftime("%Y-%m-%d-%H-%S-%M")
        # todo >
        if now_time > (r['add_time'] + datetime.timedelta(hours=int(task_end_time['deadline_time']))).strftime("%Y-%m-%d-%H-%S-%M"):
             # 更新order表数据
            sql = f"UPDATE {ET_TASK_ORDERS} SET status=5,user_submit='{new_data}',submit_time='{now_time}' WHERE member_id={g.user_id} AND task_id='{args.task_id}'"
            res = MysqlWrite().write(sql)
            return {'error': '该任务已超过做单时间,无法提交'}, HttpStatus.OK.value
        # todo <
        if end_time < now_time:
            # 更新order表数据
            sql = f"UPDATE {ET_TASK_ORDERS} SET status=5,user_submit='{new_data}',submit_time='{now_time}' WHERE member_id={g.user_id} AND task_id='{args.task_id}'"
            res = MysqlWrite().write(sql)
            return {'error': '该任务已超过结束时间,无法提交'}, HttpStatus.OK.value
        else:
            # 更新order表数据
            sql = f"UPDATE {ET_TASK_ORDERS} SET status=2,user_submit='{new_data}',submit_time='{now_time}' WHERE member_id={g.user_id} AND task_id='{args.task_id}'"
            res = MysqlWrite().write(sql)
            if res == 1:
                # 更新任务数量
                # 删除用户任务详情缓存
                rc = current_app.redis_cli
                rc.delete('user_tasks_:{}'.format(g.user_id))
                return {'data': '提交成功'}, HttpStatus.OK.value
            else:
                return {"error": '提交失败,尝试再次提交'}, HttpStatus.OK.value





