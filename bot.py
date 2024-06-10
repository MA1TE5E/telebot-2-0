import os
import logging
import telebot
import csv
from telebot import types
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levellevel)s - %(message)s')
logger = logging.getLogger(__name__)

# Вставьте сюда токен своего бота
API_TOKEN = '7322233778:AAHxgxNC_6dRnsJJeXhlyyw4ajBPu4ELUEk'
bot = telebot.TeleBot(API_TOKEN)

# Папки для сохранения изображений
IMAGE_FOLDER = 'images'
ANNOTATED_IMAGE_FOLDER = 'annotated_images'
CSV_FILE_PATH = 'weld_defects.csv'
WEB_APP_URL = 'http://maltesers.pythonanywhere.com/draw.html?image='

# Убедимся, что папки существуют
os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(ANNOTATED_IMAGE_FOLDER, exist_ok=True)

# Убедимся, что CSV файл существует
if not os.path.exists(CSV_FILE_PATH):
    with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'ФИО',
            'Должность',
            'Вид сварки',
            'Тип покрытия электрода',
            'Марка электрода',
            'Диаметр электрода',
            'Тип соединения',
            'Пространственное положение сварки',
            'Сила тока',
            'Ссылка на изображение',
            'Ссылка на аннотированное изображение'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

# Хранилище состояний и данных пользователей
user_data = {}

# Состояния для процесса логина и получения информации о сварке
STATE_NONE = 0
STATE_WAITING_FOR_FIO = 1
STATE_WAITING_FOR_POSITION = 2
STATE_WAITING_FOR_COMMAND = 3
STATE_WAITING_FOR_SET_WELDING_PARAMS = 4
STATE_WAITING_FOR_IMAGE = 5
STATE_WAITING_FOR_DRAWN_IMAGE = 6

# Состояния для установки параметров сварки
STATE_WAITING_FOR_WELDING_TYPE = 10
STATE_WAITING_FOR_COVERAGE_TYPE = 11
STATE_WAITING_FOR_ELECTRODE_BRAND = 12
STATE_WAITING_FOR_ELECTRODE_DIAMETER = 13
STATE_WAITING_FOR_CONNECTION_TYPE = 14
STATE_WAITING_FOR_WELDING_POSITION = 15
STATE_WAITING_FOR_CURRENT = 16

# Функция для создания главного меню
def create_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("📙 About"),
        types.KeyboardButton("📄 Types"),
        types.KeyboardButton("🆘 Help"),
        types.KeyboardButton("⁉️ FAQ"),
        types.KeyboardButton("🗾 Отправить изображение"),
        types.KeyboardButton("⚙️ Установить параметры сварки")
    )
    return markup

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data[message.chat.id] = {"state": STATE_WAITING_FOR_FIO}
    bot.send_message(message.chat.id, "Добро пожаловать! Пожалуйста, введите ваше ФИО:")
    logger.info(f"User {message.chat.id} started the bot and is asked for FIO.")

# Обработчик для кнопок меню
@bot.message_handler(func=lambda message: message.text in ["📙 About", "📄 Types", "🆘 Help", "⁉️ FAQ", "🗾 Отправить изображение", "⚙️ Установить параметры сварки"])
def handle_menu_buttons(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "Пожалуйста, начните с команды /start")
        return

    if message.text == "📙 About":
        bot.send_message(chat_id, "🤖 *WeldDefectBot* - это телеграм-бот, разработанный для анализа дефектов сварных швов...", parse_mode="Markdown")
    elif message.text == "📄 Types":
        bot.send_message(chat_id, "Я умею определять такие дефекты как:...", parse_mode="Markdown")
    elif message.text == "🆘 Help":
        bot.send_message(chat_id, "Просто отправь мне фотографию сварного шва.\n\nКак пользоваться ботом:...", parse_mode="Markdown")
    elif message.text == "⁉️ FAQ":
        bot.send_message(chat_id, "❓ *Часто задаваемые вопросы*\n\n1. Какой тип фотографий лучше всего подходит для анализа?...", parse_mode="Markdown")
    elif message.text == "🗾 Отправить изображение":
        if "welding_params" in user_data[chat_id]:
            user_data[chat_id]["state"] = STATE_WAITING_FOR_IMAGE
            bot.send_message(chat_id, "Теперь отправьте изображение:")
        else:
            user_data[chat_id]["state"] = STATE_WAITING_FOR_SET_WELDING_PARAMS
            bot.send_message(chat_id, "Пожалуйста, сначала установите параметры сварки.")
    elif message.text == "⚙️ Установить параметры сварки":
        user_data[chat_id]["state"] = STATE_WAITING_FOR_WELDING_TYPE
        bot.send_message(chat_id, "Вид сварки:")
        logger.info(f"User {chat_id} is asked for welding type.")

# Обработчик для текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        bot.send_message(chat_id, "Пожалуйста, начните с команды /start")
        return

    state = user_data[chat_id].get("state", STATE_NONE)

    if state == STATE_WAITING_FOR_FIO:
        user_data[chat_id]["fio"] = message.text
        user_data[chat_id]["state"] = STATE_WAITING_FOR_POSITION
        bot.send_message(chat_id, "Введите вашу должность:")
        logger.info(f"User {chat_id} provided FIO: {message.text}.")
    elif state == STATE_WAITING_FOR_POSITION:
        user_data[chat_id]["position"] = message.text
        user_data[chat_id]["state"] = STATE_WAITING_FOR_COMMAND
        bot.send_message(chat_id, "Регистрация завершена. Выберите опцию из меню ниже:", reply_markup=create_main_menu())
        logger.info(f"User {chat_id} provided position: {message.text}.")
    elif state == STATE_WAITING_FOR_WELDING_TYPE:
        user_data[chat_id].setdefault("welding_params", {})["welding_type"] = message.text
        user_data[chat_id]["state"] = STATE_WAITING_FOR_COVERAGE_TYPE
        bot.send_message(chat_id, "Тип покрытия электрода:")
        logger.info(f"User {chat_id} provided welding type: {message.text}.")
    elif state == STATE_WAITING_FOR_COVERAGE_TYPE:
        user_data[chat_id]["welding_params"]["coverage_type"] = message.text
        user_data[chat_id]["state"] = STATE_WAITING_FOR_ELECTRODE_BRAND
        bot.send_message(chat_id, "Марка электрода:")
        logger.info(f"User {chat_id} provided coverage type: {message.text}.")
    elif state == STATE_WAITING_FOR_ELECTRODE_BRAND:
        user_data[chat_id]["welding_params"]["electrode_brand"] = message.text
        user_data[chat_id]["state"] = STATE_WAITING_FOR_ELECTRODE_DIAMETER
        bot.send_message(chat_id, "Диаметр электрода:")
        logger.info(f"User {chat_id} provided electrode brand: {message.text}.")
    elif state == STATE_WAITING_FOR_ELECTRODE_DIAMETER:
        user_data[chat_id]["welding_params"]["electrode_diameter"] = message.text
        user_data[chat_id]["state"] = STATE_WAITING_FOR_CONNECTION_TYPE
        bot.send_message(chat_id, "Тип соединения:")
        logger.info(f"User {chat_id} provided electrode diameter: {message.text}.")
    elif state == STATE_WAITING_FOR_CONNECTION_TYPE:
        user_data[chat_id]["welding_params"]["connection_type"] = message.text
        user_data[chat_id]["state"] = STATE_WAITING_FOR_WELDING_POSITION
        bot.send_message(chat_id, "Пространственное положение сварки:")
        logger.info(f"User {chat_id} provided connection type: {message.text}.")
    elif state == STATE_WAITING_FOR_WELDING_POSITION:
        user_data[chat_id]["welding_params"]["welding_position"] = message.text
        user_data[chat_id]["state"] = STATE_WAITING_FOR_CURRENT
        bot.send_message(chat_id, "Сила тока:")
        logger.info(f"User {chat_id} provided welding position: {message.text}.")
    elif state == STATE_WAITING_FOR_CURRENT:
        user_data[chat_id]["welding_params"]["current"] = message.text
        user_data[chat_id]["state"] = STATE_WAITING_FOR_COMMAND
        bot.send_message(chat_id, "Параметры сварки установлены. Выберите опцию из меню ниже:", reply_markup=create_main_menu())
        logger.info(f"User {chat_id} provided current: {message.text}.")
    elif state == STATE_WAITING_FOR_IMAGE:
        handle_image(message)

# Обработчик для приема изображений
@bot.message_handler(content_types=['photo'])
def handle_image(message):
    chat_id = message.chat.id
    state = user_data.get(chat_id, {}).get("state", STATE_NONE)

    if state == STATE_WAITING_FOR_IMAGE:
        try:
            # Получаем file_id самого большого изображения (наивысшего качества)
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)

            # Сохраняем изображение и отправляем ответ пользователю
            file_path = save_image(file_info, file_id)
            if file_path:
                # Убедитесь, что image_path сохраняется
                if chat_id not in user_data:
                    user_data[chat_id] = {}
                user_data[chat_id]["image_path"] = file_path
                logger.info(f"Image path saved for user {chat_id}: {file_path}")
                print(f"DEBUG: Image path for user {chat_id} is {user_data[chat_id]['image_path']}")

                # Формируем URL для веб-приложения с параметром изображения
                image_url = f"{WEB_APP_URL}{file_path}"
                bot.send_message(chat_id, f"Изображение получено. Перейдите по ссылке для обозначения дефектов: {image_url}")
                user_data[chat_id]["state"] = STATE_WAITING_FOR_DRAWN_IMAGE
                bot.send_message(chat_id, "Теперь отправьте аннотированное изображение.")
                logger.info(f"Image received and saved as {file_path}. User {chat_id} is asked for annotated image.")
            else:
                bot.send_message(chat_id, "Произошла ошибка при сохранении изображения.")
                logger.error(f"Failed to save image for user {chat_id}.")
        except Exception as e:
            logger.error(f"Error handling image for user {chat_id}: {e}")
            bot.send_message(chat_id, "Произошла ошибка при обработке изображения.")
    elif state == STATE_WAITING_FOR_DRAWN_IMAGE:
        handle_annotated_image(message)

# Обработчик для приема аннотированных изображений
@bot.message_handler(content_types=['document', 'photo'])
def handle_annotated_image(message):
    chat_id = message.chat.id
    state = user_data.get(chat_id, {}).get("state", STATE_NONE)

    if state != STATE_WAITING_FOR_DRAWN_IMAGE:
        bot.send_message(chat_id, "Пожалуйста, следуйте инструкциям и отправьте аннотированное изображение, когда это необходимо.")
        return

    try:
        # Логирование перед проверкой 'image_path'
        logger.info(f"Checking for image_path for user {chat_id}")
        print(f"DEBUG: Checking for image_path for user {chat_id}")

        # Проверьте, существует ли 'image_path' в user_data
        if 'image_path' not in user_data[chat_id]:
            bot.send_message(chat_id, "Изображение не найдено. Пожалуйста, начните сначала.")
            logger.error(f"No image path found for user {chat_id} when receiving annotated image.")
            print(f"DEBUG: No image path found for user {chat_id} in user_data")
            return

        # Логирование значения 'image_path'
        logger.info(f"Image path for user {chat_id}: {user_data[chat_id]['image_path']}")
        print(f"DEBUG: Image path for user {chat_id}: {user_data[chat_id]['image_path']}")

        # Получаем file_id самого большого изображения (наивысшего качества)
        file_id = message.photo[-1].file_id if message.content_type == 'photo' else message.document.file_id
        file_info = bot.get_file(file_id)

        # Сохраняем аннотированное изображение и отправляем ответ пользователю
        annotated_file_path = save_annotated_image(file_info, user_data[chat_id]["image_path"])
        if annotated_file_path:
            user_data[chat_id]["annotated_image_path"] = annotated_file_path
            bot.send_message(chat_id, "Аннотированное изображение получено. Спасибо!")
            save_data_to_file(chat_id)
            bot.send_message(chat_id, "Все данные сохранены.")
            logger.info(f"Annotated image received and saved as {annotated_file_path} for user {chat_id}.")
            user_data[chat_id]["state"] = STATE_NONE
        else:
            bot.send_message(chat_id, "Произошла ошибка при сохранении аннотированного изображения.")
            logger.error(f"Failed to save annotated image for user {chat_id}.")
    except Exception as e:
        logger.error(f"Error handling annotated image for user {chat_id}: {e}")
        bot.send_message(chat_id, "Произошла ошибка при обработке аннотированного изображения.")

# Функция для сохранения изображения
def save_image(file_info, file_id):
    try:
        # Получаем текущее количество файлов в папке
        files = os.listdir(IMAGE_FOLDER)
        file_number = len(files) + 1
        file_path = os.path.join(IMAGE_FOLDER, f"{file_number}.jpg")

        # Скачиваем файл
        downloaded_file = bot.download_file(file_info.file_path)

        # Сохраняем файл
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        logger.info(f"Image saved at path: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return None

# Функция для сохранения аннотированного изображения
def save_annotated_image(file_info, original_image_path):
    try:
        # Изменяем имя файла, добавляя суффикс "_a" перед расширением
        base_name = os.path.basename(original_image_path)
        name, ext = os.path.splitext(base_name)
        annotated_file_path = os.path.join(ANNOTATED_IMAGE_FOLDER, f"{name}_a{ext}")

        # Скачиваем файл
        downloaded_file = bot.download_file(file_info.file_path)

        # Сохраняем файл
        with open(annotated_file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        logger.info(f"Annotated image saved at path: {annotated_file_path}")
        return annotated_file_path
    except Exception as e:
        logger.error(f"Error saving annotated image: {e}")
        return None

# Функция для сохранения данных в CSV файл
def save_data_to_file(chat_id):
    try:
        data = user_data[chat_id]
        file_path = data.get("image_path", "N/A")
        annotated_image_path = data.get("annotated_image_path", "N/A")
        welding_params = data.get("welding_params", {})

        file_exists = os.path.isfile(CSV_FILE_PATH)

        with open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'ФИО',
                'Должность',
                'Вид сварки',
                'Тип покрытия электрода',
                'Марка электрода',
                'Диаметр электрода',
                'Тип соединения',
                'Пространственное положение сварки',
                'Сила тока',
                'Ссылка на изображение',
                'Ссылка на аннотированное изображение'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()  # записываем заголовки, если файл не существует

            row = {
                'ФИО': data.get("fio", ""),
                'Должность': data.get("position", ""),
                'Вид сварки': welding_params.get("welding_type", ""),
                'Тип покрытия электрода': welding_params.get("coverage_type", ""),
                'Марка электрода': welding_params.get("electrode_brand", ""),
                'Диаметр электрода': welding_params.get("electrode_diameter", ""),
                'Тип соединения': welding_params.get("connection_type", ""),
                'Пространственное положение сварки': welding_params.get("welding_position", ""),
                'Сила тока': welding_params.get("current", ""),
                'Ссылка на изображение': file_path,
                'Ссылка на аннотированное изображение': annotated_image_path
            }
            writer.writerow(row)

        logger.info(f"Data for user {chat_id} saved to CSV.")
    except Exception as e:
        logger.error(f"Error saving data to file: {e}")

# Запуск бота с обработкой исключений
def run_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logger.error(f"Error: {e}")
            bot.stop_polling()
            time.sleep(15)  # Ждем 15 секунд перед перезапуском

if __name__ == "__main__":
    run_bot()
