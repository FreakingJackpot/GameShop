from copy import deepcopy

from website.models import Game, GameImage


class Cart:
    def __init__(self, session):
        self.session = session
        self.cart = self.session.get('cart')
        if not self.cart:
            self.cart = self.session['cart'] = {}
            self.save()

    def __iter__(self):
        for game in self.cart.values():
            yield game

    @property
    def total_price(self):
        total = 0
        for game in self:
            price = game.get('discount_price') or game['price']
            total += price

        return total

    def handle_request(self, game_id, quantity):
        if game_id not in self.cart and quantity:
            game = Game.obj_by_pk(game_id)
            header = GameImage.objects.filter(game=game, is_header=True).first()
            self.cart[game_id] = {
                'id': game.id,
                'name': game.name,
                'quantity': int(quantity),
                'header': header.url,
                'discount_price': float(game.discount_price) if game.discount_price else None,
                'price': float(game.price),
            }

            if game.discount_price:
                self.cart[game_id]['discount'] = float(game.price - game.discount_price)
                self.cart[game_id]['discount_percent'] = game.applied_rule.discount_percent

        elif quantity:
            self.cart[game_id]['quantity'] = quantity
        else:
            self.cart.pop(str(game_id))

        self.save()

    def save(self):
        self.session['cart'] = self.cart
        self.session.save()

    def flush(self):
        self.cart = {}
        self.save()

    def to_dict(self):
        cart = deepcopy(self.cart)
        cart['total_price'] = self.total_price
        return cart
