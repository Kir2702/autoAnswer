# -*- coding: utf-8 -*-
import json
def type(bo_data):
    type = 'undefined'
    status_list=[]
    for l in bo_data:
        status_list.append(l.get("DisplayCssClass"))
    cash_list = []
    for i in status_list:
        cash_list.append(i)
    S = set()
    status_list = []
    for e in cash_list:
        if e in S:
            continue
        S.add(e)
        status_list.append(e)
    if len(status_list) == 1:
        if status_list[0] == 'progress':
            type = 'booked'
        if status_list[0] == 'error':
            type = 'error'
        if status_list[0] == 'success':
            type = 'success'
    if len(status_list) > 1:
        if 'success' in status_list or 'return' in status_list:
            type = 'success'
    return type
