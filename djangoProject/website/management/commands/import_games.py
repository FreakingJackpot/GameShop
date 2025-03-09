from django.core.management import BaseCommand

from website.models import Incoming
from website.utils.steam_api_handlers import SteamGameDetailsEndpoint
from website.utils.steam_data_processors import SteamDetailsProcessing


class Command(BaseCommand):
    def handle(self, *args, **options):
        steam_ids = Incoming.get_steam_ids()

        details = SteamGameDetailsEndpoint().get_details_by_ids(steam_ids)
        SteamDetailsProcessing.process(details)
