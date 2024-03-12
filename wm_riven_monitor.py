import json
from collections import OrderedDict
import requests, time, re
import dingtalkchatbot.chatbot as cb
import datetime
import hashlib
import yaml
from lxml import etree
import sqlite3



counter = {}

#读取配置文件
def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.load(f,Loader=yaml.FullLoader)
        github_token = config['all_config']['github_token']
        translate = False
        if int(config['all_config']['translate'][0]['enable']) == 1:
            translate = True
        if int(config['all_config']['dingding'][0]['enable']) == 1:
            dingding_webhook = config['all_config']['dingding'][1]['webhook']
            dingding_secretKey = config['all_config']['dingding'][2]['secretKey']
            app_name = config['all_config']['dingding'][3]['app_name']
            return app_name,github_token,dingding_webhook,dingding_secretKey, translate
        elif int(config['all_config']['feishu'][0]['enable']) == 1:
            feishu_webhook = config['all_config']['feishu'][1]['webhook']
            app_name = config['all_config']['feishu'][2]['app_name']
            return app_name,github_token,feishu_webhook,feishu_webhook, translate
        elif int(config['all_config']['server'][0]['enable']) == 1:
            server_sckey = config['all_config']['server'][1]['sckey']
            app_name = config['all_config']['server'][2]['app_name']
            return app_name,github_token,server_sckey, translate
        elif int(config['all_config']['pushplus'][0]['enable']) == 1:
            pushplus_token = config['all_config']['pushplus'][1]['token']
            app_name = config['all_config']['pushplus'][2]['app_name']
            return app_name,github_token,pushplus_token, translate
        elif int(config['all_config']['tgbot'][0]['enable']) ==1 :
            tgbot_token = config['all_config']['tgbot'][1]['token']
            tgbot_group_id = config['all_config']['tgbot'][2]['group_id']
            app_name = config['all_config']['tgbot'][3]['app_name']
            return app_name,github_token,tgbot_token,tgbot_group_id, translate
        elif int(config['all_config']['tgbot'][0]['enable']) == 0 and int(config['all_config']['feishu'][0]['enable']) == 0 and int(config['all_config']['server'][0]['enable']) == 0 and int(config['all_config']['pushplus'][0]['enable']) == 0 and int(config['all_config']['dingding'][0]['enable']) == 0:
            print("[-] 配置文件有误, 五个社交软件的enable不能为0")

github_headers = {
    'Authorization': "token {}".format(load_config()[1])
}


#读取黑名单用户
def black_user():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        black_user = config['all_config']['black_user']
        return black_user

#初始化创建数据库
def create_database():
    conn = sqlite3.connect('data.db')
    #print("[]create_database 函数 连接数据库成功！")
    # logging.info("create_database 函数 连接数据库成功！")
    cur = conn.cursor()
    try:
        cur.execute('''CREATE TABLE IF NOT EXISTS keyword_monitor
                   (url_id TEXT,
                    weapon_url_name TEXT,
                    translated_weapon_url_name TEXT,
                    riven_name TEXT,
                    translated_attributes TEXT,
                    buyout_price TEXT,
                    starting_price TEXT,
                    ingame_name TEXT,
                    created TEXT);''')
        print("成功创建关键字监控表")
    except Exception as e:
        print("创建监控表失败！报错：{}".format(e))
    conn.commit()  # 数据库存储在硬盘上需要commit  存储在内存中的数据库不需要
    conn.close()
    if load_config()[0] == "dingding":
        dingding("test", "连接成功", load_config()[2], load_config()[3])
    elif load_config()[0] == "server":
        server("test", "连接成功", load_config()[2])
    elif load_config()[0] == "pushplus":
        pushplus("test", "连接成功", load_config()[2])        
    elif load_config()[0] == "tgbot":
        tgbot("test", "连接成功", load_config()[2], load_config()[3])


# 新的翻译函数，用于从文件加载翻译字典
def load_translation_dict(file_path):
    translation_dict = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                original_key, translated_value = line.strip().split('=')
                translation_dict[original_key] = translated_value
    except Exception as e:
        print(f"Error loading translation dictionary: {e}")
    return translation_dict

# 加载翻译字典
translation_dict = load_translation_dict('translation_dict.txt')

# 修改翻译函数
def translate_using_dict(text, translation_dict):
    # 如果 text 在字典中有对应的翻译，则返回翻译结果，否则返回原文本
    return translation_dict.get(text, text) #original_key_1 translated_value_1

#关键词搜索
def getKeywordNews(keyword):
    today_keyword_info_tmp = []
    try:
        # 抓取关键词内容
        api = "https://api.warframe.market/v1/auctions/search?type=riven&positive_stats={}&sort_by=price_desc".format(keyword)
        json_str = requests.get(api, timeout=10).json()
        #formatted_json = json.dumps(json_str, indent=2)
        #print(json_str)
        today_date = datetime.date.today()
        n = len(json_str['payload']['auctions'])
        if n > 30:
            n = 30
        for i in range(0, n):
            url_id = json_str['payload']['auctions'][i]['id']
            if url_id not in black_user():
                try:
                    weapon_url_name = json_str['payload']['auctions'][i]['item']['weapon_url_name'] #武器名称
                    translated_weapon_url_name = translate_using_dict(weapon_url_name, translation_dict)
                    riven_name = json_str['payload']['auctions'][i]['item']['name'] #紫卡词缀
                    attributes_list = [f"{attr['value']} {attr['url_name']}" for attr in json_str['payload']['auctions'][i]['item']['attributes']] #数值
                    # 翻译 sorted_attributes 中的内容
                    translated_attributes = [(value, translate_using_dict(url_name, translation_dict)) for attribute in attributes_list for value, url_name in [attribute.split(' ', 1)]]
                    buyout_price = json_str['payload']['auctions'][i]['buyout_price'] #买断价格
                    starting_price = json_str['payload']['auctions'][i]['starting_price'] #起标价格
                    ingame_name = json_str['payload']['auctions'][i]['owner']['ingame_name'] #游戏id
                    created = json_str['payload']['auctions'][i]['created'] #上架时间
                    created_tmp = re.findall('\d{4}-\d{2}-\d{2}', created)[0]
                    if created_tmp == str(today_date):
                        today_keyword_info_tmp.append({"riven_name": riven_name, "url_id": url_id, "weapon_url_name": weapon_url_name, "translated_weapon_url_name": translated_weapon_url_name, "translated_attributes": translated_attributes, "buyout_price": buyout_price, "starting_price": starting_price, "ingame_name": ingame_name, "created": created})
                        print("[+] keyword: {}-{}".format(translated_weapon_url_name, riven_name))
                    #else:
                        #print("[-] keyword: {} ,该{}-{}的更新时间为{}, 不属于今天".format(url_id, translated_weapon_url_name, riven_name, created))
                except Exception as e:
                    pass
            else:
                pass
        today_keyword_info = OrderedDict()
        for item in today_keyword_info_tmp:
            riven_id = item['url_id']
            if riven_id in counter:
                if counter[riven_id] < 2:
                    counter[riven_id] +=1
                    today_keyword_info.setdefault(item['url_id'], {**item, })
                    success_message = f"Successfully added {item['url_id']} to today_keyword_info."
                    print(success_message)
            else:
                 counter[riven_id] = 0
                 today_keyword_info.setdefault(item['url_id'], {**item, })
        today_keyword_info = list(today_keyword_info.values())
        #print(today_keyword_info)

        return today_keyword_info

    except Exception as e:
        print(e, "WM市场链接不通")
    return today_keyword_info_tmp

#获取到的关键字仓库信息插入到数据库
def keyword_insert_into_sqlite3(data):
    conn = sqlite3.connect('data.db')
    print("keyword_insert_into_sqlite3 函数 打开数据库成功！")
    print(data)
    cur = conn.cursor()
    for i in range(len(data)):
        try:
            url_id = data[i]['url_id']
            translated_attributes_str = json.dumps(data[i]['translated_attributes'])
            print(translated_attributes_str)
            cur.execute("INSERT INTO keyword_monitor (url_id,weapon_url_name,translated_weapon_url_name,riven_name,translated_attributes,buyout_price,starting_price,ingame_name,created) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(url_id, data[i]['weapon_url_name'], data[i]['translated_weapon_url_name'], data[i]['riven_name'], translated_attributes_str, data[i]['buyout_price'], data[i]['starting_price'], data[i]['ingame_name'], data[i]['created']))
            print("keyword_insert_into_sqlite3 函数: 紫卡id:{}插入数据成功！".format(url_id))
        except Exception as e:
            print("keyword_insert_into_sqlite3 error {}".format(e))
            pass
    conn.commit()
    conn.close()
#查询数据库里是否存在该关键字仓库的方法
def query_keyword_info_database(url_id):
    conn = sqlite3.connect('data.db')
    cur = conn.cursor()
    sql_grammar = "SELECT url_id FROM keyword_monitor WHERE url_id = '{}';".format(url_id)
    cursor = cur.execute(sql_grammar)
    return len(list(cursor))

#获取不存在数据库里的关键字信息
def get_today_keyword_info(today_keyword_info_data):
    today_all_keyword_info = []
    for i in range(len(today_keyword_info_data)):
        try:
            today_keyword_name = today_keyword_info_data[i]['url_id']
            today_url_id = re.findall(today_keyword_name, today_keyword_info_data[i]['url_id'].upper())
            
            if len(today_url_id) == 1: 
                pass
            Verify = query_keyword_info_database(today_url_id)
            if Verify == 0:
                print("[+] 数据库里不存在{}".format(today_url_id))
                today_all_keyword_info.append(today_keyword_info_data[i])
            else:
                print("[-] 数据库里存在{}".format(today_url_id))
        except Exception as e:
            pass
    return today_all_keyword_info

#读取本地链接文件转换成list
def load_tools_list():
    with open('tools_list.yaml', 'r',  encoding='utf-8') as f:
        list = yaml.load(f,Loader=yaml.FullLoader)
        return list['tools_list'], list['keyword_list'], list['user_list']
# 钉钉
def dingding(text, msg,webhook,secretKey):
    ding = cb.DingtalkChatbot(webhook, secret=secretKey)
    ding.send_text(msg='{}\r\n{}'.format(text, msg), is_at_all=False)


#发送信息到社交工具
def sendKeywordNews(data):
    try:
        text = '有新的紫卡监控 - 送达! \r\n** 请查收!!! **'
        # 获取 紫卡 信息
        for i in range(len(data)):
            try:
                url_id =  data[i]['url_id']
                body = (
                "武器名称: " + str(data[i]['translated_weapon_url_name']) + "-" + str(data[i]['riven_name']) + "\r\n"
                + "紫卡词条: " + "\r\n" + str(data[i]['translated_attributes']) + "\r\n"
                + "起标价格: " + str(data[i]['starting_price']) + "\r\n"
                + "买断价格: " + str(data[i]['buyout_price']) + "\r\n"
                + "上架时间: " + str(data[i]['created']) + "\r\n"
                + "WM地址: " + "https://warframe.market/zh-hans/auction/" + url_id + "\r\n"
                + "游戏内对话: /w " + str(data[i]['ingame_name']) + " hi,i want to buy " + str(data[i]['weapon_url_name']) + "-" + str(data[i]['riven_name']) + "\r\n"
                )
                if load_config()[0] == "dingding":
                    dingding(text, body, load_config()[2], load_config()[3])
                    print("钉钉 发送 紫卡 成功")
                if load_config()[0] == "feishu":
                    feishu(text, body, load_config()[2])
                    print("飞书 发送 紫卡 成功")
                if load_config()[0] == "server":
                    server(text, body, load_config()[2])
                    print("server酱 发送 紫卡 成功")
                if load_config()[0] == "pushplus":
                    pushplus(text, body, load_config()[2])
                    print("pushplus 发送 紫卡 成功")                    
                if load_config()[0] == "tgbot":
                    tgbot(text, body, load_config()[2], load_config()[3])
                    print("tgbot 发送 紫卡 成功")
            except IndexError:
                pass
    except Exception as e:
        print("sendKeywordNews 函数 error:{}".format(e))

#main函数
if __name__ == '__main__':
    print("WM市场紫卡 监控中 ...")
    #初始化部分
    create_database()
    
    while True:
        # 判断是否达到设定时间
        now = datetime.datetime.now()
        # 到达设定时间，结束内循环
        if now.hour == 23 and now.minute > 50:
            counter = {}    # 每天初始化黑名单

        tools_list, keyword_list, user_list = load_tools_list()


        print("\r\n\t\t  关键字监控 \t\t\r\n")
        # 关键字监控 , 最好不要太多关键字，防止 WM市场 次要速率限制  
        for keyword in keyword_list:
            time.sleep(5)  # 每个关键字停 5s ，防止关键字过多导致速率限制

            keyword_data = getKeywordNews(keyword)
            if len(keyword_data) > 0:
                today_keyword_data = get_today_keyword_info(keyword_data)
                sendKeywordNews(today_keyword_data)
                keyword_insert_into_sqlite3(today_keyword_data)
