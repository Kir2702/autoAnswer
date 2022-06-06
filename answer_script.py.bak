# -*- coding: utf-8 -*-
from generator import order_type, success_answer, error_answer, booked_answer
import requests
import json

def bo_data(orderid):
    headers = {"Authorization": "token="}
    r = requests.get('https://' + orderid, headers = headers, timeout=20)
    respons = json.loads(r.text)
    return respons

def sj_data(orderid):
    data = {"orderid": orderid, "actionsearch": "/e/create"}
    headers = {"Authorization": "token"}
    r = requests.post('https://', headers = headers, json = data, timeout=20)
    respons = json.loads(r.text)
    return respons

def get_answer(orderid, values):
    addition = False
    if values['price'] == True or values['tariff'] == True or values['return_date'] == True or values['carrier'] == True or values['passenger_name'] == True or values['service_class'] == True or values['receipt'] == True:
        addition = True
    try:
        bo = bo_data(orderid)
    except:
        return str("превышено время ожидания ответа от rgw.onelya.ru")
    try:
        sj = sj_data(orderid)
    except:
        return str("превышено время ожидания ответа от journal.onelya.ru")
    answer_type = order_type.type(bo)
    if answer_type == 'success':
        if addition == False:
            answer = success_answer.answer(bo, sj)
        else:
            answer = success_answer.answer_add(bo, sj, values)
        return answer
    if answer_type == 'error':
        answer = error_answer.answer(bo, sj)
        return answer
    if answer_type == 'booked':
        answer = booked_answer.answer(bo, sj)
        return answer
    if answer_type == 'undefined':
        return str("order type undefined") 


