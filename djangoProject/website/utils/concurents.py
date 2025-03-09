from requests import get

from website.models import Game, Concurrent
from website.utils.mappers import ConcurrentPriceMapper


class Plati:
    _url = "https://plati.io/api/search.ashx"
    _description_keywords = ('ключ', 'steam gift', 'гифт', 'key')
    _rating_minimum = 100
    _name_template = "Plati.{seller_name}"

    def __init__(self, game_ids):
        self.params = {
            "query": "",
            "visibleOnly": "true",
            "response": "json",
        }

        self.games = Game.get_by_ids(game_ids).only('id', 'price', 'discount_price', 'name')
        self.concurs_name_to_id = Concurrent.map_name_to_id()

    def search_and_load(self):
        processed = []
        for game in self.games:
            self.params['query'] = game.name
            response = get(self._url, params=self.params)
            data = response.json()
            for seller_data in data['items']:
                processed_data = self._process_seller_data(seller_data)
                if processed_data:
                    self._update_game_info(processed_data, game)
                    processed.append(processed_data)

        ConcurrentPriceMapper(processed).upsert()
        return processed

    def _process_seller_data(self, data):
        descr = data['description'].lower()
        name = data['name'].lower()
        for key in self._description_keywords:
            if (key in descr or key in name) and data['seller_rating'] >= self._rating_minimum:
                processed_data = {}

                seller_name = data['seller_name']
                internal_name = self._name_template.format(seller_name=seller_name)

                id_ = self.concurs_name_to_id.get(internal_name)
                if not id_:
                    concur = Concurrent(name=internal_name)
                    concur.save()
                    id_ = concur.id
                    self.concurs_name_to_id[internal_name] = id_

                processed_data['concurrent_id'] = id_
                processed_data['price'] = data['price_rur']

                return processed_data

    def _update_game_info(self, data, game):
        data['game_id'] = game.id
        seller_price = data['price']
        data['is_lower_price'] = self._is_price_lower(game, seller_price)

    def _is_price_lower(self, game, seller_price):
        is_price_gt = game.discount_price is None and game.price > seller_price
        is_discount_gt = game.discount_price is not None and game.discount_price > seller_price
        if is_price_gt or is_discount_gt:
            return True
        return False
