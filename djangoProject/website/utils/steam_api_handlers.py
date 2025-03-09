from time import sleep

from requests import get


class SteamGamesListEndpoint:
    _url = 'http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=json'

    def get_all_data(self):
        return self.get_data()

    def get_data(self):
        response = self.request()
        return response['applist']['apps']

    def request(self):
        response = get(self._url)
        json_response = response.json()
        return json_response


class SteamGameDetailsEndpoint:
    _url = 'https://store.steampowered.com/api/appdetails'
    _rate_limit = 5 * 62

    _price_filter = 'price_overview'

    def __init__(self):
        self._params = {
            'appids': '',
            'cc': 'RU',
            'l': 'russian',
        }

    def get_details_by_ids(self, ids):
        details = []
        self._params.pop('filters', None)
        for id_ in ids:
            self._params['appids'] = id_
            response = get(self._url, params=self._params)

            if response.status_code == 429:
                sleep(self._rate_limit)
                response = get(self._url, params=self._params)

            details.append(response.json())
        return details

    def get_prices_by_ids(self, ids):
        prices = {}
        self._params['appids'] = ','.join(map(str,ids))
        self._params['filters'] = self._price_filter
        response = get(self._url, params=self._params)

        if response.status_code == 429:
            sleep(self._rate_limit)
            response = get(self._url, params=self._params)

        data = response.json()
        for steam_id, data_ in data.items():
            prices[steam_id] = {'initial': data_['data']['price_overview']['initial'],
                                'final': data_['data']['price_overview']['final'], }

        return prices
