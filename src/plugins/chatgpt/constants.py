from . import conversation

CONFIG = {
    "qq": "your_bot_qq_number",
    "openai": {
        "api_key": "your_openai_api_key"
    },
    "baiducloud": {
        "check": True,
        "client_id": "your_baidu_api_key",
        "client_secret": "your_baidu_secret_key"
    }
}

contexts = conversation.ContextManager()
