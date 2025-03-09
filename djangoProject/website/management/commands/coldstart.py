from django.core.management import BaseCommand

from website.tasks import load_steam_ids
from website.utils.steam_api_handlers import SteamGameDetailsEndpoint
from website.utils.steam_data_processors import SteamDetailsProcessing


class Command(BaseCommand):
    def handle(self, *args, **options):
        load_steam_ids()
        details = SteamGameDetailsEndpoint().get_details_by_ids(
            [1627720, 588650, 895400, 2527500, 2475490, 393380, 1167630, 1190000, 1145360, 240, 2183900,
             1086940, 2406770, 2186680, 1184370, 1184370])
        SteamDetailsProcessing.process(details)
