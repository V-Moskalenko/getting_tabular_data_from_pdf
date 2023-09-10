import logging
from tendo import singleton
from telegram_bot import telebot_module

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    try:
        logger.info('Старт')
        me = singleton.SingleInstance
        telebot_module.bot.infinity_polling()
    except Exception as e:
        logger.error(f'Ошибка в main - {e}')
        telebot_module.bot.infinity_polling()
