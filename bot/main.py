import os
from collections import defaultdict
from telebot import TeleBot
from telebot.types import (
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
    CallbackQuery
)
from db.database import db
from db.models import Feedback, Students
from dotenv import load_dotenv
from abc import ABC, abstractmethod

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
            "1. Нажать на кнопку 'Обратная связь'\n"
            "2. Выбрать тип обратной связи\n"
            "3. Написать свое сообщение\n"
            "4. Отправить его\n"
            "<b>Кнопка 'Цифровые ресурсы' содержит полезные ссылки.</b>",
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
        👉 <a href="https://inpsy.hspu.org/">Сайт психологической службы</a>

        <b>🖼️ Виртуальный тур по Русскому музею</b>
        👉 <a href="https://virtual.rusmuseumvrm.ru">Посетить музей</a>

        <b>💪 Студенческий фитнес клуб "PROFIT"</b>
        👉 <a href="https://vk.com/studprofit">Записаться в клуб</a>

        <b>🎮 Герценовский игровой клуб</b>
        👉 <a href="https://vk.com/herzengame">Присоединиться</a>

        <b>🌍 Атлас студенческих объединений</b>
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


class BotGame(BotHandler):
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.selected_parts = defaultdict(lambda: defaultdict(int))  # Default value is 0 (int)
        if not os.path.exists("carts"):
            os.makedirs("carts")

    def handle(self, message: Message):
        self.send_image(message.chat.id, 1)

    def send_image(self, chat_id: int, image_number: int):
        try:
            with open(f"carts/{image_number}.png", "rb") as cart:
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("Часть 1", callback_data=f"part_{image_number}_1"),
                    InlineKeyboardButton("Часть 2", callback_data=f"part_{image_number}_2"),
                    InlineKeyboardButton("Часть 3", callback_data=f"part_{image_number}_3"),
                )
                self.bot.send_photo(chat_id, cart, reply_markup=keyboard)
        except FileNotFoundError:
            self.bot.send_message(chat_id, "Изображение временно недоступно")


class GameCallbackHandler(BotHandler):
    def __init__(self, bot: TeleBot, game_handler: BotGame):
        self.bot = bot
        self.game_handler = game_handler
        self.selected_parts = defaultdict(lambda: defaultdict(int))
        self.part_texts = {
            1: {1: "Текст для части 1 картинки 1", 2: "Текст для части 2 картинки 1", 3: "Текст для части 3 картинки 1"},
            2: {1: "Текст для части 1 картинки 2", 2: "Текст для части 2 картинки 2", 3: "Текст для части 3 картинки 2"},
            3: {1: "Текст для части 1 картинки 3", 2: "Текст для части 2 картинки 3", 3: "Текст для части 3 картинки 3"},
            4: {1: "Текст для части 1 картинки 4", 2: "Текст для части 2 картинки 4", 3: "Текст для части 3 картинки 4"},
            5: {1: "Текст для части 1 картинки 5", 2: "Текст для части 2 картинки 5", 3: "Текст для части 3 картинки 5"},
            6: {1: "Текст для части 1 картинки 6", 2: "Текст для части 2 картинки 6", 3: "Текст для части 3 картинки 6"},
            7: {1: "Текст для части 1 картинки 7", 2: "Текст для части 2 картинки 7", 3: "Текст для части 3 картинки 7"},
            8: {1: "Текст для части 1 картинки 8", 2: "Текст для части 2 картинки 8", 3: "Текст для части 3 картинки 8"},
            9: {1: "Текст для части 1 картинки 9", 2: "Текст для части 2 картинки 9", 3: "Текст для части 3 картинки 9"},
        }

        self.button_names = {
            1: ["Часть 1", "Часть 2", "Часть 3"],
            2: ["Часть 1", "Часть 2", "Часть 3"],
            3: ["Часть 1", "Часть 2", "Часть 3"],
            4: ["Часть 1", "Часть 2", "Часть 3"],
            5: ["Часть 1", "Часть 2", "Часть 3"],
            6: ["Часть 1", "Часть 2", "Часть 3"],
            7: ["Часть 1", "Часть 2", "Часть 3"],
            8: ["Часть 1", "Часть 2", "Часть 3"],
            9: ["Часть 1", "Часть 2", "Часть 3"],
        }

    def handle(self, call: CallbackQuery):
        data = call.data.split("_")
        action = data[0]
        chat_id = call.message.chat.id

        if action == "part":
            image_number = int(data[1])
            part_number = int(data[2])

            if self.selected_parts[chat_id][image_number] != 0:
                self.bot.answer_callback_query(call.id, "Вы уже выбрали часть этой картинки!")
                return

            self.selected_parts[chat_id][image_number] = part_number
            self.bot.send_message(chat_id, self.part_texts[image_number][part_number])
            self.send_next_button(chat_id, image_number)

        elif action == "next":
            image_number = int(data[1])

            if image_number < 9:
                self.game_handler.send_image(chat_id, image_number + 1)
            else:
                self.bot.send_message(chat_id, "🎉 Вы завершили игру!")
                self.selected_parts[chat_id].clear()
                self.bot.send_message(chat_id, "Возвращаемся в основное меню.", reply_markup=FeedbackBot.markup_main())

        self.bot.answer_callback_query(call.id)

    def send_next_button(self, chat_id: int, image_number: int):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Дальше →", callback_data=f"next_{image_number}"))
        self.bot.send_message(chat_id, "Выберите следующую часть:", reply_markup=keyboard)


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