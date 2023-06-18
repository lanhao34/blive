from sanic import Sanic
from sanic.response import json, html

from pyecharts import options as opts
from pyecharts.charts import Line

import pymongo
from typing import List
import datetime
import pandas as pd

# 初始化 Sanic
app = Sanic(__name__)

client = pymongo.MongoClient("mongodb://localhost:27017/")
pipeline = [{"$project": {"online": 1, "current_time": 1, "gaonengbang": 1}}]
def read_info(uid: int) -> List:
    last_collection = client[str(uid)].list_collection_names()[-1]
    results = client[str(uid)][last_collection].aggregate(pipeline)
    return results

def line_base(uid) -> Line:
    collections = map(int, client[str(uid)].list_collection_names())
    last_collection = sorted(collections)[-1]
    results = list(client[str(uid)][str(last_collection)].aggregate(pipeline))
    times = [datetime.datetime.fromtimestamp(int(r['current_time'])) for r in results]
    counts = [r['gaonengbang'] for r in results]
    date = datetime.datetime.fromtimestamp(last_collection)
    formatted_date = date.strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame(results)
    df['date'] = pd.to_datetime(df['current_time'])
    print(df)
    # for r in results:
    #     print(r)
    # print(times, counts)
    c = (
        Line()
        .add_xaxis(times)
        .add_yaxis("Count", counts)
        .set_global_opts(
            title_opts=opts.TitleOpts(title=formatted_date),
            xaxis_opts=opts.AxisOpts(type_="time", name="Time"),
            yaxis_opts=opts.AxisOpts(name="Count"),
        )
    )
    return c

uid = 777964
@app.route("/lineChart", methods=["GET"])
async def draw_line_chart(request):
    c = line_base(uid)
    return json(c.dump_options_with_quotes())


@app.route("/", methods=["GET"])
async def index(request):
    return html(open("./templates/index.html").read())


if __name__ == '__main__':
    app.run(host='0.0.0.0')