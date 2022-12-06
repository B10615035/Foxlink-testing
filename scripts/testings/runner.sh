. scripts/testings/envs.sh

# if [[ $1 == "local" ]];
# then

# reset foxlink database
bash scripts/systems/clean_server.sh db

bash scripts/systems/start_server.sh db $SCENARIO_DB_TAG

# reset mqtt server
bash scripts/systems/clean_server.sh emqx
bash scripts/systems/start_server.sh emqx

# elif [[ $1 == "remote" ]];
# then

#     # reset foxlink database
#     bash scripts/systems/clean_server.sh db
#     bash scripts/systems/start_server.sh db $SCENARIO_DB_TAG

#     # reset all remote servers (emqx, backend,api-db)
#     bash scripts/testings/restart_servers.sh

# else
#     echo "please specify the valid condition..."
#     exit 0
# fi


sleep 2
echo "Running $SCENARIO...."

if [ $SCENARIO == "test5" ];
then
    # shift time
    SHIFT_TIME_T1="$(date --date='-5 minutes' +'%Y-%m-%d %H:%M:%S')"
    SHIFT_TIME_T2="$(date --date='+5 minutes' +'%Y-%m-%d %H:%M:%S')"
    python -m app.update_shift_time "$SHIFT_TIME_T1" "$SHIFT_TIME_T2"

    # create time
    python -m app.utils.create_time -f $SCENARIO -s "$SHIFT_TIME_T2"
else

    if [ $IS_APP -eq "1" ];
    then
        echo "running app scenario"
        python -m app.CreateTime_APP
        # run test case
        python -m app.execute "${SCENARIO}_time" -n 100
    
    else
        # create time
        python -m app.utils.create_time -f $SCENARIO -b 150
        # run test case
        python -m app.execute $SCENARIO
    fi
fi

