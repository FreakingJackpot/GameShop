import datetime

from website.models import PriceRule, Game


class RulesController:
    _mtm_fields = ('genres', 'categories', 'developers', 'publishers',)

    def __init__(self):
        self._rules = PriceRule.get_all_rules()

    def apply_rules(self):
        games = Game.get_all_for_rules_applying()
        games_with_rules = []
        for game in games:
            for rule in self._rules:
                if self.check_rule(game, rule):
                    game.apply_rule(rule)
                    games_with_rules.append(game)

        Game.objects.bulk_update(games_with_rules, ['discount_price', 'applied_rule'], batch_size=500)

    def check_rule(self, game, rule):
        if game.steam_game_id in set([i.id for i in rule.steam_apps.all()]):
            return True

        for field in self._mtm_fields:
            game_ids = set([i.id for i in getattr(game, field).all()])
            rule_ids = set([i.id for i in getattr(rule, field).all()])

            if rule_ids and not (rule_ids & game_ids):
                return False

        if rule.release_date_lower and rule.release_date_lower < game.release_date:
            return False

        if (rule.upper_price_border and game.price > rule.upper_price_border) or (
                rule.lower_price_border and game.price < rule.lower_price_border):
            return False

        return True

    def delete_outdated(self):
        outdated = []
        for rule in self._rules:
            if rule.ends >= datetime.now():
                outdated.append(rule.id)

        games = Game.get_objs_with_rules(outdated)
        for i in games:
            i.discount_price = None
            i.applied_rule = None
        Game.objects.bulk_update(games, ['discount_price', 'applied_rule'], batch_size=500)

        PriceRule.delete_by_ids(outdated)
