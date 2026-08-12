import logging

import requests

from radar.config import settings


logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None) -> None:
        self.token = token if token is not None else settings.telegram_token
        self.chat_id = chat_id if chat_id is not None else settings.chat_id

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send_message(self, text: str, parse_mode: str | None = None) -> bool:
        if not self.is_configured:
            logger.warning("Telegram não configurado")
            return False

        payload = {"chat_id": self.chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            response = requests.post(url, json=payload, timeout=20)
            return response.status_code == 200
        except requests.RequestException:
            logger.exception("Erro ao enviar mensagem para Telegram")
            return False
