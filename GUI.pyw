# -*- coding: utf-8 -*-
import PySimpleGUI as sg
import answer_script
import check_inex_data
import requests
import json
import re
import os
import time
import random
import webbrowser
import datetime
import operator
import keyboard
import queue
import threading

# объявляем горячие клавиши
#ctrlc = 'ctrl + с'
#ctrlv = 'ctrl + м'

############################################[Функция генерации ответа]######################################################################
def answer_generate(work_id, gui_queue, orderid, values):
    try:
        answer = answer_script.get_answer(orderid, values)
        print(answer)
        gui_queue.put('{} ::: done'.format(work_id))
        return
    except:
        print('Что-то пошло не так((')
        sg.PopupAnimated(None)
        gui_queue.put('{} ::: done'.format(work_id))

        

def check_inex_generate(work_id, gui_queue, login):
    try:
        answer = check_inex_data.check_inex_data(login)
        print(answer)
        gui_queue.put('{} ::: done'.format(work_id))
        return
    except:
        print('Что-то пошло не так((')
        sg.PopupAnimated(None)
        gui_queue.put('{} ::: done'.format(work_id))


############################################[Генерируем словарь с данными выпадающего списка дополнения ответов]######################################################################
# определяем основные списки для формирования выпадающих списков
folder = []
tree = os.walk('additions')
for i in tree:
    folder.append(i)
drop_dict = {}
subtype = []
type = folder[0][1]
# формируем словарь с папками и файлами в них
for address, dirs, files in folder:
    if address == 'additions':
        None
    else:
        name_type = address
        name_type = re.sub(r"additions\\", '', name_type)
        name_file_in_subt_list = []
        for file in files:
            name_file_in_subt = re.sub(r"\.txt$", '', file)
            name_file_in_subt_list.append(name_file_in_subt)
        subtype.append(name_file_in_subt_list)
        name_subtype = {}
        for file in files:
            address_files = address + '/' + file
            address_files = re.sub(r"\\", '/', address_files)
            with open(r'' + address_files, "r", encoding="utf-8") as addition:
                name_file = addition.name
                name_file = re.sub(r"\.txt$", '', name_file)
                name_file = re.sub(r"^(.*?)/", '', name_file)
                name_file = re.sub(r"^(.*?)/", '', name_file)
                text_file = addition.read()
                name_subtype[name_file] = text_file
        drop_dict[name_type] = name_subtype

############################################[Отрисовка приложения]####################################################################################################################
gui_queue = queue.Queue(maxsize = 1)

layout = [
    
    [sg.Text('ID закза:', size=(8, 1)), 
     sg.InputText('', key = 'orderid'), 
     sg.Button(button_text = 'Создать ответ'),
     sg.Button(button_text = 'CHECK INEX DATA'),
     sg.Radio('БО БШ', 'BO', default=True, key = "BSH"), 
     sg.Radio('БО GDS', 'BO', default=False, key = "GDS"), 
     sg.Checkbox('Статус', key = 'status')
     ],
	 
    [sg.Checkbox('Цены', key = 'price'),
     sg.Checkbox('Тарифы', key = 'tariff'),
     sg.Checkbox('Дата возврата', key = 'return_date'),
     sg.Checkbox('Перевозчик', key = 'carrier'),
     sg.Checkbox('ФИО пассажиров', key = 'passenger_name'),
     sg.Checkbox('№ вагона, № места, класс обслужывания', key = 'service_class'),
     sg.Checkbox('Чеки', key = 'receipt')
     ],
    
    [sg.Text('Тип ответа:', size=(8, 1)),
     sg.Combo(type, default_value = 'Тип ответа', size=(21, None), key = "drop_list_1"),
     sg.Button(button_text = 'Выбрать'),
     sg.Combo([], default_value = 'Подтип ответа', size=(21, None), key = "drop_list_2"),
     sg.Button(button_text = 'Добавить')
     ],
    
    [sg.Output(size=(125, 30), key = "data_output")],
    [sg.Exit(),
     sg.Button(button_text = 'Clear')]
    ]

window = sg.Window('Генератор ответа', layout)#  no_titlebar = True , resizable = True

###############################################[Логика работы приложения]#################################################################################################################
work_id = 0
while True:                             
    event, values = window.read(timeout=100) # данные для работы логики
    if event in (None, 'Создать ответ'):
        # очищаем окно вывода от старой инфы
        window.FindElement("data_output").Update('')
        if values['BSH'] == True:
            # форматируем запрос
            orderid = values['orderid']
            orderid = re.sub(r'\s+', '', orderid)
            if re.match(r'\d\d\d\d\d\d\d\d', orderid):
                # получаем координаты верхнего левого угла окна
                window_location = window.CurrentLocation()
                window_x = window_location[0] + 340
                window_y = window_location[1] + 250

                # запускаем генератор ответа в отдельном потоке 
                if work_id == 0:
                    loading_animation = threading.Thread(target = answer_generate, args=(work_id, gui_queue, orderid, values,), daemon = True)
                    loading_animation.start()
                    work_id = 1
        if values['GDS'] == True:
            print("Функционал еще не реализован.")

    if event in (None, 'CHECK INEX DATA'):
        # очищаем окно вывода от старой инфы
        window.FindElement("data_output").Update('')
        login = values['orderid']
        window_location = window.CurrentLocation()
        window_x = window_location[0] + 340
        window_y = window_location[1] + 250
        
        if work_id == 0:
            loading_animation = threading.Thread(target = check_inex_generate, args=(work_id, gui_queue, login,), daemon = True)
            loading_animation.start()
            work_id = 1   

    try:
        message = gui_queue.get_nowait()  # смотрим, было ли что-то размещено в очереди
    except queue.Empty:  # get_nowait() получит исключение, когда очередь пуста
        message = None   
    if message is not None:
        work_id = 0
        if not work_id:
            sg.PopupAnimated(None)
            loading_animation.join()
    # рисуем котика
    if work_id:
        sg.PopupAnimated('loading.gif', background_color = 'white', transparent_color = 'white', keep_on_top = False, grab_anywhere = True, time_between_frames = 100, location = (window_x, window_y))# keep_on_top = False, grab_anywhere = False,
    # очистка окна
    if event in (None, 'Clear'):
        # очищаем окно вывода от старой инфы
        window.FindElement("data_output").Update('')
   # обрабатываем значение списка типа ответа 
    if event in (None, 'Выбрать'):
        for i in range(len(type)):
            if values['drop_list_1'] == type[i]:
                new_vel = subtype[i]
                window.FindElement('drop_list_2').update(values = new_vel)
    # обрабатываем значение списка подтипа ответа 			
    if event in (None, 'Добавить'):
        #print(values)# отладочка
        try:
            dop_answer = drop_dict.get(values['drop_list_1']).get(values['drop_list_2'])
            if dop_answer == None:
                None
            else:
                print()
                print(dop_answer)
        except:
            None
    if event in (None, 'Exit') or event == sg.WIN_CLOSED:
        window.close()
        break