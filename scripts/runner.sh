SCENARIO="test1"
# install package
python -m pip install -r requirements.txt
# set source code folder direction
export FOXLINK_DIR="/home/ntust-foxlink/foxlink/foxlink-api-backend/"
# reset database
bash scripts/reset_db.sh
# reset mqtt server
bash scripts/restart_servers.sh
# # initialize login
# python -m app.worker "testLogin_single"
# # create time
# python -m app.utils.create_time -f $SCENARIO
# # run foxlinkevents
# python -m app.foxlinkevent $SCENARIO
# # run test case
# python -m app.worker $SCENARIO