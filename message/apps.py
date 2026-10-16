from django.apps import AppConfig


class MessageConfig(AppConfig):
    name = "message"

    def ready(self):
        import message.signals
