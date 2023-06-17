# импорты
import vk_api
from pprint import pprint
from config import acces_token
from datetime import datetime
from vk_api.exceptions import ApiError


# получение данных о пользователе

class VkHeart:
    def __init__(self, acces_token):
        self.api = vk_api.VkApi(token=acces_token)

    def bdate_age(self, bdate):
        if bdate is not None:
            user_year = bdate[5:]
            now = datetime.now().year
            return now - int(user_year)
        else:
            return

    def get_profile_info(self, user_id):
        try:
            info, = self.api.method('users.get',
                                    {'user_id': user_id,
                                     'fields': 'bdate,city,sex'
                                     }
                                    )
        except ApiError as e:
            info = {}
            print(f'error = {e}')

        '''фильтрует полученную информацию'''

        filter_info = {'name': (info['first_name'] + ' ' + info['last_name']) if
                       'first_name' in info and 'last_name' in info else None,
                       'age': self.bdate_age(info.get('bdate')),
                       'city': info.get('city')['title'] if info.get('city') is not None else None,
                       'sex': info.get('sex'),
                       'id': user_id
                       }

        return filter_info

# поиск пользователей

    def get_profile_search(self, params, offset):
        try:
            users = self.api.method('users.search',
                                    {'count': 50,
                                     'offset': offset,
                                     'hometown': params.get('city'),
                                     'sex': 1
                                        if params.get('sex') == 2 else 2,
                                     'has_photo': True,
                                     'age_from': params.get('year') - 2
                                        if params.get('year') is True else None,
                                     'age_to': params.get('year') + 2
                                        if params.get('year') is True else None,
                                     }
                                    )

        except ApiError as e:
            users = []
            print(f'error = {e}')

        filter_info = []
        for item in users['items']:
            if item['is_closed'] is False:
                filter_info.append({
                    'name': item['first_name'] + ' ' + item['last_name'],
                    'id': item['id']})

        return filter_info

# поиск фотографий

    def get_photos_search(self, id):
        try:
            photo = self.api.method('photos.get',
                                    {'owner_id': id,
                                     'album_id': 'profile',
                                     'extended': 1
                                     }
                                    )
        except ApiError as e:
            photo = {}
            print(f'error = {e}')

# фильтрует фото по количеству лайков и комментариев
        filter_photo = [
                    {'owner_id': item['owner_id'],
                     'id': item['id'],
                     'likes': item['likes']['count'] + item['comments']['count']
                     } for item in photo['items']
                    ]

        ''' сортировка фото по максимальному значению атрибута likes'''
        sort_photo = sorted(filter_photo, key=lambda x: x.get('likes'), reverse=True)

        return sort_photo[:3]


if __name__ == '__main__':
    user_id = 736941648
    heart = VkHeart(acces_token)
    params = heart.get_profile_info(user_id)
    form_users = heart.get_profile_search(params, 0)
    form_user = form_users.pop()
    photos = heart.get_photos_search(form_user['id'])

