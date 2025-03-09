import locale
import threading
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal

from django.conf import settings

from website.models import Game, Publisher, Developer, Concurrent, SteamGame
from .mappers import CategoryMapper, PublisherMapper, DeveloperMapper, GenreMapper, GameMapper, GameImageMapper, \
    ConcurrentPriceMapper

LOCALE_LOCK = threading.Lock()


@contextmanager
def setlocale():
    with LOCALE_LOCK:
        saved = locale.setlocale(locale.LC_TIME)
        try:
            yield locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        finally:
            locale.setlocale(locale.LC_TIME, saved)


def convert_steam_price_to_decimal(price):
    price = str(price)
    int_part = price[:-2]
    fract_part = price[-1:-3:-1]

    return Decimal(f"{int_part}.{fract_part}")


class SteamDetailsProcessing:

    @classmethod
    def process(cls, data):
        images, categories, publishers, developers, genres, steam_ids = cls._extract_foreign_fields(data)
        cls._upsert_foreign(categories, publishers, developers, genres)

        id_by_steam_id = SteamGame.get_id_by_steam_id_map(steam_ids)

        processed_data = cls._process_game_data(data, id_by_steam_id)
        GameMapper(processed_data).upsert()

        cls._update_images_fields(images, processed_data)
        GameImageMapper(images).upsert()

    @classmethod
    def _extract_foreign_fields(cls, data):
        images = []
        categories = []
        publishers = []
        developers = []
        genres = []
        steam_ids = []

        for game in data:
            steam_id, item = tuple(game.items())[0]
            steam_ids.append(steam_id)

            data_ = item['data']
            developers.extend(data_['developers'])
            publishers.extend(data_['publishers'])

            genres_ = cls._process_list_key(data_['genres'])
            genres.extend(genres_)

            categories_ = cls._process_list_key(data_['categories'])
            categories.extend(categories_)

            images.extend(
                cls._process_images(data_['header_image'], data_['screenshots'], int(steam_id))
            )

        genres = tuple({'id': i[0], 'description': i[1]} for i in set(genres))
        categories = tuple({'id': i[0], 'description': i[1]} for i in set(categories))
        developers = tuple({'name': i} for i in set(developers))
        publishers = tuple({'name': i} for i in set(publishers))

        return images, categories, publishers, developers, genres, steam_ids

    @classmethod
    def _process_list_key(cls, key_data):
        data = []
        for i in key_data:
            data.append((int(i['id']), i['description']))

        return data

    @classmethod
    def _process_images(cls, header_image, screenshots, steam_id):
        images_ = [{'url': i['path_full'], 'is_header': False, 'steam_id': steam_id} for i in screenshots]
        images_.append({'url': header_image, 'is_header': True, 'steam_id': steam_id})

        return images_

    @classmethod
    def _upsert_foreign(cls, categories, publishers, developers, genres):
        CategoryMapper(categories).upsert()
        PublisherMapper(publishers).upsert()
        DeveloperMapper(developers).upsert()
        GenreMapper(genres).upsert()

    @classmethod
    def _process_game_data(cls, data, id_by_steam_id):
        publishers = Publisher.get_name__id_map()
        developers = Developer.get_id_name_map()

        processed = []
        with setlocale():
            for game in data:
                steam_id, item = tuple(game.items())[0]
                steam_game_id = id_by_steam_id[int(steam_id)]

                data_ = item['data']
                release_date = datetime.strptime(data_['release_date']['date'], '%d %b. %Y г.')
                release_date = release_date.strftime('%Y-%m-%d')

                price = convert_steam_price_to_decimal(data_['price_overview']['initial'])

                req_min = data_['pc_requirements'].get('minimum', '')
                req_min = req_min.replace("<strong>Минимальные:</strong><br>", "")

                req_recom = data_['pc_requirements'].get('recommended', '')
                req_recom = req_recom.replace("<strong>Рекомендованные:</strong><br>", "")

                data_ = {
                    'name': data_['name'],
                    'steam_game_id': steam_game_id,
                    'description': data_['detailed_description'],
                    'requirements': f"{req_min}\n{req_recom}",
                    'release_date': release_date,
                    'price': price,
                    'categories': tuple(int(i['id']) for i in data_['categories']),
                    'genres': tuple(int(i['id']) for i in data_['genres']),
                    'publishers': tuple(publishers[name] for name in data_['publishers']),
                    'developers': tuple(developers[name] for name in data_['developers']),
                }

                processed.append(data_)

        return processed

    @classmethod
    def _update_images_fields(cls, images, processed_data):
        game_by_steam_id = Game.obj_by_steam_id(steamgame_ids=(i['steam_game_id'] for i in processed_data))
        for image in images:
            steam_id = image.pop('steam_id')
            image['game_id'] = game_by_steam_id[steam_id].id


class SteamDetailPriceProcessing:
    @classmethod
    def process(cls, data):
        game_by_steam_id = Game.obj_by_steam_id(steam_ids=data.keys())
        steam, _ = Concurrent.objects.get_or_create(name=settings.STEAM_CONCURRENT_NAME)

        updated_games = []
        concurrent_prices = []
        for steam_id, prices in data.items():
            game = game_by_steam_id[int(steam_id)]

            price = convert_steam_price_to_decimal(prices['initial'])

            if price != game.price:
                game.price = price
                updated_games.append(game)

            price = convert_steam_price_to_decimal(prices['final'])
            is_lower = cls.is_price_lower(game, price)

            concurrent_prices.append({
                'game_id': game.id,
                'concurrent_id': steam.id,
                'price': price,
                'is_lower_price': is_lower,
            })

        cls._update_models(updated_games, concurrent_prices)

    @staticmethod
    def is_price_lower(game, price):
        is_price_gt = game.discount_price is None and game.price > price
        is_discount_gt = game.discount_price is not None and game.discount_price > price
        if is_price_gt or is_discount_gt:
            return True
        return False

    @staticmethod
    def _update_models(games, prices_data):
        Game.objects.bulk_update(games, ['price'], batch_size=500)
        ConcurrentPriceMapper(prices_data).upsert()
