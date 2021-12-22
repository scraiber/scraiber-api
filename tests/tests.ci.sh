echo "Setup docker-compose"
docker-compose up -d --build
docker-compose ps
echo "Run tests"
sleep 10
docker-compose exec test pytest