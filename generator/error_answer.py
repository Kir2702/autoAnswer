# -*- coding: utf-8 -*-
import re
import json
import datetime
from jinja2 import Template

def SJ_answer_data(sj_data):
    for l in sj_data:
        orderidinjson = l.get("orderid")
        login = l.get("login")
        email = l.get("email")
        censorship = re.findall(r'(?<=\S)(\S+)[@]', email)
        if len(censorship) == 0:
            email_cens = re.findall(r'[@]\S+', email)
            email_cens = ('*' + email_cens[0])
        else:
            email_cens = re.sub(r'(?<=\S)(\S+)[@]', '*' * len(censorship[0]) + '@', email)
        date_time_create = l.get("datetime")
        date_time_create = re.findall(r'^\d\d\d\d\d\d\d\d\d\d', date_time_create)
        date_time_create = int((date_time_create[0]))
        date_time_create = datetime.datetime.fromtimestamp(date_time_create).strftime('%d.%m.%y' " в " '%H:%M')
        response = json.loads(l.get("response"))
    agent_payment_id = response.get('AgentPaymentId')
    blocks = []
    rout_blocks = response.get("ReservationResults")
    for i in rout_blocks:
        route = i['OriginStation'] + " → " + i['DestinationStation']
        train_number = i['TrainNumber']
        departure_date_time = re.sub(r'\-', '.', i['DepartureDateTime'])
        departure_date_time = re.sub(r'[T]', ' ', departure_date_time)
        departure_time = re.findall(r'\d\d:\d\d$', departure_date_time)
        departure_year = re.findall(r'\d{4}', departure_date_time)
        departure_year = re.findall(r'\d\d$', departure_year[0])
        departure_month_day = re.findall(r'\b\d\d', departure_date_time)
        departure_date_time = (departure_month_day[2] + '.' + departure_month_day[1] + '.' +  departure_year[0] + ' в ' +  departure_time[0]) 
        blanks = i.get('Blanks')
        id_blanks = []
        for b in blanks:
            id_blank = b.get('OrderItemBlankId')
            id_blanks.append(id_blank)
        block = {
            'route': route,
            'train_number': train_number,
            'departure_date_time': departure_date_time,
            'id_blanks': id_blanks
            }
        blocks.append(block)
    answer_data = {
        'order_id': orderidinjson,
        'agent_payment_id': agent_payment_id,
        'login': login,
        'email': email_cens,
        'date_time_create': date_time_create,
        'blocks': blocks
        }
    return answer_data

def BO_answer_data(bo_data):
    bo_answer_data = []
    for l in bo_data:
        if l.get('UiSimpleStatus') == 'Error' and l.get('DisplayType') == 'Покупка':
            display_service_type = l.get('DisplayServiceType')
            if display_service_type == 'ЖД-билеты':
                item_id = l.get('OrderItemId')
            else:
                item_id = l.get('MainItemId')
            blanks = l.get('Blanks')
            for b in blanks:
                blank_bo_id = b.get('OrderItemBlankId')
                blank_number = b.get('BlankNumber')
                fix_number_blanc = blank_number
                try:
                    blank_number = re.sub(r'[№]', '', fix_number_blanc)
                except:
                    None
                customers_id = []
                blank_customers = b.get('BlankCustomers')
                for c in blank_customers:
                    customer_id = c.get('OrderCustomerId')
                    customers_id.append(customer_id)               
                data_blank = {
                    'blank_bo_id': blank_bo_id,
                    'item_id': item_id,
                    'customers_id': customers_id,
                    'blank_number': blank_number,
                    'display_service_type': display_service_type
                    }
                bo_answer_data.append(data_blank)
    return bo_answer_data

def combination (sj_answer_data, bo_answer_data):
    blanks = []
    meals = []
    baggage = []
    insurance = []
    for blank in bo_answer_data:
        if blank['display_service_type'] == 'ЖД-билеты':
            blanks.append(blank['blank_number'])
        elif blank['display_service_type'] == 'ЖД, дополнительное питание':
            meals.append(blank['blank_number'])
        elif blank['display_service_type'] == 'ЖД, дополнительный багаж':
            baggage.append(blank['blank_number'])
        elif blank['display_service_type'] == 'Страховки НС' or blank['display_service_type'] == 'Страховки МС':
            insurance.append(blank['blank_number'])   
    blanks_in_order = {
        'blanks': blanks,
        'meals': meals,
        'baggage': baggage,
        'insurance': insurance
        }
    cash_list = []
    for block in sj_answer_data['blocks']:
        cash_block = []
        cash_block.append(block['route'])
        cash_block.append(block['train_number'])
        cash_block.append(block['departure_date_time'])
        cash_list.append(cash_block)
    blocks_without_duplicates = []
    for i in cash_list:
        if i in blocks_without_duplicates:
            None
        else:
           blocks_without_duplicates.append(i)
    blocks = []
    for i in blocks_without_duplicates:
        id_blanks_list = []
        for j in sj_answer_data['blocks']:
            if i[0] == j['route'] and i[1] == j['train_number'] and i[2] == j['departure_date_time']:
                id_blanks_list.append(j['id_blanks'])
        id_blanks = []
        for first_layer in id_blanks_list:
            for second_layer in first_layer:
                id_blanks.append(second_layer)
        blank_numbers = []
        for id_blank in id_blanks:
            for bo_data in bo_answer_data:
                if id_blank == bo_data['blank_bo_id']:
                    blank_numbers.append(str('ЭБ ' + bo_data['blank_number']))
                    for add in bo_answer_data:
                        if add['display_service_type'] != 'ЖД-билеты':
                            if bo_data['item_id'] == add['item_id']:
                                if len(add['customers_id']) == 1:
                                    for add_customer_id in add['customers_id']:
                                        for blanck_customer_id in bo_data['customers_id']:
                                            if add_customer_id == blanck_customer_id:                                                
                                                if add['display_service_type'] == 'ЖД, дополнительное питание':  
                                                    blank_numbers.append(str('ЭКРС ' + add['blank_number']))
                                                if add['display_service_type'] == 'ЖД, дополнительный багаж':    
                                                    blank_numbers.append(str('ЭБК ' + add['blank_number']))
                                                if add['display_service_type'] == 'Страховки НС' or add['display_service_type'] == 'Страховки МС':
                                                    blank_numbers.append(str('ЭСП ' + add['blank_number']))
                                                break   
                                if len(add['customers_id']) == 2:
                                    for add_customer_id in add['customers_id']:
                                        for blanck_customer_id in bo_data['customers_id']:                                                                                        
                                            if add_customer_id == blanck_customer_id:                                                
                                                if add['display_service_type'] == 'ЖД, дополнительное питание':  
                                                    blank_numbers.append(str('ЭКРС ' + add['blank_number']))
                                                if add['display_service_type'] == 'ЖД, дополнительный багаж':    
                                                    blank_numbers.append(str('ЭБК ' + add['blank_number']))
                                                if add['display_service_type'] == 'Страховки НС' or add['display_service_type'] == 'Страховки МС':
                                                    blank_numbers.append(str('ЭСП ' + add['blank_number']))
                                            break    
                
        block = {
            'route': i[0],
            'train_number': i[1],
            'departure_date_time': i[2],
            'blank_numbers': blank_numbers
            }
        blocks.append(block)
    answer_data = {
        'order_id': sj_answer_data['order_id'],
        'agent_payment_id': sj_answer_data['agent_payment_id'],      
     	'login': sj_answer_data['login'],
	'email': sj_answer_data['email'],
	'date_time_create': sj_answer_data['date_time_create'],
        'blanks_in_order': blanks_in_order,
        'blocks': blocks        
        }
    return answer_data

def get_answer(answer_data):
    with open("tamplate/error.txt", "r", encoding="utf-8") as template:
        read_template = template.read()
    read_template = Template(read_template, trim_blocks=True)
    answer = read_template.render(answer_data)
    return answer

def answer(bo_data, sj_data):
    sj_answer_data = SJ_answer_data(sj_data)
    bo_answer_data = BO_answer_data(bo_data)
    answer_data = combination(sj_answer_data, bo_answer_data)
    answer = get_answer(answer_data)
    return answer
