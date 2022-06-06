# -*- coding: utf-8 -*-
from jinja2 import Template
import requests
import json
import re

def check_inex_data_search(login):
    data = {"login":login, "actionsearch": '/auth/login', "status": '401'}
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0aWNrZXRfdGVleF8xIiwicm9sZXMiOiJvcCIsImlhdCI6MTYwMzIxMDczNn0.bqFmtg8gOOdDNfkj1XPgiZ8Z31GgqvnRcyJ-k1Blqdc"}
    r = requests.post('https://journal.onelya.ru/audit/v1/search', headers = headers, json=data, timeout=20)
    respons = json.loads(r.text)
    return respons
    
def get_answer(check_inex_data_data):
    with open("tamplate/check_inex_data.txt", "r", encoding="utf-8") as template:
        read_template = template.read()
    read_template = Template(read_template, trim_blocks=True)
    answer = read_template.render(check_inex_data_data)
    return answer

def check_inex_data(login):
    login = str(login)
    sj_data = check_inex_data_search(login)[0]
    error = sj_data['error']
    login = sj_data['login']
    email = sj_data['email']
    inex_email = re.findall(r'[^\s]+$', error)[0]
    check_inex_data_data = {
        'error': error,
        'login': login,
        'email': email,
        'inex_email': inex_email       
        }
    check_inex_answer = get_answer(check_inex_data_data)
    return check_inex_answer
