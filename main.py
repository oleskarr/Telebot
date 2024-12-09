from telegram import Bot
import json
import os
from datetime import datetime
import logging
import re
from telegram import (
    Bot,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    Contact
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)

import os

# Проверка существования файла
if not os.path.exists('zk-picture.jpg'):
    logging.error("Файл 'zk-picture.jpg' не найден.")
# Токены и ID чатов
MAIN_BOT_TOKEN = '7209568265:AAExH1wBnBOAtNFu3m0gRcd4xUv3hikav7U'
NOTIFICATION_BOT_TOKEN = '6874321311:AAHWMKv35bgYknrme_oMcpWAjH9vgVf9UgY'
LOG_FILE = 'user_log.json'
CHAT_ID = '-1002177666021'
 

firstqu = [
    ("Уточните, что вы хотите отобразить в каталоге? Выберете интересующие Вас площади (можно несколько вариантов)", ["Студия - 1К квартира", "2К квартира", "3К квартира", "4К и более квартира"]),
    ("Какой этаж интересует?", ["Первый", "Посередине", "Верхние"]),
    ("Какая форма оплаты?", ["Наличные (рассрочка)", "Ипотека-Господдержка", "Нужна консультация по условиям"])
]
secondqu = [
    ("Цель приобретения (можно один или несколько)", ["Для собственного проживания", "С целью последующей перепродажи", "Длительное инвестирование и/или для сдачи", "Детям, родителям, близким"]),
    ("Выберите районы (можно один или несколько)", ["Южный берег Крыма", "Керченский полуостров", "Центральная равнина", "Каламитский залив", "Нужна помощь, чтобы разобраться"]),
    ("Выберите степень готовности дома (можно один или несколько)", ["Проект или начало строительства ФЗ-214", "Строительство ФЗ-214 (сдача ближайшие 2-4 года)", "На этапе сдачи в эксплуатацию ФЗ-214", "Сдан"]),
    ("Инфраструктура рядом с ЖК (можно один или несколько)", ["Детский сад, школа, поликлиника, тц", "Вдали от суеты и шума", "Близость к морю", "В горах и лесной местности"])
]

# Словарь для хранения ответов пользователей
user_answers = {}

# Создание файла лога, если его не существует
def ensure_log_file():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as file:
            json.dump([], file)
    os.chmod(LOG_FILE, 0o666)

ensure_log_file()

# Логирование информации о пользователе
async def log_user_info(user, chat_id):
    try:
        user_info = {
            'user_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username if user.username else f"ID_{user.id}",
            'language_code': user.language_code,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'answers': user_answers[chat_id]['answers'],
            'phone_number': user_answers[chat_id]['phone_number']
        }
        with open(LOG_FILE, 'r') as file:
            data = json.load(file)
        data.append(user_info)
        with open(LOG_FILE, 'w') as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        logging.error(f"Ошибка при работе с файлом логирования: {e}")

# Отправка уведомления администратору о новом пользователе
async def send_notification(user, chat_id):
    try:
        notification_bot = Bot(token=NOTIFICATION_BOT_TOKEN)
        username_or_id = f"@{user.username}" if user.username else f"ID_{user.id}"
        initial_choice = user_answers[chat_id].get('initial_choice', 'Выбор не указан')  # Теперь это будет указано
        message = (
            f"Новый пользователь ЖК Скай-Плаза бот:\n"
    f"Имя: {user_answers[chat_id]['name']}\n"  # Обновляем здесь
    f"Username/ID: {username_or_id}\n"
    f"Язык: {user.language_code}\n"
    f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    f"Начальный выбор: {initial_choice}\n"
    f"Ответы: {user_answers[chat_id]['answers']}\n"
    f"Номер телефона: {user_answers[chat_id]['phone_number']}"
        )
        await notification_bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления: {e}")
       



# Функция для отправки приветственного сообщения
async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('Собрать каталог по жк', callback_data='catalog')],
        [InlineKeyboardButton('Получить только презентацию', callback_data='presentation')],
        [InlineKeyboardButton('Сравнить ЖК Крыма', callback_data='compare')]
    ])

    # Отправляем фото с текстом
    await context.bot.send_photo(
        chat_id=chat_id, 
        photo='.\zk-picture.jpg', 
        caption="ЖК Скай Плаза Ялта, приветствует Вас!"
    )

    # Отправляем текстовое сообщение после фото
    await context.bot.send_message(
        chat_id,
        f"Здравствуйте, {update.message.from_user.first_name}!\n"
        f"Я помогу собрать тебе информацию по ЖК Скай Плаза Ялта!\n"
        f"Настройте самостоятельно каталог, чтобы получить условия, цены, планировку и презентацию ЖК. "
        f"Бонусом Вы получите доступ в полный каталог ЖК Крыма! 🔥🔥",
        reply_markup=markup
    )

# Функция для отправки изображения


# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.message.chat.id
    if chat_id not in user_answers:
        user_answers[chat_id] = {
            'name': user.first_name,
            'user_id': user.id,
            'answers': [],
            'registered': False,
            'awaiting_phone': False,
            'phone_number': None
        }
    if not user_answers[chat_id]['registered']:
        await log_user_info(user, chat_id)
        
        
    else:
        await update.message.reply_text(f"С возвращением, {user.first_name}!")
    await send_welcome_message(update, context)

# Функция для отправки вопросов пользователю
# Функция для отправки вопросов пользователю
async def send_question(bot: Bot, chat_id, question_index, question_list):
    question, options = question_list[question_index]
    keyboard = [
        [InlineKeyboardButton(option, callback_data=f"select_{question_index}_{i}")]
        for i, option in enumerate(options)
    ]
    keyboard.append([InlineKeyboardButton("Продолжить", callback_data=f"continue_{question_index}")])
    markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(chat_id, question, reply_markup=markup)

# Обработка callback-запросов
async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat.id
    await query.answer()

    if query.data.startswith('catalog'):
        user_answers[chat_id]['initial_choice'] = 'Собрать каталог по жк'  # Сохранение начального выбора
        await send_question(context.bot, chat_id, 0, firstqu)  # Передаем массив firstqu
    elif query.data.startswith('presentation'):
        user_answers[chat_id]['initial_choice'] = 'Получить только презентацию'  # Сохранение начального выбора
        user_answers[chat_id]['awaiting_phone'] = True
        await context.bot.send_message(
            chat_id,
            'Для отправки вам презентации нажмите кнопку «Отправить номер» или введите его самостоятельно',
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton('Отправить номер ', request_contact=True)]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
    elif query.data.startswith('compare'):
        user_answers[chat_id]['initial_choice'] = 'Сравнить ЖК Крыма'  # Сохранение начального выбора
        await send_question(context.bot, chat_id, 0, secondqu)  # Отправляем вопросы из secondqu
    elif query.data.startswith('select_'):
        question_index, option_index = map(int, query.data.split("_")[1:])
        current_question_list = firstqu if user_answers[chat_id]['initial_choice'] == 'Собрать каталог по жк' else secondqu
        option = current_question_list[question_index][1][option_index]
        if option not in user_answers[chat_id]['answers']:
            user_answers[chat_id]['answers'].append(option)
        await query.edit_message_text(
            f"Вы выбрали: {', '.join(user_answers[chat_id]['answers'])}\nВы можете выбрать ещё варианты или нажать 'Продолжить'.",
            reply_markup=query.message.reply_markup
        )
    elif query.data.startswith('continue_'):
        question_index = int(query.data.split("_")[1])
        current_question_list = firstqu if user_answers[chat_id]['initial_choice'] == 'Собрать каталог по жк' else secondqu
        if question_index < len(current_question_list) - 1:
            await send_question(context.bot, chat_id, question_index + 1, current_question_list)
        else:
            user_answers[chat_id]['awaiting_phone'] = True
            await context.bot.send_message(
                chat_id,
                'Для отправки подборки нажмите кнопку «Отправить номер» или введите его самостоятельно',
                reply_markup=ReplyKeyboardMarkup(
                    [[KeyboardButton('Отправить номер', request_contact=True)]],
                    one_time_keyboard=True,
                    resize_keyboard=True
                )
            )


# Проверка корректности номера телефона
def is_valid_phone_number(phone_number):
    pattern = re.compile(r'^\+?\d{10,15}$')
    return pattern.match(phone_number) is not None

# Обработка сообщений от пользователя
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    user = update.message.from_user  # Получение информации о пользователе
    username = user.username  # Получение имени пользователя

    if chat_id not in user_answers:
        user_answers[chat_id] = {'answers': [], 'registered': False}  # Инициализация состояния пользователя

    if username:  # Если имя пользователя доступно
        user_answers[chat_id]['username'] = username  # Сохранение имени пользователя в состоянии
    else:
        user_answers[chat_id]['username'] = "Не указано"  # Обработка случая, если имя пользователя отсутствует

    if chat_id in user_answers:
        user_state = user_answers[chat_id]

        if user_state.get('awaiting_phone'):
            if update.message.contact:  # Обработка контакта
                contact: Contact = update.message.contact
                phone_number = contact.phone_number
            else:  # Обработка текста
                phone_number = update.message.text

            if is_valid_phone_number(phone_number):
                user_state['phone_number'] = phone_number
                user_state['awaiting_phone'] = False

                # Запрос имени пользователя
                await context.bot.send_message(
                    chat_id,
                    'Спасибо! Теперь укажите ваше имя:'
                )
                user_state['awaiting_name'] = True  # Устанавливаем флаг ожидания имени
            else:
                await context.bot.send_message(
                    chat_id,
                    'Пожалуйста, введите корректный номер телефона или отправьте контакт.'
                )
        
        elif user_state.get('awaiting_name'):
            user_state['name'] = update.message.text  # Сохраняем введённое имя
            user_state['awaiting_name'] = False  # Сбрасываем флаг ожидания имени

            await context.bot.send_message(
                chat_id,
                f'Спасибо, {user_state["name"]}! Мы свяжемся с вами в ближайшее время.',
                reply_markup=ReplyKeyboardMarkup([[]], one_time_keyboard=True)
            )

            # Отправка уведомления администратору после завершения опроса и получения имени
            await send_notification(user, chat_id)
            user_answers[chat_id]['registered'] = True

# Отправка данных второму боту


# Создание приложения
application = ApplicationBuilder().token(MAIN_BOT_TOKEN).build()

# Регистрация обработчиков
application.add_handler(CommandHandler('start', start))
application.add_handler(CallbackQueryHandler(handle_query))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(MessageHandler(filters.CONTACT, handle_message))

# Запуск бота
if __name__ == '__main__':
    application.run_polling()