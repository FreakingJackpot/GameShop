import uuid
from decimal import Decimal

from django.db import models
from django.db.models import Prefetch


class MapperMixin(models.Model):
    key_fields: tuple

    class Meta:
        abstract = True

    @classmethod
    def get_all_keys(cls) -> models.QuerySet:
        return cls.objects.values_list(*cls.key_fields)

    @classmethod
    def get_by_keys(cls, keys: tuple) -> models.QuerySet:
        filter_params = {f"{field}__in": (key[i] for key in keys) for i, field in enumerate(cls.key_fields)}
        return cls.objects.filter(**filter_params)

    @classmethod
    def get_ids_by_keys(cls, keys: tuple) -> models.QuerySet:
        filter_params = {f"{field}__in": (key[i] for key in keys) for i, field in enumerate(cls.key_fields)}
        return cls.objects.filter(**filter_params).values_list('id', flat=True)

    def get_key(self):
        return tuple(getattr(self, field) for field in self.key_fields)


class SteamGame(MapperMixin):
    steam_id = models.IntegerField('Id в Steam', unique=True)
    name = models.TextField('Имя')

    key_fields = ('steam_id',)

    class Meta:
        verbose_name = 'Игра в Steam'
        verbose_name_plural = 'Игры в Steam'

    def __str__(self):
        return f'{self.steam_id} ({self.name})'

    @classmethod
    def get_id_by_name(cls, name):
        obj = cls.objects.filter(name=name).first()
        return obj.id if obj else None

    @classmethod
    def get_id_by_steam_id_map(cls, steam_ids):
        return dict(cls.objects.filter(steam_id__in=steam_ids).values_list('steam_id', 'id'))


class Game(MapperMixin):
    name = models.TextField('Имя')
    steam_game = models.OneToOneField('SteamGame', on_delete=models.CASCADE)
    description = models.TextField('Описание')
    release_date = models.DateField('Дата релиза')
    requirements = models.TextField('Системные требования')
    genres = models.ManyToManyField('Genre')
    categories = models.ManyToManyField('Category')
    developers = models.ManyToManyField('Developer')
    publishers = models.ManyToManyField('Publisher')
    price = models.DecimalField(max_digits=7, decimal_places=2)
    discount_price = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)

    applied_rule = models.ForeignKey('PriceRule', on_delete=models.SET_NULL, null=True, blank=True)

    key_fields = ('steam_game_id',)

    class Meta:
        verbose_name = 'Игра на сайте'
        verbose_name_plural = 'Игры на сайте'

    def __str__(self):
        return f'{self.id} ({self.name})'

    @classmethod
    def steam_game_id_to_id(cls, steam_ids):
        return dict(cls.objects.filter(steam_game_id__in=steam_ids).values_list('steam_game_id', 'id'))

    @classmethod
    def obj_by_steam_id(cls, **kwargs):
        steam_ids = kwargs.get('steam_ids')
        if steam_ids:
            return {obj.steam_game.steam_id: obj for obj in cls.objects.filter(steam_game__steam_id__in=steam_ids)}
        else:
            steamgame_ids = kwargs.get('steamgame_ids')
            return {obj.steam_game.steam_id: obj for obj in
                    cls.objects.select_related('steam_game').filter(steam_game_id__in=steamgame_ids)}

    @classmethod
    def id_by_steam_game_id_map(cls, steam_game_ids):
        return dict(cls.objects.filter(steam_game_id__in=steam_game_ids).values_list('steam_game_id', 'id'))

    @classmethod
    def get_steam_ids(cls):
        return cls.objects.values_list('steam_id', flat=True)

    @classmethod
    def get_all_ids(cls):
        return cls.objects.values_list('id', flat=True)

    @classmethod
    def get_all_for_rules_applying(cls):
        prefetches = [
            Prefetch('steam_game', queryset=SteamGame.objects.all().only('steam_id')),
            Prefetch('categories', queryset=Category.objects.all().only('id')),
            Prefetch('developers', queryset=Developer.objects.all().only('id')),
            Prefetch('publishers', queryset=Publisher.objects.all().only('id')),

        ]
        return cls.objects.all().prefetch_related(*prefetches)

    @classmethod
    def get_id_by_name(cls, name):
        obj = cls.objects.filter(name=name).first()
        return obj.id if obj else None

    @classmethod
    def get_by_ids(cls, ids):
        return cls.objects.filter(id__in=ids)

    @classmethod
    def get_objs_with_rules(cls, rule_ids):
        return cls.objects.filter(applied_rule_id__in=rule_ids)

    @classmethod
    def get_obj_for_list_view(cls):
        return cls.objects.filter(steam_game__incoming__key__is_sold=False).order_by('-applied_rule_id').distinct()

    @classmethod
    def obj_by_pk(cls, pk):
        return cls.objects.select_related('applied_rule').prefetch_related('categories', 'genres', 'developers',
                                                                           'publishers').get(id=pk)

    def apply_rule(self, rule):
        self.discount_price = self.price - self.price * Decimal(rule.discount_percent) / 100
        self.applied_rule = rule


class GameImage(MapperMixin):
    url = models.TextField(unique=True)
    game = models.ForeignKey('Game', on_delete=models.CASCADE)
    is_header = models.BooleanField(default=False)

    key_fields = ('url',)

    class Meta:
        verbose_name = 'Фото игры'
        verbose_name_plural = 'Фото игр'

    def __str__(self):
        return f'{self.game} (Главная:{self.is_header})'


class Genre(MapperMixin):
    name = models.TextField(unique=True)

    key_fields = ('id',)

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return f'{self.name}'


class Category(MapperMixin):
    name = models.TextField()

    key_fields = ('id',)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Категории"

    def __str__(self):
        return f'{self.id} ({self.name})'


class Publisher(MapperMixin):
    name = models.TextField(unique=True)

    key_fields = ('name',)

    class Meta:
        verbose_name = 'Издатель'
        verbose_name_plural = 'Издатели'

    def __str__(self):
        return f'{self.id} ({self.name})'

    @classmethod
    def get_name__id_map(cls):
        return dict(cls.objects.values_list('name', 'id'))


class Developer(MapperMixin):
    name = models.TextField(unique=True)

    key_fields = ('name',)

    class Meta:
        verbose_name = 'Разработчик'
        verbose_name_plural = 'Разработчики'

    def __str__(self):
        return f'{self.id} ({self.name})'

    @classmethod
    def get_id_name_map(cls):
        return dict(cls.objects.values_list('name', 'id'))


class Concurrent(models.Model):
    name = models.TextField(unique=True,
                            help_text="Два типа названий: <Имя> - самостоятельный конкурент, "
                                      "<Маркетплейс>.<Имя> - продавец с маркетплейса ")

    class Meta:
        verbose_name = 'Конкурент'
        verbose_name_plural = 'Конкуренты'

    def __str__(self):
        return f'{self.id} ({self.name})'

    @classmethod
    def map_name_to_id(cls):
        return dict(cls.objects.values_list('name', 'id'))


class ConcurrentPrice(MapperMixin):
    concurrent = models.ForeignKey('Concurrent', on_delete=models.CASCADE)
    game = models.ForeignKey('Game', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)
    is_lower_price = models.BooleanField(default=False)

    key_fields = ('concurrent_id', 'game_id')

    class Meta:
        verbose_name = 'Цена конкурента'
        verbose_name_plural = 'Цены конкурентов'
        unique_together = (('concurrent', 'game'),)

    def __str__(self):
        return f'{self.game} ({self.concurrent})'


class Distributor(models.Model):
    name = models.TextField()

    class Meta:
        verbose_name = 'Дистрибьютор'
        verbose_name_plural = 'Дистрибьюторы'

    def __str__(self):
        return f'{self.id} ({self.name})'

    @classmethod
    def get_by_name(cls, name):
        return cls.objects.filter(name=name).first()


class Incoming(models.Model):
    distributor = models.ForeignKey('Distributor', on_delete=models.CASCADE)
    game = models.ForeignKey('SteamGame', on_delete=models.CASCADE)
    date = models.DateField('Дата отгрузки', auto_now_add=True)
    count = models.IntegerField('Число ключей')

    class Meta:
        verbose_name = 'Поступление'
        verbose_name_plural = 'Поступления'

    def __str__(self):
        return f'{self.date} {self.distributor.name} {self.game.name}'

    @classmethod
    def get_steam_ids(cls):
        return cls.objects.values_list('game__steam_id', flat=True).distinct()


class Key(models.Model):
    incoming = models.ForeignKey('Incoming', on_delete=models.CASCADE)
    value = models.TextField('Ключ')
    is_sold = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Ключ'
        verbose_name_plural = 'Ключи'

    def __str__(self):
        return f'{self.incoming.game.name} {self.is_sold}'


class PriceRule(models.Model):
    name = models.TextField('Имя')
    priority = models.IntegerField()

    steam_apps = models.ManyToManyField(SteamGame, related_name='steam_apps',
                                        help_text='Steam Id игр, правило применяется ко всем играм, указанных здесь.'
                                                  ' Другие ограничения не учитываются', blank=True)
    release_date_lower = models.DateField('Дата выхода меньше чем', null=True, blank=True)

    genres = models.ManyToManyField('Genre', related_name='genres', blank=True)
    categories = models.ManyToManyField('Category', related_name='categories', blank=True)
    developers = models.ManyToManyField('Developer', related_name='developers', blank=True)
    publishers = models.ManyToManyField('Publisher', related_name='publishers', blank=True)

    upper_price_border = models.DecimalField('Верхняя граница цены', max_digits=7, decimal_places=2, null=True,
                                             blank=True)
    lower_price_border = models.DecimalField('Нижняя граница цены', max_digits=7, decimal_places=2, null=True,
                                             blank=True)

    discount_percent = models.FloatField()

    starts = models.DateTimeField()
    ends = models.DateTimeField()

    class Meta:
        verbose_name = 'Правило'
        verbose_name_plural = 'Правила'

    def __str__(self):
        return f'{self.id} ({self.name})'

    @classmethod
    def get_all_rules(cls):
        prefetches = [
            Prefetch('steam_apps', queryset=SteamGame.objects.all().only('steam_id')),
            Prefetch('categories', queryset=Category.objects.all().only('id')),
            Prefetch('developers', queryset=Developer.objects.all().only('id')),
            Prefetch('publishers', queryset=Publisher.objects.all().only('id')),

        ]
        return cls.objects.prefetch_related(*prefetches).order_by('priority').all()

    @classmethod
    def delete_by_ids(cls, ids):
        cls.objects.filter(id__in=ids).delete()


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    date = models.DateField(auto_now_add=True)
    price = models.DecimalField(max_digits=9, decimal_places=2)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.date} {self.email}'

    @classmethod
    def create_order(cls, email, cart_dict):
        order = cls(email=email, price=cart_dict.pop('total_price'))
        order.save()

        keys = {}
        for cart_item in cart_dict.values():
            game = Game.obj_by_pk(cart_item['id'])
            game_keys = OrderItem.create(order, game, cart_item['quantity'])
            keys.update(game_keys)

        return keys


class OrderItem(models.Model):
    key = models.ForeignKey('Key', on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    original_price = models.DecimalField(max_digits=7, decimal_places=2)
    final_price = models.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.order_id} {self.key.incoming.game.name}'

    @classmethod
    def create(cls, order, game, quantity):
        objs = []
        key_ids = []

        keys = Key.objects.filter(incoming__game_id=game.steam_game_id, is_sold=False)[:quantity]
        for key in keys:
            item = cls(key=key, order=order)
            if game.discount_price:
                item.original_price, item.final_price = game.price, game.discount_price
            else:
                item.original_price, item.final_price = game.price, game.price

            objs.append(item)
            key_ids.append(key.id)

        Key.objects.filter(id__in=key_ids).update(is_sold=True)
        OrderItem.objects.bulk_create(objs)

        return {game.name: (key.value for key in keys)}
