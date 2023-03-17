import sys

import nonebot

from nonebot.adapters.onebot.v11 import adapter
from nonebot import log

log.logger.remove()
logger_id = log.logger.add(sys.stdout, level=0, diagnose=False)


nonebot.init()

driver = nonebot.get_driver()

# adapter_config = driver._adapters["OneBot V12"].config

driver.register_adapter(adapter.Adapter)

nonebot.load_plugins("src/plugins")

nonebot.run()
