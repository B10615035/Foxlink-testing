from datetime import datetime
from app.services.thread import   worker
import  argparse
import logging
import json
import multiprocessing
import signal

logging.basicConfig(level=logging.DEBUG)

def cleanup_childrens(*args,**_args):
    active = multiprocessing.active_children()

    for p in active:
        p.kill()

    print(f"All Childrens Killed!!!(totally:{len(active)})")

def main(create_process=False):
    signal.signal(signal.SIGINT, cleanup_childrens)
    signal.signal(signal.SIGTERM, cleanup_childrens)

    parser = argparse.ArgumentParser()
    parser.add_argument(dest='json')
    args = parser.parse_args()
    worker_behaviour = None
    thread_num = 0
    
    with open(f'./app/scenario/{args.json}.json') as jsonfile:
        config = json.load(jsonfile)
        thread_num = len(config['worker_behavier'])
        print(f"Thread Num:{thread_num} loaded")
        worker_behaviour = config['worker_behavier']

    print(f"Scenario:{args.json} loaded")
    start_time = datetime.now()

    print(f"Start at:{start_time}")
    worker_thread = []

    print(f"Creating Threads.")

    
    for i in range(thread_num):    
        worker_thread.append(
            multiprocessing.Process(
                target=worker,
                args=(
                    worker_behaviour[i]['username'],
                    worker_behaviour[i]['behavier'],
                    i
                )
            )
        )
        worker_thread[-1].start()

    print(f"Running Threads.")
    for i in range(thread_num):
        worker_thread[i].join()

    print(f"Workers Complete.")
    logging.warning("============= DONE ==============")
    logging.warning(datetime.now() - start_time)


if __name__ == '__main__':
    main()
