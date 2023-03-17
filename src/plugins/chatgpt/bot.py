import openai
from loguru import logger

from nonebot import adapters
from nonebot.adapters.onebot import v11

from . import constants
from .middlewares.baiducloud import MiddlewareBaiduCloud

# Set up OpenAI API key
openai.api_key = constants.CONFIG["openai"]["api_key"]

# Function to send a message to the OpenAI chatbot model and return its response


async def ask_openai(messages):
    # Use OpenAI's ChatCompletion API to get the chatbot's response
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=200,
        stop=None,
        temperature=0.7,
    )

    # Find the first response from the chatbot that has text in it (some responses may not have text)
    for choice in response.choices:
        if "text" in choice:
            return choice.text

    # If no response with text is found, return the first response's content (which may be empty)
    return response.choices[0].message.content


baidu = MiddlewareBaiduCloud()


def extract_message(event) -> str:
    text = ""
    for message in event.message:
        if message.type == 'at':
            pass
        elif message.type == 'reply':
            pass
        elif message.type == 'text':
            text = text + str(message)
        else:
            logger.warning(f"Unknown message type: {message.type}")
    return text


def remove_prefix_if_has(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return None


def get_preset(systems):
    if systems:
        reply = ""
        for index, system in enumerate(systems):
            reply = reply + str(index) + '. ' + system + '\n'
        return reply
    else:
        return '尚未设置任何设定'


async def handle_private_message(bot, event) -> None:
    async def respond_private_message(message: str):
        reply = adapters.Message([
            v11.MessageSegment.reply(event.message_id),
            v11.MessageSegment.text(message),
        ])
        await bot.send(event=event, message=reply)

    try:
        context = constants.contexts.get_user_context(event.user_id)
        question = extract_message(event)
        if question is None or not len(question):
            await respond_private_message("我听不懂你想问什么")
            return

        cmd = remove_prefix_if_has(question, '/设定')
        if cmd is not None:
            await respond_private_message(get_preset(context.get_system()))
            return

        cmd = remove_prefix_if_has(question, '/添加设定 ')
        if cmd is not None:
            context.add_system(cmd)
            await respond_private_message(get_preset(context.get_system()))
            return

        cmd = remove_prefix_if_has(question, '/删除设定 ')
        if cmd is not None:
            context.remove_system(int(cmd))
            await respond_private_message(get_preset(context.get_system()))
            return

        messages = context.ask_with_context(question)
        logger.info(f"OpenAI question: {messages}")
        response = await ask_openai(messages)
        logger.info(f"OpenAI response: {response}")

        checked_response = await baidu.handle_respond(response)
        send_result = await respond_private_message(checked_response)
        logger.info(f"Send response: {send_result}")
        context.push_conversation(question, response)
    except openai.error.InvalidRequestError as e:
        await respond_private_message("服务器拒绝了您的请求，原因是" + str(e))
    except Exception as e:  # 未处理的异常
        logger.exception(e)
        await respond_private_message("出现故障！")


async def handle_group_message(bot, event) -> None:
    async def respond_group_message(message: str):
        reply = adapters.Message([
            v11.MessageSegment.reply(event.message_id),
            v11.MessageSegment.text(message),
        ])
        await bot.send(event=event, message=reply)

    try:
        group_context = constants.contexts.get_group_context(event.group_id)
        user_context = group_context.get_user_context(event.user_id)
        question = extract_message(event)
        if question is None or not len(question):
            await respond_group_message("我听不懂你想问什么")
            return

        cmd = remove_prefix_if_has(question, '/群设定')
        if cmd is not None:
            await respond_group_message(get_preset(group_context.get_system()))
            return

        cmd = remove_prefix_if_has(question, '/添加群设定 ')
        if cmd is not None:
            group_context.add_system(cmd)
            await respond_group_message(get_preset(group_context.get_system()))
            return

        cmd = remove_prefix_if_has(question, '/删除群设定 ')
        if cmd is not None:
            group_context.remove_system(int(cmd))
            await respond_group_message(get_preset(group_context.get_system()))
            return

        cmd = remove_prefix_if_has(question, '/用户设定')
        if cmd is not None:
            await respond_group_message(get_preset(user_context.get_system()))
            return

        cmd = remove_prefix_if_has(question, '/添加用户设定 ')
        if cmd is not None:
            user_context.add_system(cmd)
            await respond_group_message(get_preset(user_context.get_system()))
            return

        cmd = remove_prefix_if_has(question, '/删除用户设定 ')
        if cmd is not None:
            user_context.remove_system(int(cmd))
            await respond_group_message(get_preset(user_context.get_system()))
            return

        messages = user_context.ask_with_context(question)
        logger.info(f"OpenAI question: {messages}")
        response = await ask_openai(messages)
        logger.info(f"OpenAI response: {response}")

        checked_response = await baidu.handle_respond(response)
        send_result = await respond_group_message(checked_response)
        logger.info(f"Send response: {send_result}")
        user_context.push_conversation(question, response)
    except openai.error.InvalidRequestError as e:
        await respond_group_message("服务器拒绝了您的请求，原因是" + str(e))
    except Exception as e:  # 未处理的异常
        logger.exception(e)
        await respond_group_message("出现故障！")
