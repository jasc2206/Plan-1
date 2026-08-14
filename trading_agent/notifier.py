import requests

from .config import settings


class ConsoleNotifier:
    def send(self, message: str) -> None:
        print(message)


class TelegramNotifier:
    def __init__(self):
        self.token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id

    def send(self, message: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        requests.post(url, json={"chat_id": self.chat_id, "text": message}, timeout=10)


def get_notifier():
    if settings.telegram_bot_token and settings.telegram_chat_id:
        return TelegramNotifier()
    return ConsoleNotifier()
