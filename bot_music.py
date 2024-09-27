import telebot
from telebot import types
import json
import os

# Инициализация бота
bot = telebot.TeleBot('7637080530:AAHS8Saa0M2ic0czpP9mcB20XmHeE8Id4H8')

MUSIC_FILE = 'music_genres.json'

# Загрузка музыки из файла
def load_music():
    if os.path.exists(MUSIC_FILE):
        with open(MUSIC_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {
                    'Pop': [],
                    'Rock': [],
                    'Hip-Hop': [],
                    'Jazz': [],
                    'Classical': [],
                    'Electronic': []
                }
    return {
        'Pop': [],
        'Rock': [],
        'Hip-Hop': [],
        'Jazz': [],
        'Classical': [],
        'Electronic': []
    }

music_genres = load_music()

# Функция для сохранения музыки в файл
def save_music():
    with open(MUSIC_FILE, 'w') as file:
        json.dump(music_genres, file)

# Список для хранения идентификаторов сообщений
message_ids = {}

# Функция для очистки предыдущих сообщений
def clear_chat_history(chat_id):
    if chat_id in message_ids:
        for message_id in message_ids[chat_id]:
            try:
                bot.delete_message(chat_id, message_id)
            except:
                continue
        message_ids[chat_id] = []

# Функция для создания кнопок жанров
def create_genre_buttons():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(genre) for genre in music_genres.keys()]
    buttons.append(types.KeyboardButton('/start'))
    markup.add(*buttons)
    return markup

# Функция для создания кнопок действий
def create_action_buttons():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton('Добавить музыку'),
        types.KeyboardButton('Выбрать музыку')
    ]
    markup.add(*buttons)
    return markup

# Обработчик для выбора жанра при добавлении музыки
def handle_genre_selection_for_adding(message):
    if message.text in music_genres.keys():
        genre = message.text
        clear_chat_history(message.chat.id)
        sent_message = bot.send_message(message.chat.id, f"Пожалуйста, отправьте аудиофайлы для добавления в жанр {genre}. Когда закончите, отправьте /done.")
        message_ids[message.chat.id] = [sent_message.message_id]
        bot.register_next_step_handler(sent_message, handle_multiple_audios, genre, [])
    else:
        sent_message = bot.send_message(message.chat.id, "Пожалуйста, выберите жанр из предложенных вариантов.")
        message_ids[message.chat.id].append(sent_message.message_id)
        bot.register_next_step_handler(sent_message, handle_genre_selection_for_adding)

# Обработчик для загрузки нескольких аудиофайлов
def handle_multiple_audios(message, genre, audio_files):
    if message.text == "/done":
        for audio_file in audio_files:
            music_genres[genre].append({'file_id': audio_file})
        save_music()
        sent_message = bot.send_message(message.chat.id, "Добавление музыки завершено.")
        message_ids[message.chat.id].append(sent_message.message_id)
        sent_message = bot.send_message(message.chat.id, "Выберите действие:", reply_markup=create_action_buttons())
        message_ids[message.chat.id].append(sent_message.message_id)
    elif message.audio:
        audio_files.append(message.audio.file_id)
        sent_message = bot.reply_to(message, f'Музыка добавлена в очередь для жанра {genre}! Отправьте следующий аудиофайл или /done для завершения.')
        message_ids[message.chat.id].append(sent_message.message_id)
        bot.register_next_step_handler(sent_message, handle_multiple_audios, genre, audio_files)
    elif message.document and message.document.mime_type.startswith('audio/'):
        audio_files.append(message.document.file_id)
        sent_message = bot.reply_to(message, f'Музыка добавлена в очередь для жанра {genre}! Отправьте следующий аудиофайл или /done для завершения.')
        message_ids[message.chat.id].append(sent_message.message_id)
        bot.register_next_step_handler(sent_message, handle_multiple_audios, genre, audio_files)
    else:
        sent_message = bot.reply_to(message, 'Пожалуйста, отправьте аудиофайл или /done для завершения.')
        message_ids[message.chat.id].append(sent_message.message_id)
        bot.register_next_step_handler(sent_message, handle_multiple_audios, genre, audio_files)

# Обработчик для команды /start
@bot.message_handler(commands=['start'])
def start(message):
    clear_chat_history(message.chat.id)
    sent_message = bot.send_message(message.chat.id, "Выберите действие:", reply_markup=create_action_buttons())
    message_ids[message.chat.id] = [sent_message.message_id]

# Обработчик для выбора действия
@bot.message_handler(func=lambda message: message.text in ['Добавить музыку', 'Выбрать музыку'])
def handle_action_selection(message):
    if message.text == 'Добавить музыку':
        clear_chat_history(message.chat.id)
        sent_message = bot.send_message(message.chat.id, "Выберите жанр для добавления музыки:", reply_markup=create_genre_buttons())
        message_ids[message.chat.id] = [sent_message.message_id]
        bot.register_next_step_handler(sent_message, handle_genre_selection_for_adding)
    elif message.text == 'Выбрать музыку':
        clear_chat_history(message.chat.id)
        sent_message = bot.send_message(message.chat.id, "Выберите жанр для прослушивания музыки:", reply_markup=create_genre_buttons())
        message_ids[message.chat.id] = [sent_message.message_id]

# Обработчик для выбора жанра при прослушивании музыки
@bot.message_handler(func=lambda message: message.text in music_genres.keys())
def handle_genre_selection_for_listening(message):
    genre = message.text
    clear_chat_history(message.chat.id)
    sent_message = bot.send_message(message.chat.id, f"Вы выбрали жанр {genre}.")
    message_ids[message.chat.id] = [sent_message.message_id]
    
    if not music_genres[genre]:
        sent_message = bot.send_message(message.chat.id, f"К сожалению, в жанре {genre} пока нет песен.")
        message_ids[message.chat.id].append(sent_message.message_id)
    else:
        for song in music_genres[genre]:
            try:
                sent_audio = bot.send_audio(message.chat.id, song['file_id'])
                message_ids[message.chat.id].append(sent_audio.message_id)
            except Exception as e:
                print(f"Ошибка при отправке аудио: {e}")
    
    sent_message = bot.send_message(message.chat.id, "Выберите действие:", reply_markup=create_action_buttons())
    message_ids[message.chat.id].append(sent_message.message_id)

# Запуск бота
bot.polling()
