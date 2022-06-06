# -*- coding: utf-8 -*-
import re
import json
import requests
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
        'login': login,
        'email': email_cens,
        'date_time_create': date_time_create,
        'blocks': blocks
        }
    return answer_data

def BO_answer_data(bo_data):
    bo_answer_data = []
    for l in bo_data:
        if l.get('UiSimpleStatus') == 'Success' and l.get('DisplayType') == 'Покупка':
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
     	'login': sj_answer_data['login'],
	'email': sj_answer_data['email'],
	'date_time_create': sj_answer_data['date_time_create'],
        'blanks_in_order': blanks_in_order,
        'blocks': blocks        
        }
    return answer_data

def tariff_found(number, bo_data):
    for l in bo_data:
        if l.get("UiSimpleStatus") == "Success" and l.get("DisplayType") == "Покупка" and l.get("DisplayServiceType") == "ЖД-билеты":
            blanks = l.get('Blanks')
            for blank in blanks:
               tariff = blank.get('RailwayAddData').get('TariffDisplayName')
               if str(blank.get('BlankNumber')) == str(number):
                   return tariff

def carrier_found(number, bo_data):
    for l in bo_data:
        if l.get("UiSimpleStatus") == "Success" and l.get("DisplayType") == "Покупка" and l.get("DisplayServiceType") == "ЖД-билеты":
            route_parts = l.get('RouteParts')
            for route in route_parts:
                carrier = route.get('CarrierExpressNameRu')
                order_item_id = route.get('OrderItemId')
                blanks = l.get('Blanks')
                for blank in blanks:
                    if str(blank.get('BlankNumber')) == str(number):
                        if str(blank.get('OrderItemId')) == str(order_item_id):
                            return carrier
   
def price_found(number, bo_data):     
    for l in bo_data:
        if l.get("UiSimpleStatus") == "Success" and l.get("DisplayType") == "Покупка" and l.get("DisplayServiceType") == "ЖД-билеты":
            blanks = l.get('Blanks')
            for blank in blanks:
               price = blank.get('Fare')
               if str(blank.get('BlankNumber')) == str(number):
                   return price

def passenger_name_found(number, bo_data):     
    for l in bo_data:
        if l.get("UiSimpleStatus") == "Success" and l.get("DisplayType") == "Покупка" and l.get("DisplayServiceType") == "ЖД-билеты":
            blanks = l.get('Blanks')
            for blank in blanks:
               passenger = blank.get('CustomerNames')
               if str(blank.get('BlankNumber')) == str(number):
                   return passenger

def service_class_found(number, bo_data):
    for l in bo_data:
        if l.get("UiSimpleStatus") == "Success" and l.get("DisplayType") == "Покупка" and l.get("DisplayServiceType") == "ЖД-билеты":
            blanks = l.get('Blanks')
            for blank in blanks:
                order_item_id = blank.get('OrderItemId')
                for i in l.get('OrderItemSegmentGroupLasts'):
                    if str(i.get('OrderItemId')) == str(order_item_id):
                        car_number = i.get('RailwayAddData').get('CarNumber')
                        service_class = i.get('RailwayAddData').get('ServiceClass')               
                blank_customers = blank.get('BlankCustomers')
                customers_id_list = []
                for customer in blank_customers:
                    customers_id_list.append(str(customer.get('OrderCustomerId')))
                places = str()
                for j in l.get('PassengerRouteParts'):
                    if str(j.get('OrderCustomerId')) in customers_id_list:
                        places = places + str(j.get('Places')) + ' '     
                if str(blank.get('BlankNumber')) == str(number):
                    service_class = str('класс обслуживания ' + service_class + ', вагон ' + car_number + ', место ' + places)
                    return service_class

def return_date_found(confirm_data, blank):
    confirm_results = confirm_data['ConfirmResults']
    for blok in confirm_results:
        if blok['$type'] == 'ApiContracts.Railway.V1.Messages.Reservation.RailwayConfirmResponse, ApiContracts':
            blanks = blok['Blanks']

            for i in blanks:
                if int(i['Number']) == int(blank):
                    return_date = i['OnlineTicketReturnExpirationDateTime']
                    return_date = re.sub(r'\-', '.', return_date)
                    return_date = re.sub(r'[T]', ' ', return_date)
                    return_time = re.findall(r'\d\d:\d\d', return_date)
                    return_year = re.findall(r'\d{4}', return_date)
                    return_year = re.findall(r'\d\d$', return_year[0])
                    return_month_day = re.findall(r'\b\d\d', return_date)
                    return_date = (return_month_day[2] + '.' + return_month_day[1] + '.' +  return_year[0] + ' в ' +  return_time[0]) 
                    break
    return return_date

def get_confirm(orderid):
    actionsearch = "/order/confirm"
    data = {"orderid":orderid, "actionsearch":actionsearch, "status":'200'}
    headers = {"Authorization": ''}
    r = requests.post('https://' headers = headers, json=data, timeout=10)
    respons = json.loads(r.text)
    confirm = respons[0].get('response')
    for i in range(len(confirm)):
        if ord(confirm[i]) == 10:
            delimiter = i
            break
    confirm = json.loads(confirm[delimiter:])
    return confirm

def get_get_receipts(orderid):
    actionsearch = "/auth/getTickets"
    data = {"orderid":orderid, "actionsearch":actionsearch, "status":'200'}
    headers = {"Authorization": ""}
    r = requests.post('https://', headers = headers, json=data, timeout=10)
    respons = json.loads(r.text)

    links = []
    for i in respons:
        resp = i['response']
        resp = json.loads(resp)
        receipt_links = resp['receiptLinks']
        for receipt_link in receipt_links:
            links.append(receipt_link['receiptlink'])
    cash_list = []
    for i in links:
        cash_list.append(i)
    S = set()
    links = []
    for e in cash_list:
        if e in S:
            continue
        S.add(e)
        links.append(e)
    if len(links) == 1 and links[0] == '':
        return str('В journal.onelya.ru отсутствуют ссылки не чеки')
    else:
        str_links = str('')
        for link in links:
            str_links = str_links + link + '\n'
        return str_links

def add(answer_data, values, bo_data):
    order_includes = str('Заказ включает ЭБ:')
    for blank in answer_data['blanks_in_order']['blanks']:
        order_includes = order_includes + '\n№ ' + blank
        if values['tariff'] == True:
            try:
                order_includes = order_includes + ' тариф: «' + str(tariff_found(blank, bo_data)) + '»; '
            except:
                None
        if values['carrier'] == True:
            try:
                order_includes = order_includes + ' перевозчик: «' + str(carrier_found(blank, bo_data)) + '»; '
            except:
                None
        if values['price'] == True:
            try:
                order_includes = order_includes + ' на сумму: ' + str(price_found(blank, bo_data)) + ' руб; '
            except:
                None
        if values['passenger_name'] == True:
            try:
                order_includes = order_includes + ' на ' + str(passenger_name_found(blank, bo_data)) + '; '
            except:
                None        
        if values['service_class'] == True:
            try:
                order_includes = order_includes + ' ' + str(service_class_found(blank, bo_data)) + '; '
            except:
                None    
        if values['return_date'] == True:
            try:
                confirm_data = get_confirm(values['orderid'])
                order_includes = order_includes + ' дата и время возврата онлайн: ' + str(return_date_found(confirm_data, blank)) + '; '
            except:
                None   
    if len(answer_data['blanks_in_order']['meals']) > 0:
        order_includes = order_includes + '\nЗаказ включает ЭКРС:'
        for blank in answer_data['blanks_in_order']['meals']:
            order_includes = order_includes + ' № ' + blank
    if len(answer_data['blanks_in_order']['baggage']) > 0:
        order_includes = order_includes + '\nЗаказ включает ЭБК:'
        for blank in answer_data['blanks_in_order']['baggage']:
            order_includes = order_includes + ' № ' + blank
    if len(answer_data['blanks_in_order']['insurance']) > 0:
        order_includes = order_includes + '\nЗаказ включает ЭСП:'
        for blank in answer_data['blanks_in_order']['insurance']:
            order_includes = order_includes + ' № ' + blank
    if values['receipt'] == True:
        if values['tariff'] == False and values['carrier'] == False and values['price'] == False and values['passenger_name'] == False and values['service_class'] == False and values['return_date'] == False:
            order_includes = str('')
            if len(answer_data['blanks_in_order']['blanks']) > 0:
                order_includes = order_includes + '\nЗаказ включает ЭБ:'
                for blank in answer_data['blanks_in_order']['blanks']:
                    order_includes = order_includes + ' № ' + blank
            if len(answer_data['blanks_in_order']['meals']) > 0:
                order_includes = order_includes + '\nЗаказ включает ЭКРС:'
                for blank in answer_data['blanks_in_order']['meals']:
                    order_includes = order_includes + ' № ' + blank
            if len(answer_data['blanks_in_order']['baggage']) > 0:
                order_includes = order_includes + '\nЗаказ включает ЭБК:'
                for blank in answer_data['blanks_in_order']['baggage']:
                    order_includes = order_includes + ' № ' + blank
            if len(answer_data['blanks_in_order']['insurance']) > 0:
                order_includes = order_includes + '\nЗаказ включает ЭСП:'
                for blank in answer_data['blanks_in_order']['insurance']:
                    order_includes = order_includes + ' № ' + blank        
            try:
                receipt = get_get_receipts(values['orderid'])
            except:
                receipt = None
        else:
            try:
                receipt = get_get_receipts(values['orderid'])
            except:
                receipt = None
    else:
        receipt = None
    answer_data_add = {
        'order_id': answer_data['order_id'],
        'login': answer_data['login'],
        'email': answer_data['email'],
        'date_time_create': answer_data['date_time_create'],
        'blanks_in_order': order_includes,
        'blocks': answer_data['blocks'],
        'receipt': receipt
        }
    return answer_data_add

def get_add_answer(answer_add_data):
    with open("tamplate/success_add.txt", "r", encoding="utf-8") as template:
        read_template = template.read()
    read_template = Template(read_template, trim_blocks=True)
    answer = read_template.render(answer_add_data)
    return answer

def answer_add(bo_data, sj_data, values):
    sj_answer_data = SJ_answer_data(sj_data)
    bo_answer_data = BO_answer_data(bo_data)
    answer_data = combination(sj_answer_data, bo_answer_data)
    answer_add_data = add(answer_data, values, bo_data)
    answer_add = get_add_answer(answer_add_data)
    return answer_add

def get_answer(answer_data):
    with open("tamplate/success.txt", "r", encoding="utf-8") as template:
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
