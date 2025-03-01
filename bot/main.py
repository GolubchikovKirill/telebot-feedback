import os
from abc import ABC, abstractmethod
from collections import defaultdict
from telebot import TeleBot
from dotenv import load_dotenv
from telebot.types import (
    ReplyKeyboardMarkup,
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from db.database import db
from db.models import Feedback, Students

load_dotenv()
TOKEN = os.getenv("TOKEN")


class BotHandler(ABC):
    @abstractmethod
    def handle(self, message: Message | CallbackQuery):
        pass


class StartHandler(BotHandler):
    def __init__(self, bot: TeleBot):
        self.bot = bot

    def handle(self, message: Message):
        image_url = "https://disk.yandex.ru/i/7MNk0dTd9YzMUQ"
        self.bot.send_photo(
            message.chat.id,
            image_url,
            caption="<b>Уважаемый студент! Я <s>бот</s> кот для сбора обратной связи.</b>\n"
                    "<b>Для того, чтобы поделиться тем, что тебе понравилось и/или ты хотел бы добавить, "
                    "нажми кнопку ниже.</b>",
            parse_mode="HTML",
            reply_markup=FeedbackBot.markup_main()
        )


class FeedbackHandler(BotHandler):
    def __init__(self, bot: TeleBot):
        self.bot = bot

    def handle(self, message: Message):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Что понравилось", callback_data="liked"))
        keyboard.add(InlineKeyboardButton("Что можно добавить", callback_data="add"))
        self.bot.send_message(message.chat.id, "Выберите тип обратной связи:", reply_markup=keyboard)


class HelpHandler(BotHandler):
    def __init__(self, bot: TeleBot):
        self.bot = bot

    def handle(self, message: Message):
        self.bot.send_message(
            message.chat.id,
            "<b>Для того, чтобы оставить обратную связь, нужно:</b>\n"
            "1. Нажать на кнопку 'Обратная связь'.\n"
            "2. Выбрать тип обратной связи.\n"
            "3. Написать свое сообщение.\n"
            "4. Отправить его.\n"
            "\n"
            "<b>Кнопка 'Цифровые ресурсы' содержит полезные ссылки.</b>\n"
            "\n"
            "<b>Чтобы приступить к интерактиву - нажмите кнопку 'Играть'.</b>\n"
            "Выберите одну из предложенных карточек, затем выполните задание, либо ответьте на вопрос\n"
            "Кнопка 'Далее', чтобы продолжить, пока не дойдете до конца.",
            parse_mode="HTML"
        )


class ResourcesHandler(BotHandler):
    def __init__(self, bot: TeleBot):
        self.bot = bot

    def handle(self, message: Message):
        image_url = "https://disk.yandex.ru/i/gqOpER4MIq1pwA"
        caption = """
        <b>📚 Психологическая служба РГПУ им. А. И. Герцена</b>
Помощь и поддержка студентов.
        👉 <a href="https://inpsy.hspu.org/">Сайт психологической 
            службы</a>

<b>🖼️ Виртуальный тур по 
        Русскому музею</b>
        👉 <a href="https://virtual.rusmuseumvrm.ru">Посетить музей</a>

<b>💪 Студенческий фитнес 
        клуб "PROFIT"</b>
        👉 <a href="https://vk.com/studprofit">Записаться в клуб</a>

<b>🎮 Герценовский игровой 
        клуб</b>
        👉 <a href="https://vk.com/herzengame">Присоединиться</a>

<b>🌍 Атлас студенческих 
        объединений</b>
        👉 <a href="https://www.herzen.spb.ru/about/struct-uni/contr/dep-edu-pract-youth-projects/atlas-studencheskikh-obedineniy/">Смотреть атлас</a>
        """
        self.bot.send_photo(message.chat.id, image_url, caption=caption, parse_mode="HTML")


class FeedbackCallbackHandler(BotHandler):
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.states = defaultdict(dict)

    def handle(self, call: CallbackQuery):
        if call.data in ("liked", "add"):
            self.bot.answer_callback_query(call.id)
            self.states[call.message.chat.id] = {"state": "waiting_feedback", "type": call.data}
            self.bot.send_message(
                call.message.chat.id,
                "Напишите вашу обратную связь:",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("Отмена", callback_data="cancel_feedback")
                )
            )

        elif call.data == "cancel_feedback":
            self.bot.answer_callback_query(call.id)
            if call.message.chat.id in self.states:
                del self.states[call.message.chat.id]
            self.bot.send_message(
                call.message.chat.id,
                "Отмена отправки сообщения",
                reply_markup=FeedbackBot.markup_main()
            )


class BotGame:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.selected_parts = defaultdict(lambda: defaultdict(int))
        self.button_names = {
            1: ["1.1 Преодолевая преграды", "1.2 Действие — мой инструмент", "1.3 Сила маленьких шагов"],
            2: ["2.1 Ресурсы внутри меня", "2.2 Используя каждый момент", "2.3 Возможности общения"],
            3: ["3.1 Социальное восприятие", "3.2 Принятие в группе", "3.3 Значимые отношения"],
            4: ["4.1 Общение с группой", "4.2 Социальная батарейка", "4.3 Тёплый круг общения"],
            5: ["5.1 Личные границы", "5.2 Как сказать НЕТ", "5.3 Чужие ожидания"],
            6: ["6.1 Новый город - новые возможности", "6.2 Вопросы быта", "6.3 Зов родного края"],
            7: ["7.1 Культурный шок", "7.2 В поиске новых друзей", "7.3 Связь с культурой"],
            8: ["8.1 Экзаменационный стресс", "8.2 Новые вызовы учёбы", "8.3 Слишком много информации"],
            9: ["9.1 Новые смыслы", "9.2 В поисках баланса", "9.3 Принятие"],
        }

        if not os.path.exists("carts"):
            os.makedirs("carts")

    def handle(self, message: Message):
        self.send_image(message.chat.id, 1)

    def send_image(self, chat_id: int, image_number: int):
        try:
            with open(f"carts/{image_number}.png", "rb") as cart:
                keyboard = InlineKeyboardMarkup()
                buttons = [
                    InlineKeyboardButton(
                        text=self.button_names[image_number][i],
                        callback_data=f"part_{image_number}_{i + 1}"
                    ) for i in range(3)
                ]
                # Добавляем кнопки ПО ОДНОЙ, чтобы они шли в столбец
                for button in buttons:
                    keyboard.add(button)

                self.bot.send_photo(chat_id, cart, reply_markup=keyboard)
        except FileNotFoundError:
            self.bot.send_message(chat_id, "Изображение временно недоступно")


class GameCallbackHandler:
    def __init__(self, bot: TeleBot, game_handler: BotGame):
        self.bot = bot
        self.game_handler = game_handler
        self.selected_parts = defaultdict(lambda: defaultdict(int))

        self.part_texts = {
            1: {
                1: """<b>Вопросы:</b>
• Что самое сложное вы преодолели за последний год?
• Какие уроки вы извлекли из этого опыта?

<b>Задание:</b> Нарисуйте или напишите, как вы видите свой путь к цели, несмотря на преграды.""",
                2: """<b>Упражнение:</b> Выберите одну задачу, которая вызывает у вас сомнения. 
Сформулируйте её в виде первого конкретного шага и выполните его.

<b>Совет:</b> Начните с малого, но начинайте. Это откроет дорогу большим успехам.""",
                3: """<b>Упражнение:</b> Разделите сложную задачу на три небольших шага и выполните их поэтапно.

<b>Совет:</b> Не перегружайте себя сразу. Делайте маленькие, но уверенные шаги."""
            },
            2: {
                1: """<b>Упражнение:</b> Составьте список из 5 своих качеств, которые помогают вам справляться с трудностями.

<b>Совет:</b> Напоминайте себе о своих сильных сторонах каждый раз, когда сталкиваетесь с вызовом.""",
                2: """<b>Упражнение:</b> Напишите три возможности, которые у вас есть прямо сейчас. 
Какие шаги вы можете предпринять, чтобы их реализовать?

<b>Совет:</b> Искать возможности полезно даже в простых повседневных делах.""",
                3: """<b>Упражнение:</b> Позвоните или напишите человеку, который может поддержать вас или дать совет. 
Что нового вы можете узнать от него?

<b>Совет:</b> Общение открывает неожиданные перспективы."""
            },
            3: {
                1: """<b>Задание:</b> Напишите, как вы воспринимаете чужое мнение о себе. 
• Что помогает вам оставаться уверенным в себе, несмотря на внешние воздействия?""",
                2: """<b>Задание:</b> Вспомните, когда вы почувствовали поддержку и принятие 
со стороны одногруппников или преподавателей. 
Как это повлияло на вашу уверенность в своих силах? 
Как вы можете создать атмосферу принятия для других людей в группе?""",
                3: """<b>Вопрос:</b> Кто в вашей жизни влияет на ваши решения?
<b>Задание:</b> Напишите о трех людях, чье мнение для вас наиболее значимо. 
Что именно в их словах или действиях помогает вам чувствовать себя уверенно?"""
            },
            4: {
                1: """<b>Задание:</b> Подумайте о своем последнем взаимодействии с кем-то из группы. 
Были ли вы довольны общением? 
Что можно улучшить в вашем взаимодействии, чтобы почувствовать большую удовлетворенность?""",
                2: """<b>Задание:</b> Оцените свою «социальную батарейку» от 0 до 10.
После каждой ситуации взаимодействия подумайте, заряжает она вас или разряжает.
Какие взаимодействия помогают вам «зарядиться»?""",
                3: """<b>Задание:</b> Напишите анонимно комплименты или добрые слова для трех человек из группы. 
Передайте их, и обсудите, как такие жесты влияют на атмосферу.

<b>Вопросы:</b> Когда вы в последний раз слышали искреннюю похвалу в свой адрес? 
Как это на вас повлияло?"""
            },
            5: {
                1: """<b>Задание:</b> Напишите, как вы определяете свои личные границы в отношениях с другими людьми. 
Какие фразы или действия помогают вам устанавливать эти границы и защищаться от манипуляций?""",
                2: """<b>Задание:</b> Представьте ситуацию, когда одногруппник или друг просит вас сделать что-то, 
что вам неудобно. Сыграйте диалог, где вы вежливо, но твердо отказываете.

<b>Вопрос:</b> Что для вас сложнее: говорить “нет” близким людям или одногруппникам? Почему?""",
                3: """<b>Задание:</b> Напишите три ожидания, которые вы чувствуете от окружающих. 
Решите, какие из них соответствуют вашим ценностям, а какие — нет.

<b>Вопрос:</b> Как вы справляетесь с ситуациями, когда ожидания окружающих не совпадают 
с вашими желаниями?"""
            },
            6: {
                1: """<b>Задание:</b> Поделитесь, какие трудности могут возникнуть при переезде для учёбы. 
Обсудите, как можно быстрее освоиться в новом месте.

<b>Вопрос:</b> Какие шаги помогут вам адаптироваться к жизни в незнакомом городе?""",
                2: """<b>Задание:</b> Подумайте, что сложнее всего в самостоятельной жизни. 
Какие лайфхаки помогают вам быстрее обустроиться в новом месте?""",
                3: """<b>Задание:</b> Поделитесь способами, которые помогают вам справляться с ностальгией.

<b>Вопрос:</b> Какие новые привычки могут помочь быстрее адаптироваться в новом месте?"""
            },
            7: {
                1: """<b>Задание:</b> Вспомните случай, когда вы столкнулись с культурными различиями. 
Как вы справились с этой ситуацией?

<b>Вопрос:</b> Как можно наладить общение с представителями других культур?""",
                2: """<b>Задание:</b> Поделитесь своими способами заведения знакомств в новой среде. 
Какие темы лучше не поднимать в начале общения?

<b>Вопрос:</b> Как легко и естественно влиться в новую компанию?""",
                3: """<b>Задание:</b> Напишите, какие способы помогают сохранять связь со своими традициями
и родным языком в новой среде.

<b>Вопрос:</b> Как можно интегрироваться в новую культуру, не теряя связи с родной?"""
            },
            8: {
                1: """<b>Задание:</b> Поделитесь своими методами борьбы с тревогой перед экзаменами. 
Что помогает вам сохранять спокойствие?""",
                2: """<b>Задание:</b> Вспомните ситуацию, когда вы не понимали задание или требования. Как вы нашли выход?

<b>Вопрос:</b> Что делать, если задание кажется непонятным или слишком сложным?""",
                3: """<b>Задание:</b> Обсудите, как можно быстрее разбираться в больших объёмах информации.

<b>Вопрос:</b> Что помогает вам справляться с информационной перегрузкой?"""
            },
            9: {
                1: """<b>Задание:</b> Вспомните моменты, когда вы теряли мотивацию. Как вы справлялись с этим?

<b>Вопрос:</b> Что делать, если пропало желание учиться?""",
                2: """<b>Задание:</b> Поделитесь своими методами организации времени. Какие привычки помогают вам всё успевать?

<b>Вопрос:</b> Как правильно расставлять приоритеты и не перегружать себя?""",
                3: """<b>Задание:</b> Вспомните случаи, когда вам было сложно объяснить родителям свою точку зрения. 
Как вы с этим справились?

<b>Вопрос:</b> Как построить конструктивный диалог с родителями?"""
            }
        }

    def handle(self, call: CallbackQuery):
        data = call.data.split("_")
        action = data[0]
        chat_id = call.message.chat.id

        if action == "part":
            image_number = int(data[1])
            part_number = int(data[2])

            if self.selected_parts[chat_id][image_number] != 0:
                self.bot.answer_callback_query(call.id, "Вы уже выбрали картинку!")
                return

            self.selected_parts[chat_id][image_number] = part_number
            self.bot.send_message(
                chat_id,
                self.part_texts[image_number][part_number],
                parse_mode='HTML'
            )
            self.send_next_button(chat_id, image_number)

        elif action == "next":
            image_number = int(data[1])

            if image_number < 9:
                self.game_handler.send_image(chat_id, image_number + 1)
            else:
                self.bot.send_message(chat_id, "🎉 Вы завершили игру! Нажми на 'Обратную связь' и поделись ею.")
                self.selected_parts[chat_id].clear()
                # self.bot.send_message(chat_id, "Возвращаемся в основное меню.")

        self.bot.answer_callback_query(call.id)

    def send_next_button(self, chat_id: int, image_number: int):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Дальше →", callback_data=f"next_{image_number}"))
        self.bot.send_message(chat_id, "Продолжить игру!", reply_markup=keyboard)


class FeedbackBot:
    def __init__(self, token: str):
        self.bot = TeleBot(token)
        self.game_handler = BotGame(self.bot)
        self.handlers = {
            "start": StartHandler(self.bot),
            "feedback": FeedbackHandler(self.bot),
            "help": HelpHandler(self.bot),
            "resources": ResourcesHandler(self.bot),
            "feedback_callback": FeedbackCallbackHandler(self.bot),
            "game": self.game_handler,
            "game_callback": GameCallbackHandler(self.bot, self.game_handler),
        }
        self.register_handlers()

    def register_handlers(self):
        # Командные обработчики
        self.bot.message_handler(commands=['start'])(lambda msg: self.handlers["start"].handle(msg))

        # Обработчики текстовых сообщений
        self.bot.message_handler(func=lambda m: m.text == "Обратная связь")(
            lambda msg: self.handlers["feedback"].handle(msg))
        self.bot.message_handler(func=lambda m: m.text == "Помощь")(
            lambda msg: self.handlers["help"].handle(msg))
        self.bot.message_handler(func=lambda m: m.text == "Цифровые ресурсы")(
            lambda msg: self.handlers["resources"].handle(msg))
        self.bot.message_handler(func=lambda m: m.text == "Игра")(
            lambda msg: self.handlers["game"].handle(msg))

        # Callback обработчики
        self.bot.callback_query_handler(func=lambda c: c.data in ("liked", "add", "cancel_feedback"))(
            lambda call: self.handlers["feedback_callback"].handle(call))

        self.bot.callback_query_handler(func=lambda c: c.data.startswith(("part", "next")))(
            lambda call: self.handlers["game_callback"].handle(call))

        # Обработчик текста для обратной связи
        self.bot.message_handler(func=lambda m: self.handlers["feedback_callback"].states.get(m.chat.id, {}).get(
            "state") == "waiting_feedback")(
            self.handle_feedback_text)

    def handle_feedback_text(self, message: Message):
        state = self.handlers["feedback_callback"].states.get(message.chat.id)
        if not state:
            return

        feedback_type = state["type"]
        self.save_feedback(message, feedback_type)
        del self.handlers["feedback_callback"].states[message.chat.id]
        self.bot.send_message(
            message.chat.id,
            "✅ Спасибо за вашу обратную связь!",
            reply_markup=self.markup_main()
        )

    @staticmethod
    def save_feedback(message: Message, category: str):
        with db.create_session() as session:  # Используем контекстный менеджер
            try:
                student = session.get(Students, message.from_user.id)  # Используем session.get()
                if not student:
                    student = Students(
                        id=message.from_user.id,
                        name=message.from_user.full_name
                    )
                    session.add(student)

                feedback = Feedback(
                    message=message.text,
                    category=category
                )
                session.add(feedback)
                session.commit()
            except Exception as e:
                print(f"Ошибка сохранения сообщения: {e}")
                session.rollback()

    @staticmethod
    def markup_main() -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            "Обратная связь",
            "Игра",
            "Цифровые ресурсы",
            "Помощь"
        )
        return markup

    def run(self):
        print("Бот запущен!")
        self.bot.infinity_polling()


if __name__ == "__main__":
    bot = FeedbackBot(TOKEN)
    bot.run()
