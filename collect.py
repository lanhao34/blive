import toml
import requests
import logging
import pymongo
import time
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from functools import partial
from bilibili_api import sync, live

logging.basicConfig(level=logging.DEBUG, filename='log/collect.log', filemode='a', 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

url = "https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids"

conf = toml.load("collect.toml")
print(conf)
# rooms = dict([(uid, live.LiveRoom(uid)) for uid in conf['uids']])

client = pymongo.MongoClient("mongodb://localhost:27017/")
async def get_info_by_uids(uids: int) -> dict:
    logging.debug(f'Pull room info of user {uids}.')
    r = requests.get(url, params={'uids[]': uids}).json()['data']
    # print(r)
    for uid, data in r.items():
        if data['live_status']:
            data['current_time'] = time.time()
            gaoneng = await live.LiveRoom(int(data['room_id'])).get_gaonengbang(1)
            data['gaonengbang'] = gaoneng['onlineNum']
            client[uid][str(data['live_time'])].insert_one(data)
    return data


if __name__ == '__main__':
    scheduler = AsyncIOScheduler()

    task = partial(get_info_by_uids, conf['uids'])
    sync(get_info_by_uids(conf['uids']))
    # 添加任务到调度器，并设置触发器为每10分钟执行一次
    scheduler.add_job(task, 'interval', minutes=conf['interval'])

    # 启动调度器
    scheduler.start()

    # 运行事件循环
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.shutdown()
        loop.close()