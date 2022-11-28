TIME_H_M="$(date --date='5 minute' +'%H:%M')"
ssh ntust-foxlink@140.118.157.9 -p 7869 "cd $FOXLINK_DIR; \
sed -i 's/DAY_SHIFT_END=.*/DAY_SHIFT_END=$TIME_H_M/' ntust.env; \ 
$1;"