from nonebot import on
from nonebot.adapters import Bot
from nonebot.adapters import Event

from .chatgpt import constants
from .chatgpt import bot as gpt

meta = on(type="meta")

message = on(type="message")


@message.handle()
async def handle_message(bot: Bot, event: Event):
    if event.sub_type == 'normal' and event.message_type == 'group':
        if not event.original_message or len(event.original_message) < 1:
            return
        at = event.original_message[0]
        if at.type != 'at' or not at.data or 'qq' not in at.data or at.data['qq'] != constants.CONFIG['qq']:
            return

        await gpt.handle_group_message(bot, event)
    if event.sub_type == 'friend' and event.message_type == 'private':
        await gpt.handle_private_message(bot, event)
