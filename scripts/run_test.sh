SCENARIO=$1
echo "Running Scenario: $1"
. scripts/load_env.sh
bash scripts/init_env.sh
bash scripts/load_db.sh $1
bash scripts/restart_servers.sh
# python -m app.worker "testLogin_single"
python -m app.utils.create_time -f $1
# python -m app.foxlinkevent $1
python -m app.worker $1