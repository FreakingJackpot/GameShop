import requests

import logging


def get_task_logger():
    return Logger(logging.getLogger('task'))


class Logger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log(self, level, msg, **extra):
        dict_message = {
            'message': msg,
            **extra,
        }
        self.logger.log(level, dict_message)


def configure_telepush_url():
    return f'http://localhost:8083/api/messages/39f4ba'


TELEPUSH_URL = configure_telepush_url()


def push_alert(header, task_name, run_id):
    text = "{}\n\nTask: {}\n\nRun ID: {}".format(
        header,
        task_name.replace('_', '\_'),
        run_id.replace('_', '\_')
    )

    requests.post(TELEPUSH_URL, json={'text': text})


def task_failure_alert(task_name, run_id):
    push_alert("**🔥Task failed🔥**", task_name, run_id)


def task_success_alert(task_name, run_id):
    push_alert("**✅Task succeeded✅**", task_name, run_id)


def task_running_alert(task_name, run_id):
    push_alert("**🚧Task started🚧**", task_name, run_id)
