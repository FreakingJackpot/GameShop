from tempfile import NamedTemporaryFile

from django.core.mail import EmailMessage


def send_order_mail(email, keys):
    temp = NamedTemporaryFile()

    with open(temp.name, 'w') as f:
        for game_name, keys_ in keys.items():
            f.writelines([game_name + '\n', ',\n'.join(keys_), '\n'])

    with open(temp.name, 'rb') as f:
        mail = EmailMessage('Ваш заказ', 'Купленные ключи находятся в приложенном файле', to=[email, ])
        mail.attach('Ключи.txt', f.read(), 'text/plain')
        mail.send()

    temp.close()
