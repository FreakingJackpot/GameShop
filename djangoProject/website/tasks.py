import logging
import traceback
from io import BytesIO

from celery import shared_task, current_task
from django.core.mail import mail_managers
from django.core.management import call_command

from .models import Order
from .utils.email_messages import send_order_mail
from .utils.incomings_importer import IncomingsImporter
from .utils.logging import task_running_alert, task_failure_alert, task_success_alert, get_task_logger, Logger
from .utils.mappers import SteamGameMapper
from .utils.rules_controller import RulesController
from .utils.steam_api_handlers import SteamGamesListEndpoint


@shared_task
def import_incoming(excel_file: str):
    task_running_alert('import_incoming', current_task.request.id)
    try:
        IncomingsImporter(BytesIO(excel_file)).import_incoming()
        mail_managers("Incomings Imported", "Everything was imported")
        import_games.delay()
    except Exception as e:
        logger = get_task_logger()
        Logger(logger).log(logging.ERROR, str(e), {'traceback': traceback.format_exc()})
        task_failure_alert('import_incoming', current_task.request.id)

        return

    task_success_alert('import_incoming', current_task.request.id)


@shared_task
def load_steam_ids():
    task_running_alert('load_steam_ids', current_task.request.id)
    try:
        data = SteamGamesListEndpoint().get_all_data()
        SteamGameMapper(data).upsert()
    except Exception as e:
        logger = get_task_logger()
        Logger(logger).log(logging.ERROR, str(e), {'traceback': traceback.format_exc()})
        task_failure_alert('load_steam_ids', current_task.request.id)
        return

    task_success_alert('load_steam_ids', current_task.request.id)


@shared_task
def import_games():
    task_running_alert('import_games', current_task.request.id)
    try:
        call_command("import_games")
    except Exception as e:
        logger = get_task_logger()
        Logger(logger).log(logging.ERROR, str(e), {'traceback': traceback.format_exc()})
        task_failure_alert('import_games', current_task.request.id)
        raise Exception(e)

    task_success_alert('import_games', current_task.request.id)


@shared_task
def import_steam_prices():
    task_running_alert('import_steam_prices', current_task.request.id)
    try:
        call_command('import_steam_prices')
    except Exception as e:
        logger = get_task_logger()
        Logger(logger).log(logging.ERROR, str(e), {'traceback': traceback.format_exc()})
        task_failure_alert('import_steam_prices', current_task.request.id)
        raise Exception(e)

    task_success_alert('import_steam_prices', current_task.request.id)


@shared_task
def import_plati_prices():
    task_running_alert('import_plati_prices', current_task.request.id)
    try:
        call_command('import_plati_prices')
    except Exception as e:
        logger = get_task_logger()
        Logger(logger).log(logging.ERROR, str(e), {'traceback': traceback.format_exc()})
        task_failure_alert('import_plati_prices', current_task.request.id)
        raise Exception(e)
    task_success_alert('import_plati_prices', current_task.request.id)


@shared_task
def apply_rules():
    task_running_alert('apply_rules', current_task.request.id)
    try:
        RulesController().apply_rules()

    except Exception as e:
        logger = get_task_logger()
        Logger(logger).log(logging.ERROR, str(e), {'traceback': traceback.format_exc()})
        task_failure_alert('apply_rules', current_task.request.id)
        raise Exception(e)
    task_success_alert('apply_rules', current_task.request.id)


@shared_task
def delete_outdated_rules():
    RulesController().delete_outdated()


@shared_task
def order_process(email, cart_dict):
    keys = Order.create_order(email, cart_dict)
    send_order_mail(email, keys)
