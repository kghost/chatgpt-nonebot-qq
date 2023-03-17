import json
from typing import Union, Callable

import aiohttp
from loguru import logger

from ..constants import CONFIG

async def get_access_token():
    async with aiohttp.ClientSession() as session:
        async with session.post(
                "https://aip.baidubce.com/oauth/2.0/token",
                params={
                    "grant_type": "client_credentials",
                    "client_id": CONFIG["baiducloud"]["client_id"],
                    "client_secret": CONFIG["baiducloud"]["client_secret"],
                }
        ) as response:
            response.raise_for_status()
            result = await response.json()
            access_token = result.get("access_token")

            # 保存access_token到文件
            data = {"access_token": access_token}
            with open("data/baidu_access_token.json", "w") as f:
                json.dump(data, f)

            return access_token


async def read_access_token():
    try:
        with open("data/baidu_access_token.json", "r") as f:
            data = json.load(f)
            access_token = data["access_token"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        access_token = None

    return access_token


class MiddlewareBaiduCloud:
    async def handle_respond(self, response: str):
        try:
            if CONFIG["baiducloud"]["check"]:
                access_token = await read_access_token()
                if not access_token:
                    logger.debug(f"正在获取access_token，请稍等")
                    access_token = await get_access_token()

                baidu_url = f"https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined" \
                            f"?access_token={access_token}"
                headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}

                async with aiohttp.ClientSession() as session:
                    async with session.post(baidu_url, headers=headers, data={'text': response}) as result:
                        result.raise_for_status()
                        response_dict = await result.json()

                    logger.debug(f"百度云: {response_dict}")
                    # 处理百度云审核结果
                    if response_dict["conclusion"] in "合规":
                        return response

                    if len(response_dict['data']) == 1 and response_dict['data'][0]['msg'] == "存在低俗辱骂不合规":
                        return response

                    msg = response_dict['data'][0]['msg']
                    return f"[百度云]请珍惜机器人，当前返回内容不合规\n原因：{msg}"
            # 未审核消息路径
            else:
                return response
        except aiohttp.ClientError as e:
            logger.error(f"HTTP error occurred: {e}")
            return f"百度云判定出错\n以下是原消息：{rendered}"
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error occurred: {e}")
        except StopIteration as e:
            logger.error(f"StopIteration exception occurred: {e}")
