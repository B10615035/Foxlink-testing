import threading, time, random, logging
from datetime import datetime
from app.utils.query_db import query_local, query_server
from pymysql import NULL
from app.env import REPAIR_START, REPAIR_END

class MissionThread(threading.Thread):
    def __init__(self, project , line , device_name):
        threading.Thread.__init__(self)
        self.project = project
        self.line = line
        self.device_name = device_name

    def get_thread_number(self):
        r = random.randint(1,10)
        if r < 10:
            return 1

        return random.randint(2, 5)

    def run(self):

        while True:
            event_thread = []
            wait_repair = False
            thread_number = self.get_thread_number()

            if thread_number == 1:
                wait_repair = True

            for i in range(thread_number):
                event_thread.append(EventThread(i, self.project, self.line, self.device_name, wait_repair))
                event_thread[i].start()
            
            for i in range(thread_number):
                event_thread[i].join()


class EventThread(threading.Thread):
    def __init__(self, event_id, project , line , device_name, wait_repair):
        threading.Thread.__init__(self)
        self.event_id = event_id
        self.project = project
        self.line = line
        self.device_name = device_name
        self.wait_repair = wait_repair

    def get_repair_time(slef):
        return random.randint(REPAIR_START, REPAIR_END)

    def run(self):
        repair_time = self.get_repair_time()
            
        sql = """INSERT INTO foxlink.foxlinkevents (line, device_name, category, start_time, end_time, message, start_file_name, end_file_name, project, event_id)
                VALUES ('{}','{}',{},'{}',{},'{}',{},{},'{}',{})""".format(self.line, self.device_name, 192, datetime.now(), NULL, '2#插针站故障', NULL, NULL, self.project, self.event_id)
        query_local(sql)
        logging.warning(sql)

        if self.wait_repair:
            for _ in range(50):
                sql = f"""SELECT id FROM foxlink.missions m  WHERE device='{self.project}@{self.line}@{self.device_name}' AND repair_start_date IS NOT NULL AND repair_end_date IS NULL AND is_cancel = 0"""
                data = query_server(sql)
                if len(data) != 0:
                    logging.warning(sql)
                    break
                time.sleep(5)

        time.sleep(repair_time)

        sql = f"""UPDATE foxlink.foxlinkevents SET end_time='{datetime.now()}'  WHERE line='{self.line}' AND project='{self.project}' AND device_name='{self.device_name}' AND event_id={self.event_id} AND end_time IS NULL"""
        query_local(sql)
        logging.warning(sql)
