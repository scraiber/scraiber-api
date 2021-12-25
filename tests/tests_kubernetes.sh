#source .env.test
kind create cluster --name testing

docker-compose down
docker volume rm $(docker volume ls -q)
docker-compose up -d --build
#pytest 
#docker-compose exec test pytest
#cd ..
sleep 5;
pytest --envfile .env.test
#TEST_PORT="localhost" TEST_HOST="8002" SENDINBLUE_API_KEY=$SENDINBLUE_API_KEY CLUSTER_DICT=$CLUSTER_DICT pytest