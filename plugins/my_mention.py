# coding: utf-8
from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ
import subprocess
import re
from pytz import timezone
import datetime
import requests
import sys
from bs4 import BeautifulSoup
import json

#kaggleで開催中のコンペの残り日数を取得
@listen_to('reminder')
def listen_func(message):
    #コマンド実行、結果を整形
    competitions_list = subprocess.check_output(["kaggle", "competitions", "list"])
    tmp1 = str(competitions_list).split("\\n")
    tmp2 = [re.split(" +", i) for i in tmp1][2:-1]

    time = datetime.datetime.now()
    #herokuはUTC、localはJSTのため調整
    #time -= datetime.timedelta(hours = 9)

    output=[]
    for k in tmp2:
        deadline = datetime.datetime.strptime(k[1], '%Y-%m-%d')
        deadline += datetime.timedelta(days = 1) #１日分調整
        if deadline > time:
            remaining_time = str(deadline - time).split(",")[0]
            #残り日数で絵文字を変更
            if ":" in remaining_time: #1日以内のとき
                output.append("{} : {} :thumbsup_all:".format(k[0],remaining_time))
            elif int(remaining_time.split(" ")[0]) < 8:　#7日以内のとき
                output.append("{} : {} :fire:".format(k[0],remaining_time))
            elif int(remaining_time.split(" ")[0]) < 31:　#30日以内のとき
                output.append("{} : {} :eyes:".format(k[0],remaining_time))
            elif int(remaining_time.split(" ")[0]) < 101:　#100日以内のとき
                output.append("{} : {}".format(k[0],remaining_time))

    #残り時間が少ない順に出力
    for i in output[::-1]:
        message.send(i)

#act "ユーザ名" でkaggleでの１週間のsubmit数を出力
#act "ユーザ名" all で年間や月間のsubmit数を出力
@listen_to('^act')
def listen_func(message):
    #入力を読み込み
    text = message.body['text']
    #message.send(text)
    try:
        messages=text.split(" ")
        username=messages[1]
    #print(username)
    except:
        message.send("incorrect input")
        message.send("フォーマットは act \"username\" (all) です")
        #print("incorrect input")
        #print("フォーマットは act \"username\" (all) です")
        #sys.exit()
        return 0

    user_url = "https://www.kaggle.com/{}".format(username)
    r = requests.get(user_url)         #requestsを使って、webから取得
    soup = BeautifulSoup(r.text, 'lxml') #要素を抽出
    for k in soup.find("title"):
        display_name=k.split("|")[0]
        #print(display_name)
        break

    #404の処理
    if display_name== "Kaggle: Your Home for Data Science":
        message.send("incorrect user")
        message.send("username {} は存在しません。".format(username))
        #sys.exit()
        return 0

    act_url="https://www.kaggle.com/{}/activity.json".format(username)
    data = requests.get(act_url).text
    json_data = json.loads(data)
    time=datetime.datetime.now()-datetime.timedelta(hours=9)
    submit_year=0
    submit_month=0
    submit_week=0
    for i in json_data:
        submit_year+=int(i["totalSubmissions"])
        if time-datetime.timedelta(days=30)<=datetime.datetime.strptime(i["date"], "%Y-%m-%dT%H:%M:%SZ"):
            submit_month+=int(i["totalSubmissions"])
        if time-datetime.timedelta(weeks=1)<=datetime.datetime.strptime(i["date"], "%Y-%m-%dT%H:%M:%SZ"):
            submit_week+=int(i["totalSubmissions"])

    #オプション
    if len(messages)==3:
        if messages[2]=="all":
            message.send("{}さんのsubmit数".format(display_name))
            message.send("週間：{} submit".format(submit_week))
            message.send("月間：{} submit".format(submit_month))
            message.send("年間：{} submit".format(submit_year))
            #sys.exit()
            return 0

    message.send("{}さんの１週間のsubmit数：{} submit".format(display_name,submit_week))
