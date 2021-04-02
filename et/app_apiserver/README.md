## redis key info | type info

###  约定接口缓存信息

```
关系数缓存： key => drp_relation_member_{top_parent_id} | type=> hash

任务缓存： key => tasks_info | type=> hash

任务详情缓存： key => tasks_detail_:{task_id} | type=> hash

app更新接口缓存： key => user_update | type=> str

用户缓存： key => user_info_:{mobile} | type=> hash

用户收徒页面缓存： key => user_apprentice_:{member_id} | type=> hash

用户收徒收益明细缓存：key => user_appretice_detail_:{member_id} | type=> list

用户提现页面数据缓存：key => user_carry_money_:{member_id} | type=> hash

用户个人中心缓存：key => user_center:{member_id} | type=> hash

用户个人收益缓存：key => user_earnings:{member_id} | type=> list

用户个人收益缓存：key => user_earnings:{member_id} | type=> list

用户信息扩展缓存：key => user_extend_id:{member_id} | type=> hash

用户任务缓存：key => user_tasks_:{member_id} | type=> list

用户任务缓存：key => user_withdraw_recode:{member_id} | type=> list

```