from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
from config import TOKEN, MAX_TOKENS

bot = TeleBot('TOKEN')
MAX_LETTERS = MAX_TOKENS

def count_tokens(text):
    tokenizer = AutoTokenizer.from_pretrained("TheBloke/Mistral-7B-Instruct-v0.1-GGUF")  # название модели
    return len(tokenizer.encode(text))


users_history = {}



def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id,
                     text=f"Привет, {user_name}! Я бот-помощник для решения разных задач!\n"
                          f"Ты можешь прислать условие задачи, а я постараюсь её решить.\n"
                          "Иногда ответы получаются слишком длинными - в этом случае ты можешь попросить продолжить.",
                     reply_markup=create_keyboard(["/solve_task", '/help']))


# Команда /help
@bot.message_handler(commands=['help'])
def support(message):
    bot.send_message(message.from_user.id,
                     text="Чтобы приступить к решению задачи: нажми /solve_task, а затем напиши условие задачи",
                     reply_markup=create_keyboard(["/solve_task"]))

@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    bot.send_message(message.chat.id, "Напиши условие новой задачи:")
    bot.register_next_step_handler(message, get_prompt)

def continue_filter(message):
    button_text = 'Продолжить решение'
    return message.text == button_text

@bot.message_handler(func=continue_filter)
def get_promt(message):
    user_id = message.from_user.id

    if message.content_type != 'text':
        bot.send_message(user_id, "Необходимо отправить именно текстовое сообщение")
        bot.register_next_step_handler(message, get_prompt)
        return

    user_request = message.text

    if MAX_LETTERS > 150:
        bot.send_message(user_id, "Запрос превышает количество символов\nИсправь запрос")
        bot.register_next_step_handler(message, get_prompt)
        return

    if user_id not in users_history:
        users_history[user_id] = {
            'system_content': "Ты - дружелюбный помощник для решения задач по математике. Давай подробный ответ с решением на русском языке",
            'user_content': user_request,
            'assistant_content': "Решим задачу по шагам: "
        }

    elif users_history[user_id]['user_content'] == "":
        bot.send_message(user_id, "диалог не начат. пожалуйста, начни задачу сначала")
        return

def add_response(prev_response, gpt_response):

    response = prev_response + "\n\n" + gpt_response
    return response


def send_full_response(user_response):
    buttons = ["Продолжить решение", "Завершить решение"]
    bot.send_message(user_response + "\n\n" + "Какое решение вы хотите выбрать?", buttons)

def end_filter(message):
    if "завершить" in message:
        return True
    else:
        return False


@bot.message_handler(content_types=['text'], func=end_filter)
def end_task(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Текущее решение завершено.")
    users_history[user_id] = {}
    solve_task(message)

    if users_history[user_id]['user_content'] == "":
        bot.send_message(user_id, "Диалог не начат. Пожалуйста, начни задачу сначала.")
        return

logging.basicConfig(filename='error.log', level=logging.ERROR)
bot.polling()
