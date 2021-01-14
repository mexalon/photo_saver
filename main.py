import requests
import time
import os
import json
from pprint import pprint


def get_token(file_name: str):
    """получить токен из файла"""
    with open(file_name, 'r', encoding='utf-8') as f:
        token = f.readline()
    return token


class YaUploader:
    def __init__(self):
        self.token = get_token('YaD_token.txt')
        self.endpoint = 'https://cloud-api.yandex.net/v1/disk/resources/'

    def upload(self, f, file_name: str, dir_name=None):
        """Метод загруджает файл на яндекс диск"""
        if dir_name is not None and isinstance(dir_name, str):
            target_path = f'{dir_name}/{file_name}'
        else:
            target_path = file_name

        response = requests.get(self.endpoint + 'upload',
                                headers={'Authorization': f'OAuth {self.token}'},
                                params={'path': target_path, 'overwrite': True})
        response.raise_for_status()
        time.sleep(0.5)  # чтобы не забанили, ждём пол секунды

        href = response.json()['href']
        response = requests.put(href, files={'file': f})
        response.raise_for_status()
        code = {response.reason: response.status_code}
        if response.reason == 'Created':
            print('Сохранено!')
        else:
            print(code)

        return code

    def mkdir(self, dir_name: str):
        """метод для создания папки"""
        response = requests.put(self.endpoint,
                                headers={'Authorization': f'OAuth {self.token}'},
                                params={'path': dir_name})
        time.sleep(0.5)
        # response.raise_for_status()
        code = {response.reason: response.status_code}
        return code


class VkUser:
    """На вход подаётся id или домен пользователя ВК"""

    def __init__(self, some_id):
        self.token = get_token('VK_token.txt')
        self.endpoint = 'https://api.vk.com/method/'
        self.vk_ver = '5.126'

        some_user = requests.get(self.endpoint + 'users.get', params={'access_token': self.token,
                                                                      'v': self.vk_ver,
                                                                      'user_ids': some_id,
                                                                      }).json()
        time.sleep(0.5)  # чтобы не забанили, ждём пол секунды
        new_id = None
        new_user = None
        if not self.chek_error(some_user):
            new_user = some_user
            new_id = some_user['response'][0]['id']

        self.user = new_user
        self.id = new_id

    def __str__(self):
        """Имя Фамилия: ссылка на профиль"""
        if self.user:
            output = f"{self.user['response'][0]['first_name']}" \
                     f" {self.user['response'][0]['last_name']}:" \
                     f" https://vk.com/id{self.id}"
        else:
            output = f'пользователь не определён'

        return output

    def chek_error(self, response_json):
        """Проверка на ошибки запроса"""
        error = True
        if 'error' in response_json.keys():
            print(response_json['error']['error_msg'])
            error = response_json['error']['error_code']
        else:
            if 'response' in response_json.keys():
                if response_json['response']:
                    error = False
                else:
                    print('Отчего то нулевой айди возвращает пустой ответ')

        return error

    def get_albums(self):
        """Список альбомов пользователя"""
        if self.id:
            albums = requests.get(self.endpoint + 'photos.getAlbums',
                                  params={
                                      'access_token': self.token,
                                      'v': self.vk_ver,
                                      'owner_id': self.id,
                                      'need_system': 1
                                  }).json()

            time.sleep(0.5)  # чтобы не забанили, ждём пол секунды
            if not self.chek_error(albums):
                if albums['response']:
                    albums_id_index = list()
                    print(f'{self}\nАльбомы:')
                    for num, item in enumerate(albums['response']['items']):
                        print(f'{num+1}. {item["title"]}')
                        albums_id_index.append(item['id'])

                    output = albums_id_index
            else:
                output = False
        else:
            output = False

        return output

    def get_photos(self, album_id, photo_ids=None):
        """Список фото в альбоме в нужном формате (с сылкой на скачивание и некоторыми параметрами)"""
        if self.id:
            photos = requests.get(self.endpoint + 'photos.get',
                                  params={
                                      'access_token': self.token,
                                      'v': self.vk_ver,
                                      'owner_id': self.id,
                                      'album_id': album_id,
                                      'photo_ids': photo_ids,
                                      'extended': 1
                                  }).json()

            time.sleep(0.5)  # чтобы не забанили, ждём пол секунды
            if not self.chek_error(photos):
                if photos['response']:
                    photos_index = list()
                    print(f'Фотографии в альбоме {album_id}:')
                    for num, item in enumerate(photos['response']['items']):
                        photo_stat = self.photo_json_processing(item, num)
                        photos_index.append(photo_stat)

                    output = sorted(photos_index, key=(lambda item: int(item['likes'])), reverse=True)
            else:
                output = False
        else:
            output = False

        return output

    def get_photo_by_id(self, u_id: str, p_id: str):
        """ссылка на скачивание определённой фотки без знания айди альбома"""
        if self.id:
            photos = requests.get(self.endpoint + 'photos.getById',
                                  params={
                                      'access_token': self.token,
                                      'v': self.vk_ver,
                                      'photos': f'{u_id}_{p_id}',
                                      'extended': 1
                                  }).json()

            time.sleep(0.5)  # чтобы не забанили, ждём пол секунды
            if not self.chek_error(photos):
                if photos['response']:
                    item = photos['response'][0]
                    photo_stat = self.photo_json_processing(item)
                    output = photo_stat
            else:
                output = False
        else:
            output = False

        return output

    def photo_json_processing(self, photo, num=0):
        """Конвертация json фотки в нужный формат"""
        top_size = self.best_size(photo["sizes"])
        print(
            f'{num + 1}. Фото id:{photo["id"]}; лучший размер: {top_size["type"]};'
            f' лайков: {photo["likes"]["count"]};'
            f' добавлена {photo["date"]}; >> {top_size["url"]}')
        photo_stat = {'id': photo["id"],
                      'size': top_size["type"],
                      'likes': photo["likes"]["count"],
                      'date': photo["date"],
                      'url': top_size["url"]}

        return photo_stat

    def best_size(self, sizes_list):
        """ВЫбор самой большой фотки по типу"""
        type_ = ['s', 'm', 'x', 'o', 'p', 'q', 'r', 'y', 'z', 'w']
        size_ = range(1, len(type_) + 1)
        sizes_rating = dict(zip(type_, size_))
        top_size = sorted(sizes_list, key=(lambda item: sizes_rating[item['type']]), reverse=True)[0]
        return top_size


def get_user_albums(url=None):
    """запрос альбомов пользователя по ссылке"""
    the_user = add_user(url)
    if the_user:
        albums = the_user.get_albums()
        if albums:
            go_albums(the_user, albums)


def go_albums(user, index):
    """Выбор альбома для скачивания из списка альбомов"""
    all_commands_ = {'q': quit_,
                     'n': pass_
                     }
    my_command = ''
    while my_command != 'n':
        print('Выберите номер альбома для скачивания;'
              '\n"n" для выбора другого пользователя:'
              '\n"q" для завершения работы')
        my_command = input().lower().strip()
        if my_command in all_commands_.keys():
            all_commands_[my_command]()
        elif my_command.isdigit():
            num = int(my_command)
            album_processing(user, index, num)
        else:
            print('не верно задан выбор')


def album_processing(user, index, num):
    """запускает варианты действия с альбомом фото"""
    if 1 <= num < len(index) + 1:
        all_photos = user.get_photos(index[num - 1])
        what_to_do_with_photos(all_photos)
    else:
        print('нет такого альбома')


def what_to_do_with_photos(all_photos):
    all_commands_ = {'q': quit_,
                     'l': photo_to_hd,
                     'y': photo_to_yandex,
                     'n': pass_
                     }
    my_command = ''
    while my_command != 'n':
        print('Выберите:\n"y" для сохранения на Яндекс Диск;'
              '\n"l" для сохранения на локальный диск;'
              '\n"n" для выбора другого альбома:'
              '\n"q" для завершения работы')

        my_command = input().lower().strip()
        if my_command in all_commands_.keys():
            all_commands_[my_command](all_photos)
        else:
            print('не верно задан выбор')


def is_there_some_photo(some_photo=None):
    """Если на входе нет ничего, предлагает поискать фотку по ссылке"""
    if some_photo is None:
        some_photo = input('введите ссылку на фото:\n')
        photo_stats = get_photo_from_url(some_photo)
    else:
        photo_stats = some_photo

    return photo_stats


def save_one_photo():
    """Скачать и сохранить в нужное место отдельное фото по ссылке"""
    photo_stats = is_there_some_photo()
    what_to_do_with_photos(photo_stats)


def photo_to_yandex(some_photo=None):
    """Сохранение на яндекс диск"""
    photo_stats = is_there_some_photo(some_photo)
    if photo_stats:
        yandex_saver = YaUploader()
        target_dir = input('Укажите имя дериктории:').lower().strip()
        if target_dir:
            yandex_saver.mkdir(target_dir)

        for entry in some_photo:
            photo_itself = requests.get(entry['url']).content
            photo_name = f"{entry['likes']}_likes_{entry['date']}_loaded.jpg"
            print(f"Сохраняю {photo_name}")
            yandex_saver.upload(photo_itself, photo_name, target_dir)

        print(f"Сохраняю статистику")
        name = f"loaded_{photo_stats[0]['date']}_to_{photo_stats[-1]['date']}stats.json"
        yandex_saver.upload(json.dumps(photo_stats), name, target_dir)
    else:
        print('Нет такого фото')


def photo_to_hd(some_photo=None, target_dir=None):
    """Сохранение на локальный диск"""
    photo_stats = is_there_some_photo(some_photo)
    if photo_stats:
        target_dir = input('Укажите имя дериктории:').lower().strip()
        if target_dir:
            if target_dir not in os.listdir():
                os.mkdir(target_dir)

        for entry in photo_stats:
            photo_itself = requests.get(entry['url'])
            photo_name = f"{entry['likes']}_likes_{entry['date']}_loaded.jpg"
            print(f"Сохраняю {photo_name}")
            with open(os.path.join(target_dir, photo_name), 'wb') as f:
                f.write(photo_itself.content)

        print(f"Сохраняю статистику")
        name = f"loaded_{photo_stats[0]['date']}_to_{photo_stats[-1]['date']}stats.json"
        with open(os.path.join(target_dir, name), 'w') as f:
            json.dump(photo_stats, f)

    else:
        print('Нет такого фото')


def get_photo_from_url(url):
    """Вытаскиевает ссыдку на скачивание фото из ссылки на фото"""
    if 'vk.com' in url:
        u_id_p_id = url.split('photo')[1].split('?')[0].split('%')[0]
        u_id = u_id_p_id.split('_')[0]
        p_id = u_id_p_id.split('_')[1]
        the_user = add_user(u_id)
        if the_user:
            the_photo = the_user.get_photo_by_id(u_id, p_id)
        else:
            the_photo = None

        return the_photo


def get_id_from_url(url: str):
    """Разбор ссылки профиля"""
    result = url.strip().split('/id')[-1].split('/')[-1]
    if result:
        output = result
    else:
        output = None  # будет ссылка на свой собственный аккаунт

    return output


def add_user(url=None):
    """Создание нового объекта"""
    if url is None:
        url = input('введите ссылку на пользователя:\n')
        temp_id = get_id_from_url(url)
    else:
        temp_id = get_id_from_url(url)

    new_user = VkUser(temp_id)  # пока только ВК
    if new_user.id:
        output = new_user
    else:
        output = False

    return output


def help_(*args):
    print('ставьте ID пользователя либо ссылку на его профиль и нажмите Enter.\n '
          'После этого Вам будет предложено выбрать альбом для загрузки из списка '
          'альбомов этого пользователя'
          )


def quit_(*args):
    print('Выход')
    raise SystemExit(0)


def pass_(*args):
    pass


def test_(*args):
    """функция для тестирования других функций"""
    pass


def go_go():
    print('Вставьте ссылку на пользователя.\n'
          'введите "q" для выхода,'
          'введите "o" для того, чтобы скачать одно фото по ссылке, '
          '"help" для справки')

    all_commands_ = {'q': quit_,
                     'help': help_,
                     'o': save_one_photo,
                     't': test_
                     }
    while True:
        my_command = input('Ссылка на профиль: ').lower().strip()
        if my_command in all_commands_.keys():
            all_commands_[my_command]()
        else:
            get_user_albums(my_command)


if __name__ == '__main__':
    go_go()
