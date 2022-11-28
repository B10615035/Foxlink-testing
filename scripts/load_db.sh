bash scripts/server_exec.sh \
"sed -i 's/image: mysql-test.*/image: mysql-$1/' docker-compose.yml"
sleep 5