. scripts/testings/envs.sh

SHIFT_TIME_T1="$(date --date='-1 minutes' +'%Y-%m-%d %H:%M:%S')"

SHIFT_TIME_T2="$(date --date='+1 minutes' +'%Y-%m-%d %H:%M:%S')"

python -m app.update_shift_time "$SHIFT_TIME_T1" "$SHIFT_TIME_T2"