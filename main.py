from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup as bs
import json
import time
import asyncio

URL = "https://makerworld.com/en/@theblackcat"
app = FastAPI()


def collect_data():
    data = {
        "timestamp": int(time.time()),
        "stats": {},
        "uploads": []
    }

    page = requests.get(URL)
    soup = bs(page.content, "html.parser")

    # loop each element .portal-css-1rrizxm .portal-css-c85l1y
    for i, stat in enumerate(soup.find_all(class_="portal-css-1rrizxm")[0].find_all(class_="portal-css-c85l1y")):
        if i == 0:
            data["stats"]["likes"] = int(stat.text)
        elif i == 1:
            data["stats"]["collections"] = int(stat.text)
        elif i == 2:
            data["stats"]["downloads"] = int(stat.text)
        elif i == 3:
            data["stats"]["prints"] = int(stat.text)

    # get .portal-css-20hjsn .number text
    data["stats"]["followers"] = int(soup.find_all(class_="portal-css-20hjsn")[0].find(class_="number").text)

    # get all elements with class portal-css-wvs238
    uploads = soup.find_all(class_="portal-css-wvs238")

    # loop through all elements
    for upload in uploads:
        element = {
            "id": upload.find("a")["href"].split("/")[-1],
            "title": upload.find(class_="portal-css-xzqryk").text,
            "stats": {
                "likes": 0,
                "collections": 0,
                "downloads": 0,
                "prints": 0,
            }
        }

        # loop portal-css-5h23f0 classes and get text
        for i, upload_stats in enumerate(upload.find_all(class_="portal-css-5h23f0")):
            if i == 0:
                element["stats"]["likes"] = int(upload_stats.text)
            elif i == 1:
                element["stats"]["collections"] = int(upload_stats.text)
            elif i == 2:
                element["stats"]["downloads"] = int(upload_stats.text)
            elif i == 3:
                element["stats"]["prints"] = int(upload_stats.text)
        data["uploads"].append(element)

    return data


def collect_and_save_data():
    data = collect_data()
    try:
        with open("data.json", "w") as f:

            # file is history: [] array of data with { data: data, timestamp: timestamp }
            # if file is empty, create empty array

            try:
                history = json.loads(f.read())
            except:
                history = []

            # append new data to history
            history.append({
                "data": data,
            })

            # write history to file
            f.write(json.dumps(history))
    except FileNotFoundError as e:
        return {}
    return data


@app.get("/")
async def get_last():
    return collect_and_save_data()


@app.get("/history")
async def get_history():
    try:
        with open("data.json", "r") as f:
            return json.loads(f.read())
    except FileNotFoundError as e:
        return []


@app.on_event("startup")
async def startup_event():
    collect_and_save_data()

    # run collect_and_save_data every 15 minutes
    while True:
        await asyncio.sleep(900)
        collect_and_save_data()
