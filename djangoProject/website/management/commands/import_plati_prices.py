from django.core.management import BaseCommand

from website.models import Game
from website.utils.concurents import Plati


class Command(BaseCommand):
    def handle(self, *args, **options):
        game_ids = Game.get_all_ids()
        Plati(game_ids).search_and_load()
