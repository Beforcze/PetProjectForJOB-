import telebot
from telebot import types
import random
import string
import mysql.connector
from mysql.connector import Error


bot = telebot.TeleBot('7323668827:AAFBrmq9K08ofKw8gP_5vBlFOZTFBMgR4HI')

# Параметры подключения к базе данных MySQL
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'my_database'
DB_USER = 'my_user'
DB_PASSWORD = 'my_password'

# Функция для получения подключения к базе данных
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

# Функция для генерации случайного пароля
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

# Словарь для хранения состояния пользователя (сайт и сгенерированный пароль)
user_states = {}

# Функция для отображения основной клавиатуры
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=5, resize_keyboard=True)
    button_yes = types.KeyboardButton('Сгенерировать пароль')
    button_clear_passwords = types.KeyboardButton('Очистить пароли')
    button_clear_chat = types.KeyboardButton('Очистить чат')
    button_view_passwords = types.KeyboardButton('Просмотреть пароли')
    markup.add(button_yes, button_clear_passwords, button_clear_chat, button_view_passwords)
    bot.send_message(chat_id, 'Выберите действие:', reply_markup=markup)

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    show_main_menu(message.chat.id)

# Обработка команды /mysite
@bot.message_handler(commands=['mysite'])
def site(message):
    bot.send_message(message.chat.id, 'Первый сайт - https://youtube.com')

# Обработка команды /help
@bot.message_handler(commands=['help'])
def info(message):
    bot.send_message(message.chat.id, 'Этот бот создан с целью генерировать и сохранять пароли пользователей. '
                                      'Создан как пет проект, или по нормальному сленгу человеческому - просто так.')

# Обработка сообщения с текстом "Да, сохраним пароль"
@bot.message_handler(func=lambda message: message.text.lower() == 'сгенерировать пароль')
def handle_save_request(message):
    # Запрашиваем у пользователя сайт
    bot.send_message(message.chat.id, 'Введите название сайта для пароля:')
    bot.register_next_step_handler(message, process_website)

# Обработка ввода сайта
def process_website(message):
    user_id = message.from_user.id
    website = message.text.strip()
    password = generate_random_password()
    
    # Сохраняем сайт и пароль в состояние пользователя
    user_states[user_id] = {'website': website, 'password': password}

    # Создаем клавиатуру для подтверждения сохранения пароля
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    button_yes = types.KeyboardButton('Да, сохранить')
    button_no = types.KeyboardButton('Нет, отменить')
    button_back = types.KeyboardButton('Назад')
    markup.add(button_yes, button_no, button_back)

    # Отправляем пользователю сообщение с сгенерированным паролем и сайтом
    bot.send_message(message.chat.id, f'Ваш сгенерированный пароль для сайта {website}:  {password}\nСохраняем?', reply_markup=markup)

# Обработка сообщения с текстом "Да, сохранить"
@bot.message_handler(func=lambda message: message.text.lower() == 'да, сохранить')
def handle_save_password(message):
    user_id = message.from_user.id
    data = user_states.get(user_id)
    
    if data:
        website = data['website']
        password = data['password']
        conn = get_db_connection()
        
        if conn:
            try:
                cursor = conn.cursor()
                # Вставляем сайт и пароль в базу данных
                cursor.execute(
                    "INSERT INTO user_passwords (user_id, website, password) VALUES (%s, %s, %s)",
                    (user_id, website, password)
                )
                conn.commit()
                cursor.close()
                bot.send_message(message.chat.id, f'Пароль для сайта {website}: {password}')
                bot.send_message(message.chat.id, 'Пароль сохранен!')
                user_states.pop(user_id, None)
                show_main_menu(message.chat.id)
            except Error as e:
                print(f"Ошибка выполнения запроса к базе данных: {e}")
            finally:
                conn.close()
        else:
            bot.send_message(message.chat.id, 'Не удалось подключиться к базе данных.')
    else:
        bot.send_message(message.chat.id, 'Информация о пароле не найдена. Попробуйте снова.')

# Обработка сообщения с текстом "Нет, отменить"
@bot.message_handler(func=lambda message: message.text.lower() == 'нет, отменить')
def handle_cancel_password(message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)
    bot.send_message(message.chat.id, 'Операция отменена. Пароль не будет сохранен.')
    show_main_menu(message.chat.id)

# Обработка сообщения с текстом "Нет"
@bot.message_handler(func=lambda message: message.text.lower() == 'нет')
def handle_cancel(message):
    bot.send_message(message.chat.id, 'Операция отменена. Пароль не будет сохранен.')
    show_main_menu(message.chat.id)

# Обработка сообщения с текстом "Очистить пароли"
@bot.message_handler(func=lambda message: message.text.lower() == 'очистить пароли')
def handle_clear(message):
    user_id = message.from_user.id
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_passwords WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            bot.send_message(message.chat.id, 'Все сохраненные пароли удалены.')
        except Error as e:
            print(f"Ошибка выполнения запроса к базе данных: {e}")
        finally:
            conn.close()
    else:
        bot.send_message(message.chat.id, 'Не удалось подключиться к базе данных.')
    show_main_menu(message.chat.id)

# Обработка сообщения с текстом "Просмотреть пароли"
@bot.message_handler(func=lambda message: message.text.lower() == 'просмотреть пароли')
def view_passwords(message):
    user_id = message.from_user.id
    conn = get_db_connection()
    
    if conn:
        try:
            cursor = conn.cursor()
            # Извлекаем сайты и пароли пользователя из базы данных
            cursor.execute("SELECT website, password FROM user_passwords WHERE user_id = %s", (user_id,))
            records = cursor.fetchall()
            cursor.close()
            
            if records:
                # Формируем список паролей с сайтами
                password_list = "\n".join([f"{website}: {password}" for website, password in records])
                bot.send_message(message.chat.id, f"Ваши сохраненные пароли:\n{password_list}")
            else:
                bot.send_message(message.chat.id, 'Нет сохраненных паролей.')
        except Error as e:
            print(f"Ошибка выполнения запроса к базе данных: {e}")
        finally:
            conn.close()
    else:
        bot.send_message(message.chat.id, 'Не удалось подключиться к базе данных.')

# Обработка сообщения с текстом "Очистить чат"
@bot.message_handler(func=lambda message: message.text.lower() == 'очистить чат')
def delete_messages(message):
    chat_id = message.chat.id
    message_id = message.message_id

    # Удаляем сообщение с кнопкой "Очистить чат"
    bot.delete_message(chat_id, message_id)

    # Попытка удалить несколько предыдущих сообщений (например, последние 30)
    for i in range(1, 30):
        try:
            bot.delete_message(chat_id, message_id - i)
        except Exception as e:
            print(f"Не удалось удалить сообщение {message_id - i}: {e}")

    show_main_menu(chat_id)

# Обработка сообщения с текстом "Назад"
@bot.message_handler(func=lambda message: message.text.lower() == 'назад')
def cancel(message):
    show_main_menu(message.chat.id)

# Обработка всех остальных сообщений
@bot.message_handler(func=lambda message: True)
def default_response(message):
    bot.send_message(message.chat.id, 'Я не понимаю. Нажмите "Да, сохраним пароль" для генерации и сохранения пароля.')

bot.polling(none_stop=True)