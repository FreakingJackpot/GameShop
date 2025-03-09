from io import BytesIO

from pandas import read_excel
from pandas.core.interchange.dataframe_protocol import DataFrame

from website.models import SteamGame, Incoming, Distributor, Key


class IncomingsImporter:
    def __init__(self, file: BytesIO):
        self.data: DataFrame = read_excel(file, sheet_name=0)
        self._distr = self._get_distributor()

    def _get_distributor(self):
        distr_name = tuple(self.data['distributor'])[0]
        self.data = self.data.drop('distributor', axis=1)
        return Distributor.get_by_name(distr_name)

    def import_incoming(self):
        for game_name in self.data.columns:
            game_id = SteamGame.get_id_by_name(game_name)

            incoming = Incoming(game_id=game_id, count=len(self.data[game_name]), distributor=self._distr)
            incoming.save()
            keys = self.data[game_name]
            self._insert_keys(keys, incoming)

    def _insert_keys(self, keys, incoming):
        objs = []
        for i, key in keys.items():
            objs.append(Key(incoming=incoming, value=key))

        Key.objects.bulk_create(objs, batch_size=500)
