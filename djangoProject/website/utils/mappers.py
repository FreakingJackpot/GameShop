from website.models import SteamGame, MapperMixin, Game, GameImage, Genre, Category, Publisher, Developer, \
    ConcurrentPrice


class BaseMapper:
    _model: MapperMixin

    _mappings_fields: tuple  # like (('key1','key2'))
    _update_fields: set

    def __init__(self, data):
        self.all_keys = set(self._model.get_all_keys())
        reverse_map = {j: i for i, j in self._mappings_fields}
        self.data_mapping = {tuple(i[reverse_map[field]] for field in self._model.key_fields): i for i in data}


    def upsert(self):
        keys_to_insert, objs_to_update = self.split()
        self.insert(keys_to_insert)
        self.update(objs_to_update)

    def _split(self):
        keys = set(self.data_mapping.keys())
        to_insert = tuple(keys - self.all_keys)
        to_update = tuple(keys & self.all_keys)

        return to_insert, to_update

    def split(self):
        to_insert, to_update = self._split()
        return to_insert, self._model.get_by_keys(to_update)

    def insert(self, keys):
        objs = []
        for key in keys:
            data = self.data_mapping[key]
            params = {}
            for key_1, key_2 in self._mappings_fields:
                params[key_2] = data.get(key_1)

            objs.append(self._model(**params))

        self._model.objects.bulk_create(objs, batch_size=500)

    def update(self, objs):
        if self._update_fields:
            updated_objs = []
            for obj in objs:
                key = tuple(getattr(obj, key_name) for key_name in self._model.key_fields)

                data = self.data_mapping.get(key)
                if data:
                    updated = False
                    for key_1, key_2 in self._mappings_fields:
                        attr_val = data.get(key_1)

                        if key_2 in self._update_fields and getattr(obj, key_2) != attr_val:
                            setattr(obj, key_2, attr_val)

                            if not updated:
                                updated_objs.append(obj)

            update_fields = tuple(self._update_fields)
            self._model.objects.bulk_update(updated_objs, fields=update_fields, batch_size=500)


class SteamGameMapper(BaseMapper):
    _model = SteamGame

    _mappings_fields = (('appid', 'steam_id'), ('name', 'name'))
    _update_fields = {'name'}


class GameMapper(BaseMapper):
    _model = Game

    _mappings_fields = (
        ('steam_game_id', 'steam_game_id'), ('name', 'name'), ('description', 'description'),
        ('release_date', 'release_date'), ('requirements', 'requirements'), ('price', 'price'),
        ('discount_price', 'discount_price'),)
    _update_fields = {'name', 'description', 'release_date', 'requirements', 'price'}

    _mtm_fields = ('categories', 'genres', 'publishers', 'developers')


    def upsert(self):
        keys_to_insert, objs_to_update = self.split()

        self.insert(keys_to_insert)
        self.insert_mtm(keys_to_insert)

        self.update(objs_to_update)
        self.update_mtm(objs_to_update)

    def insert_mtm(self, keys):
        steam_game_ids = (i[0] for i in self.data_mapping.keys())
        id_by_steam_game_id_map = self._model.id_by_steam_game_id_map(steam_game_ids=steam_game_ids)

        categories = []
        genres = []
        publishers = []
        developers = []

        for key in keys:
            data = self.data_mapping[key]
            id_ = id_by_steam_game_id_map[data['steam_game_id']]

            categories_ = [self._model.categories.through(game_id=id_, category_id=i) for i in data['categories']]
            categories.extend(categories_)

            genres_ = [self._model.genres.through(game_id=id_, genre_id=i) for i in data['genres']]
            genres.extend(genres_)

            publishers_ = [self._model.publishers.through(game_id=id_, publisher_id=i) for i in data['publishers']]
            publishers.extend(publishers_)

            developers_ = [self._model.developers.through(game_id=id_, developer_id=i) for i in data['developers']]
            developers.extend(developers_)

        for field, objs in zip(self._mtm_fields, (categories, genres, publishers, developers)):
            ThroughtModel = getattr(self._model, field).through
            ThroughtModel.objects.bulk_create(objs, batch_size=500)

    def update_mtm(self, objs):

        categories = []
        genres = []
        publishers = []
        developers = []

        for obj in objs:
            data = self.data_mapping[obj.get_key()]

            categories_ = [self._model.categories.through(game_id=obj.id, category_id=i) for i in data['categories']]
            categories.extend(categories_)

            genres_ = [self._model.genres.through(game_id=obj.id, genre_id=i) for i in data['genres']]
            genres.extend(genres_)

            publishers_ = [self._model.publishers.through(game_id=obj.id, publisher_id=i) for i in data['publishers']]
            publishers.extend(publishers_)

            developers_ = [self._model.developers.through(game_id=obj.id, developer_id=i) for i in data['developers']]
            developers.extend(developers_)

        for field, objs_ in zip(self._mtm_fields, (categories, genres, publishers, developers)):
            ThroughtModel = getattr(self._model, field).through
            ThroughtModel.objects.filter(game__in=objs).delete()
            ThroughtModel.objects.bulk_create(objs_, batch_size=500)


class GameImageMapper(BaseMapper):
    _model = GameImage

    _mappings_fields = (('url', 'url'), ('game_id', 'game_id'), ('is_header', 'is_header'))
    _update_fields = {}


class CategoryMapper(BaseMapper):
    _model = Category

    _mappings_fields = (('id', 'id'), ('description', 'name'))
    _update_fields = {'name'}


class GenreMapper(BaseMapper):
    _model = Genre

    _mappings_fields = (('id', 'id'), ('description', 'name'))
    _update_fields = {'name'}


class PublisherMapper(BaseMapper):
    _model = Publisher

    _mappings_fields = (('name', 'name'),)
    _update_fields = {'name'}


class DeveloperMapper(BaseMapper):
    _model = Developer

    _mappings_fields = (('name', 'name'),)
    _update_fields = {'name'}


class ConcurrentPriceMapper(BaseMapper):
    _model = ConcurrentPrice

    _mappings_fields = (('concurrent_id', 'concurrent_id'), ('game_id', 'game_id'), ('price', 'price'),
                        ('is_lower_price', 'is_lower_price'),)
    _update_fields = {'price', 'is_lower_price'}
