import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from config import comunity_token, acces_token
from heart import VkHeart
from data_store import add_profiles, check_profiles
from sqlalchemy import create_engine
from config import db_url

user_date_names = {
    "city": "город",
    "sex": "пол",
    "age": "возраст"
    }


# отправка сообщений
class Bot:
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_heart = VkHeart(acces_token)
        self.offset = 0
        self.form_users = []
        self.params = {}
        self.engine = create_engine(db_url)

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()
                        }
                       )

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                user_id = event.user_id
                text = event.text.lower()
                if text == 'привет':
                    if not self.params or self.params["id"] != user_id:
                        self.params = self.vk_heart.get_profile_info(user_id)
                    print(self.params)
                    self.message_send(user_id, f'Привет &#128075; {self.params["name"]}')
                elif text == 'поиск':
                    while None in self.params.values():
                        self.missing_data(user_id)
                    else:
                        self.search_profiles(user_id)
                elif text == 'пока':
                    self.message_send(user_id, f'До скорых встреч\n{self.params["name"]}')
                else:
                    self.message_send(
                        user_id, 'Не понимаю вашу команду. Но... могу познакомить, нужно написать "Поиск" ')

# Функция для заполнения параметров для поиска.
    def missing_data(self, user_id):
        missing_key = next((key for key, value in self.params.items() if value is None), None)
        self.message_send(user_id, f'Не хватает данных для поиска. Напишите Ваш {user_date_names[missing_key]}:')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.user_id == user_id:
                text = event.text
                if text:
                    if missing_key in self.params.keys():
                        self.params[missing_key] = text
                        self.message_send(user_id, f'Спасибо, Ваш {user_date_names[missing_key]} добавлен.')
                        break

    def search_profiles(self, user_id):
        self.message_send(user_id, 'Начинаю искать &#128269;')
        found = False
        while not found:
            while not self.form_users:
                self.form_users = self.vk_heart.get_profile_search(self.params, self.offset)
                self.offset += 50

            form_user = self.form_users.pop()
            while check_profiles(self.engine, user_id, form_user["id"]):
                'Проверка анкет в БД'
                if not self.form_users:
                    break
                form_user = self.form_users.pop()
            else:
                'Добавление анкеты в БД'
                add_profiles(self.engine, user_id, form_user["id"])

                photos = self.vk_heart.get_photos_search(form_user['id'])
                photo_range = ','.join(f' photo{photo["owner_id"]}_{photo["id"]}' for photo in photos)
                self.message_send(user_id, f'Имя: {form_user["name"]}\nссылка: vk.com/id{form_user["id"]}',
                    attachment=photo_range)
                found = True


if __name__ == '__main__':
    bot = Bot(comunity_token, acces_token)
    bot.event_handler()