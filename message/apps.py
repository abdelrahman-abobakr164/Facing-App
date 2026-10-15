from django.apps import AppConfig


class MessageConfig(AppConfig):
    name = "message"

    import message.signals
