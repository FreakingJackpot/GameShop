from django.core.management import BaseCommand

from website.utils.rules_controller import RulesController


class Command(BaseCommand):
    def handle(self, *args, **options):
        RulesController().apply_rules()
