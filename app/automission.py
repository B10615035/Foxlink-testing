import pandas as pd
from app.utils.queryDB import query_server, query_testing
from app.services.mission_thread import MissionThread

def get_device():
    #選擇所有device 但不包含 rescue(救援站)
    sql = f"""SELECT project, line, device_name from testing_api.devices d WHERE workshop = 1 and project != 'rescue'"""
    data = query_server(sql)
    
    device = pd.DataFrame(data)
    device.rename(columns={0:'project', 1:'line', 2:'device_name'}, inplace=True)

    return device


if __name__ == '__main__':
    device = get_device()
    THREAD_NUMBER = len(device)
    mission_thread = []
    # device總數 91台機檯隨機產生故障
    for i in range(THREAD_NUMBER):
        print(device['project'][i], device['line'][i], device['device_name'][i])
        # 用devices數量來產生thread
        mission_thread.append(MissionThread(device['project'][i], device['line'][i], device['device_name'][i]))
        mission_thread[i].start()
    # 依序完成
    for i in range(THREAD_NUMBER):
        mission_thread[i].join()