from pathlib import Path

import telebot
import logging
from telebot import types

from recognition_module.pandas_work_with_file import recognition_main, delete_temp_files
from settings import config_class

logger = logging.getLogger(__name__)

START_MESSAGE = '''Я твой бот-помощник, для получения данных из сканированного pdf документа. 
Весь функционал реализован на кнопках, ничего писать в чат не нужно. \n
Инструкция следующая:\n
1. Нажать на кнопку "Получить данные со сканированного изображения"\n
2. Далее необходимо выбрать кнопку наклона изображения. От наклона зависит распознавание текста, 
если он выбран неверно - данные не будут получены или будут ошибочными. Если ошибочно была нажата кнопка наклона, 
всегда можно начать сначала выбрав кнопку "/start" или написать данную команду в чат.\n
3. После выбора наклона, кнопки не исчезнут и не изменятся. Необходимо вложить/добавить в чат скан в формате PDF.\n
4. Примерное время обработки 1 листа - 1 минута, после чего в чат будет добавлен excel файл, с таким же именем, как у скана.\n
'''

ERROR_STR = '''Возникла ошибка! Пожалуйста убедитесь что все действия были выполнены по инструкции, описанной в стартовом сообщении.
Если инструкция не была нарушена, попробуйте пожалуйста другой файл. Выполняется перезапуск'''

TEXT_START = "Получить данные со сканированного изображения"
TEXT_R1 = "Повернуто на 90 градусов влево"
TEXT_R2 = "Перевёрнуто"
TEXT_R3 = "Повернуто на 90 градусов вправо"
TEXT_R4 = "Изображение не наклонено"


bot = telebot.TeleBot(config_class.telebot_config.token)


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton(TEXT_START)
    btn2 = types.KeyboardButton('/start')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id,
                     text=f"Привет, {message.from_user.first_name}! {START_MESSAGE}",
                     reply_markup=markup)
    logger.info(f"{message.from_user.username} подключился к боту")


@bot.message_handler(content_types=['text'])
def func(message):
    try:
        if message.text == TEXT_START:
            rotation_button(message)
        elif message.text.lower().strip() == 'привет':
            bot.send_message(message.chat.id, 'Отлично выглядишь! А теперь выберем кнопку задания')
        else:
            bot.send_message(message.chat.id, 'Пожалуйста не пишите ничего в чат и следуйте инструкции. Запускаюсь заново')
            logger.info(f"{message.from_user.username} прислал текст - {message.text}")
            start(message)
    except Exception as e:
        logger.error(f'{message} - {e}')
        bot.send_message(message.chat.id, ERROR_STR)
        start(message)


@bot.message_handler(commands=['button'])
def rotation_button(message):
    if message.text == TEXT_START:
        try:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            btn1 = types.KeyboardButton(TEXT_R1)
            btn2 = types.KeyboardButton(TEXT_R2)
            btn3 = types.KeyboardButton(TEXT_R3)
            btn4 = types.KeyboardButton(TEXT_R4)
            markup.add(btn1, btn2, btn3, btn4)
            bot.send_message(message.chat.id, text='Выберете наклон изображения, от него зависит распознавание',
                             reply_markup=markup)
            bot.register_next_step_handler(message, get_rotation)
        except Exception as e:
            logger.error(f'{message} - {e}')
            bot.send_message(message.chat.id, ERROR_STR)
            start(message)


@bot.message_handler(content_types=['text'])
def get_rotation(message):
    try:
        rotation = {
            TEXT_R1: 270,
            TEXT_R2: 180,
            TEXT_R3: 90,
            TEXT_R4: 0
        }
        logger.info(f'{message.from_user.username} - выбрал следующий наклон: {message.text}')
        degree_of_rotation = rotation[message.text]
        bot.send_message(message.chat.id, 'Загрузите пожалуйста ОДИН pdf-файл')
        bot.register_next_step_handler(message, pdf_to_excel, degree_of_rotation)
    except Exception as e:
        logger.error(f'{message} - {e}')
        bot.send_message(message.chat.id, ERROR_STR)
        start(message)


@bot.message_handler(content_types=['document'])
def pdf_to_excel(message, degree_of_rotation):
    try:
        file_info = bot.get_file(message.document.file_id)
        logger.info(f'{message.from_user.username} - отправил следующий файл: {message.document.file_name}')
        downloaded_file = bot.download_file(file_info.file_path)
        downloaded_file_path = config_class.path_project.temp_dir + f'\{message.document.file_name}'
        with open(downloaded_file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, f"Приступил к обработке {message.document.file_name}, подождите пожалуйста несколько минут")
        recognized_file = recognition_main(downloaded_file_path, degree_of_rotation)
        with open(recognized_file, 'rb') as excel:
            bot.send_document(message.chat.id, excel)
        bot.send_message(message.chat.id, 'PDF обработан, данные в excel файле. Прекрасного дня!')
        logger.info(f'Отправил пользователю {message.from_user.username} файл: {recognized_file}')
        delete_temp_files(downloaded_file_path, recognized_file)
        start(message)
    except Exception as e:
        logger.error(f'{message} - {e}')
        bot.send_message(message.chat.id, ERROR_STR)
        start(message)