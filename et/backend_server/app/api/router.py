from app.api.account_service import bp as accountAPI
from app.api.member_service import bp as memberAPI
from app.api.task_service import bp as tasksAPI
from app.api.orders_service import bp as ordersAPI
from app.api.systems_service import bp as systemConfigAPI
from app.api.drp_service import bp as drpAPI
from app.api.activity_service import bp as activityAPI
# from app.api.account_operate_service import bp as accountOperateAPI
from app.api.work_station import bp as workstationAPI
from app.api.oem_service import bp as oemAPI
from app.api.flows_service import bp as flowsApi


router = [
    accountAPI,
    memberAPI,
    tasksAPI,
    ordersAPI, 
    systemConfigAPI,
    drpAPI,
    activityAPI,
    # accountOperateAPI,
    flowsApi,
    workstationAPI,
    oemAPI,
]
