import asyncio

import telebot
import wikipedia
from pyowm.utils.config import get_default_config
from telebot import types
from mg import get_map_cell
from pyowm import OWM
from aiogram import Bot, executor, Dispatcher

bot = telebot.TeleBot('5954450073:AAEHyfoJS41_bctnzqaEZ-x8mzX__xLAhVs')
wikipedia.set_lang("ru")

cols, rows = 8, 8
keyboard = telebot.types.InlineKeyboardMarkup()
keyboard.row(telebot.types.InlineKeyboardButton('←', callback_data='left'),
            telebot.types.InlineKeyboardButton('↑', callback_data='up'),
            telebot.types.InlineKeyboardButton('↓', callback_data='down'),
            telebot.types.InlineKeyboardButton('→', callback_data='right'))
maps = {}

def get_map_str(map_cell, player):
    map_str = ""
    for y in range(rows * 2 - 1):
        for x in range(cols * 2 - 1):
            if map_cell[x + y * (cols * 2 - 1)]:
                map_str += "⬛"
            elif (x, y) == player:
                map_str += "🔴"
            else:
                map_str += "⬜"
        map_str += "\n"

    return map_str

@bot.message_handler(commands_types=['play'])
def play_message(message):
    map_cell = get_map_cell(cols, rows)

    user_data = {
        'map': map_cell,
        'x': 0,
        'y': 0
    }
    maps[message.chat.id] = user_data
    bot.send_message(message.from_user.id, get_map_str(map_cell, (0, 0)), reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_func(query):
    user_data = maps[query.message.chat.id]
    new_x, new_y = user_data['x'], user_data['y']

    if query.data == 'left':
        new_x -= 1
    if query.data == 'right':
        new_x += 1
    if query.data == 'up':
        new_y -= 1
    if query.data == 'down':
        new_y += 1

    if new_x < 0 or new_x > 2 * cols - 2 or new_y < 0 or new_y > rows * 2 - 2:
        return None
    if user_data['map'][new_x + new_y * (cols * 2 - 1)]:
        return None

    user_data['x'], user_data['y'] = new_x, new_y

    if new_x == cols * 2 - 2 and new_y == rows * 2 - 2:
        bot.edit_message_text( chat_id=query.message.chat.id,
                               message_id=query.message.id,
                               text="Вы выиграли" )
        return None

    bot.edit_message_text( chat_id=query.message.chat.id,
                           message_id=query.message.id,
                           text=get_map_str(user_data['map'], (new_x, new_y)),
                           reply_markup=keyboard )

@bot.message_handler(commands=['start'])
def start(mess):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    wiki_button = types.KeyboardButton("Википедия")
    game_button = types.KeyboardButton("Игра")
    weather_button = types.KeyboardButton("Погода")

    markup.add(weather_button)
    markup.add(game_button)
    markup.add(wiki_button)

    bot.send_message(mess.chat.id,
                     'Тискай понравившуюся: \n кнопку',
                     reply_markup=markup)

@bot.message_handler(commands=["Wiki"])
def wiki(m):
    mess = bot.send_message(m.chat.id, 'Отправьте мне любое слово, и я найду его значение на Wikipedia')
    bot.register_next_step_handler(mess, getwiki)

def getwiki(message):
    try:
        # ny = wikipedia.page(message)
        # # Получаем первую тысячу символов
        # wikitext = ny.content[:1000]
        # # Разделяем по точкам
        # wikimas = wikitext.split('.')
        # # Отбрасываем все после последней точки
        # wikimas = wikimas[:-1]
        # # Создаем пустую переменную для текста
        # wikitext2 = ''
        # # Проходимся по строкам, где нет знаков «равно» (то есть все, кроме заголовков)
        # for x in wikimas:
        #     if not('==' in x):
        #             # Если в строке осталось больше трех символов, добавляем ее к нашей переменной и возвращаем утерянные при разделении строк точки на место
        #         if (len(( x.strip())) > 3):
        #            wikitext2 = wikitext2+x+'.'
        #     else:
        #         break
        # # Теперь при помощи регулярных выражений убираем разметку
        # wikitext2 = re.sub('\([^()]*\)', '', wikitext2)
        # wikitext2 = re.sub('\([^()]*\)', '', wikitext2)
        # wikitext2 = re.sub('\{[^\{\}]*\}', '', wikitext2)
        # # Возвращаем текстовую строку
        # return wikitext2
        bot.send_message(message.chat.id, wikipedia.summary(message.text, sentences=4))
    except Exception as e:
        bot.send_message(message.chat.id, 'В энциклопедии нет информации об этом')
        print(repr(e))

@bot.message_handler(commands=['weather'])
def weather(message):
    msg = bot.send_message(message.chat.id, 'Напиши мне название своего города:')
    bot.register_next_step_handler(msg, get_weather)

def get_weather(message):
    try:
        config_dict = get_default_config()
        config_dict['language'] = 'ru'
        owm = OWM('ca3ab9ee20c2660513ece79ac3ad8664', config_dict)
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(message.text)
        w = observation.weather
        temperature_dict = w.temperature('celsius')
        wind_dict = w.wind()
        bot.send_message(message.chat.id, 'Температура: ' + str(temperature_dict['temp']) + '°C' + '\nВлажность: ' + str(
            w.humidity) + '%' + '\nВетер: ' + str(wind_dict['speed']) + 'м/c' + '\nСостояние: ' + str(w.detailed_status))
    except Exception as e:
        bot.send_message(message.chat.id, 'Не могу найти такой город 😨')
        print(repr(e))

@bot.message_handler(content_types=["text"])
def output(message):
    if message.text == 'Википедия':
        wiki(message)
    elif message.text == 'Игра':
        play_message(message)
    elif message.text == 'Погода':
        weather(message)
    else:
        bot.send_message(message.chat.id, 'хз братан')

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, 'Вот что я могу:\n'
                                      '/start = начало веселья\n'
                                      '/wiki = википедия\n'
                                      '/game = игра\n'
                                      '/weather = погода\n')

bot.polling(none_stop=True, interval=0)