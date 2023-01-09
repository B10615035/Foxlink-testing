from datetime import datetime, timedelta
import threading
import time
import random
from pymysql import NULL
from app.services.api import login, logout, mission_action, set_shift_time
from app.services.log import create_log
from pymysql import NULL
from app.env import MQTT_BROKER, MQTT_PORT, SCENARIO, RESPONSE_START, RESPONSE_END
from paho.mqtt import client as mqtt_client
from datetime import datetime
import time
import json
import logging
from multiprocessing import Process
import asyncio
logging.basicConfig(level=logging.INFO)
logger = None

# class WorkerThread(threading.Thread):


def on_subscribe(client, userdata, flags, rc):
    global username

    logger.warning(f"client subscribe = {username}")

    create_log(
        param={
            'mission_id': NULL,
            'mqtt': '',
            'username': username,
            'action': "mqtt:subscribe",
            'description': f'status:{rc}',
            'mqtt_detail': f'{userdata}',
            'time': datetime.utcnow()
        }
    )


def on_message(client, userdata, msg):
    global topic_results, is_connect
    duplicate = False
    info = msg.payload.decode()
    topic = msg.topic
    retain = msg.retain
    mission_id = json.loads(info)['mission_id']

    logger.warn(f"on_message:{username} {mission_id} {retain}")

    if (
        retain or
        (
            topic in topic_results and
            len(topic_results[topic]) > 0 and
            mission_id == topic_results[topic][-1]
        )
    ):
        duplicate = True
    else:
        topic_results[topic].append(mission_id)

    create_log(
        param={
            'mission_id': mission_id,
            'mqtt': topic,
            'username': username,
            'action': "mqtt:receive",
            'description': f"retain: {retain}, duplicate: {duplicate}",
            'mqtt_detail': f"{topic_results} userdata:{userdata}\n, msg:{msg}",
            'time': datetime.utcnow()
        }
    )


def on_connect(c, userdata, flags, rc):
    global is_connect, username, topic_results, client
    if (rc == 0):
        logger.info(f"Connection successful: Broker")
        if(len(topic_results)>0):
            while True:
                try:
                    for topic in [ old for old in topic_results.keys()]:
                        client.subscribe(topic, 2)
                except:
                    continue
                else:
                    break

        is_connect = True
    elif (rc == 1):
        logger.warn("Connection refused - incorrect protocol version")
    elif (rc == 2):
        logger.warn("Connection refused - invalid client identifier")
    elif (rc == 3):
        logger.warn("Connection refused - server unavailable")
    elif (rc == 4):
        logger.warn("Connection refused - bad username or password")
    elif (rc == 5):
        logger.warn("Connection refused - not authorised")
    else:
        logger.error("Connection refused - unknown error.")

    create_log(
        param={
            'mission_id': NULL,
            'mqtt': "",
            'username': username,
            'action': "mqtt:connect",
            'description': f'{"success" if rc == 0 else "failed" }. status:{rc}',
            'mqtt_detail': f"{userdata}",
            'time': datetime.utcnow()
        }
    )


def on_disconnect(client, userdata, rc):
    global topic_results, is_connect
    if rc == 0:
        logger.info("Disconnect successful")
    else:
        logger.error("Disconnect - unknown error.")
    create_log(
        param={
            'mission_id': NULL,
            'mqtt': "",
            'username': username,
            'action': "mqtt:disconnect",
            'description': f'{"success" if rc == 0 else "failed" }. status:{rc}',
            'mqtt_detail': f"{userdata}",
            'time': datetime.utcnow()
        }
    )
    is_connect = False


def register_topic(topic):
    #可能是利用mqtt 從client端發送任務?
    global client, topic_results, is_connect
    logger.info(f"{topic} registered")
    topic_results[topic] = []
    #
    client.subscribe(topic, 2)
    create_log(
        param={
            'mission_id': NULL,
            'mqtt': "",
            'username': username,
            'action': "subscribe",
            'description': f'@{topic}',
            'mqtt_detail': "",
            'time': datetime.utcnow()
        }
    )


def mqtt_get(action, topic):
    global client, topic_results, is_connect
    #如果沒連線 休息1秒
    while (not is_connect):
        # logger.info(f"for action:{action} waiting for mqtt to connect({is_connect})....")
        time.sleep(1)
    #topic result 不知道是啥 但選擇的topic沒在list裡 就進行註冊
    if (not topic in topic_results.keys()):
        register_topic(topic)
    #宣告
    result = None
    #test8 付職
    if SCENARIO == "test8":
        if len(topic_results[topic]):
            result = topic_results[topic][0]
    else:
        while (len(topic_results[topic]) == 0):
            # logger.info(f"waiting for mqtt message with action:{action}")
            time.sleep(3)

        # result = topic_results[topic].pop(0)
        result = topic_results[topic][0]
    #產生mission log
    if result:
        create_log(
            param={
                'mission_id': result,
                'mqtt': f'{topic}',
                'username': username,
                'action': action,
                'description': f'get from mqtt.',
                'mqtt_detail': f'',
                'time': datetime.utcnow()
            }
        )

    return result


def mqtt_sync(status, topic):
    #刪除完成的topic
    global topic_results
    if (status and status >= 200 and status <= 299):
        topic_results[topic].pop(0)


client = None
topic_results = {}
is_connect = False
username = "Unspecified"
#
def take_action(action, mission_id, topic):
    global token, username, topic_results
    time.sleep(get_response_time())
    fail_count = 0
    while True:
        is_success, fail_count = get_status_info(mission_action(token, mission_id, action, username), fail_count)
        if is_success:
            if  action in ["reject", "finish"] or (topic.find('move-rescue-station') != -1 and action == 'start'):
                topic_results[topic].pop(0)
            break
        else:
            time.sleep(2)
#取得response_code
def get_status_info(status, fail_count):
    if status and status >= 200 and status <= 299:
        return True, 0
    
    elif status and status >= 400 and status <= 499:
        fail_count += 1
        if fail_count == 5:
            return True, fail_count

    return False, fail_count
#用於判斷故障
#90%機率接受
#95%拒絕
#91-94 顯示無反應
def get_action():
    r = random.randint(1, 100)
    #隨機數
    if r <= 90:
        return "accept"

    if r <= 95:
        return "reject"
    
    return None
#取得反應時間
def get_response_time():
    return random.randint(RESPONSE_START, RESPONSE_END)

#計算日夜班
def get_shift_type():
    if datetime.utcnow().hour % 2 == 0:
        return 0
    return 1

#更新日夜班
def update_shift(current_shift_type):
    hour = (datetime.utcnow() + timedelta(hours=8)).hour
    
    if current_shift_type != get_shift_type():
        time1 = f'{(hour+1)%24}:00:00'
        time2 = f'{hour%24}:00:00'
        
        set_shift_time(current_shift_type, time1, time2)
        current_shift_type = get_shift_type()
        set_shift_time(current_shift_type, time2, time1)

    return current_shift_type
#確定user狀態
def check_user_status(current_shift_type, worker_shift_type, worker_uuid):
    global token, username
    timeout = 30
    #確認現在選擇是日班還是夜班
    current_shift_type = update_shift(current_shift_type)
    #沒有token 代表沒登入
    if not token and  current_shift_type == worker_shift_type:
        while True:
            #登入獲得token
            status, token = login(username, worker_uuid, timeout)
            #回傳正確
            if status and status >= 200 and status < 299:
                break
    #如果有token 但 不是他的上班時間
    if token and current_shift_type != worker_shift_type:
        fail_count = 0
        while True:
            #進行登出的動作
            is_success, fail_count = get_status_info(logout(token, username, timeout=timeout), fail_count)
            if is_success:
                #token 清空
                token = None
                break
            
    return current_shift_type
    
def worker(_username, _behavier, _id, speed=1):
    
    # if (not _username == "C0001"):
    #     return
    global client, topic_results, is_connect, username, logger, token

    logger = logging.getLogger(_username)
    logger.addHandler(logging.FileHandler(f'logs/{_username}.log', mode="w"))
    username = _username
    behavier = _behavier
    mission_id = 0
    worker_uuid = _id + 10000

    token = None
    try:
        ##### Start MQTT Client ######
        client = mqtt_client.Client(f"{username}#{worker_uuid}", clean_session=False)
        client.on_message = on_message
        client.on_subscribe = on_subscribe
        client.on_disconnect = on_disconnect
        client.on_connect = on_connect
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=10)
        client.loop_start()
        #隨機產生故障
        register_topic(f'foxlink/users/{worker_uuid}/move-rescue-station')
        register_topic(f'foxlink/users/{worker_uuid}/missions')
        #這裡是test8 開始
        if SCENARIO == "test8":
            #選擇日班或夜班
            current_shift_type = (get_shift_type() + 1) % 2
            while True:
                current_shift_type = check_user_status(current_shift_type, worker_shift_type=behavier[0]['api'], worker_uuid=worker_uuid)
                #員工動作 接受or拒絕
                action = get_action()
                #路徑不明 @!@!
                topic = f'foxlink/users/{worker_uuid}/missions'
                #創建任務
                mission_id = mqtt_get(action, topic)
                #有mission id 執行 接受->開始->結束
                if mission_id:
                    if action == "accept":
                        take_action("accept", mission_id, topic)
                        take_action("start", mission_id, topic)
                        take_action("finish", mission_id, topic)
                    #拒絕
                    elif action == "reject":
                        take_action("reject", mission_id, topic)
                    else:
                    #action 不等於上述幾種 標記無動作
                        create_log(
                            param = {
                                'mission_id': mission_id,
                                'mqtt': topic,
                                'username': username,
                                'action': 'no_action',
                                'description': f'',
                                'mqtt_detail': '',
                                'time': datetime.utcnow(),
                            }
                        )
                #topic還是不知道是什麼 mqtt相關內容?
                #這裡又做一次和上面一樣內容
                topic = f'foxlink/users/{worker_uuid}/move-rescue-station'
                action = "start"
                mission_id = mqtt_get(action, topic)
                if mission_id:
                    take_action(action, mission_id, topic)
                #暫停10秒
                time.sleep(10)
        else:
            i = 0
            fetch = True
            fail_count = 0
            while i < len(behavier):
                #behavier是json檔中 test8.json的資料
                status = None
                #取得動作
                action = behavier[i]['api']
                #反應時間
                response_time = behavier[i]['response_time']
                #timeout時間
                timeout = 30  # seconds
                #logger顯示 debug用
                logger.info(f"action:{action} begin to with timeout({timeout})")
                #暫停數秒
                time.sleep(float(response_time) / speed)
                #action 登入
                if action == 'login':
                    status, token = login(username, worker_uuid, timeout)
                #action 登出
                elif action == 'logout':
                    status = logout(token, username, timeout=timeout)
                #action 接受或拒絕
                elif action in ['accept', 'reject']:
                    topic = f'foxlink/users/{worker_uuid}/missions'
                    mission_id = mqtt_get(action, topic)
                    #回傳是否成功 (status code)
                    status = mission_action( # path:app/service/api.py
                        token,
                        mission_id,
                        action,
                        username,
                        timeout=timeout
                    )
                    #
                    mqtt_sync(status, topic)
                #action開始或 api是結束
                elif action == 'start' and behavier[i - 1]['api'] == 'finish':
                    topic = f'foxlink/users/{worker_uuid}/move-rescue-station'
                    mission_id = mqtt_get(action, topic)
                    status = mission_action(
                        token,
                        mission_id,
                        action,
                        username,
                        timeout=timeout
                    )
                    #將完成的topic利用刪除pop
                    mqtt_sync(status, topic)
                #action 是開始或結束
                elif action in ['start', 'finish']:
                    status = mission_action(token, mission_id, action, username, timeout=timeout)

                logger.info(f"ended {action} with status:{status}")
                
                # is_success, fail_count = get_status_info(status, fail_count, action)
                # is_success = True
                # if is_success:
                #     logger.info(f"action:{action} completed.")
                #     i += 1
                #如果status在200-299內 代表回傳成功code
                #j應該是用於check錯誤 超過10次 回傳錯誤log 
                if status and 200 <= status and status <= 299:
                    logger.info(f"action:{action} completed.")
                    i += 1
                    if action == "finish" and j > 10:
                        mqtt_sync(200, f'foxlink/users/{worker_uuid}/missions')
                    #有成功將j改為0
                    j = 0
                elif (status and 400 <= status <= 499):
                    logger.warning(f"{username} skipping for error exceed")
                    if (j > 10):
                        i += 1
                        create_log(
                            param={
                                'mission_id': NULL,
                                'mqtt': '',
                                'username': username,
                                'action': action,
                                'description': f'skipping for error exceed',
                                'mqtt_detail': f'',
                                'time': datetime.utcnow()
                            }
                        )
                    else:
                        j += 1

                time.sleep(1)

        logger.info("completed all tasks, leaving")

        client.disconnect()
    except Exception as e:
        logger.error(f"encountered exception: {repr(e)}")

    return
