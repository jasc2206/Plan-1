import requests

from trading_agent.notifier import TelegramNotifier


class RaisingSession:
    def post(self, *args, **kwargs):
        raise requests.exceptions.ReadTimeout("simulated timeout")


def test_telegram_send_survives_network_failure(monkeypatch):
    monkeypatch.setattr(
        requests, "post",
        lambda *a, **k: (_ for _ in ()).throw(requests.exceptions.ReadTimeout("simulated timeout")),
    )
    notifier = TelegramNotifier()
    notifier.token = "fake-token"
    notifier.chat_id = "fake-chat-id"
    notifier.send("mensaje de prueba")  # no debe lanzar excepcion
