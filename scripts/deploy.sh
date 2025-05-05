# !/bin/bash

# docker가 없다면, docker 설치
if ! type docker > /dev/null
then
  echo "docker does not exist"
  echo "Start installing docker"
  sudo apt-get update
  sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
  sudo apt update
  apt-cache policy docker-ce
  sudo apt install -y docker-ce
fi

# docker-compose가 없다면 docker-compose 설치
if ! type docker-compose > /dev/null
then
  echo "docker-compose does not exist"
  echo "Start installing docker-compose"
  sudo curl -L "https://github.com/docker/compose/releases/download/1.27.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
fi

echo "Stopping and removing existing containers: ubuntu"
sudo docker-compose -f /home/ubuntu/srv/ubuntu/docker-compose.prod.yaml down

# SSL 인증서 설정
echo "Setting up SSL certificates"
if ! command -v certbot &> /dev/null; then
  echo "Installing certbot"
  sudo apt-get update
  sudo apt-get install -y certbot
fi

# Check if certificate exists
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  echo "Requesting new SSL certificate"
  # Request new certificate
  sudo certbot certonly --standalone -d $DOMAIN --agree-tos --email $EMAIL --non-interactive
fi

echo "start docker-compose up: ubuntu"
sudo docker-compose -f /home/ubuntu/srv/ubuntu/docker-compose.prod.yaml up --build -d

# 컨테이너 상태 확인
echo "Checking container status..."
sleep 10  # 컨테이너가 시작될 때까지 잠시 대기
sudo docker ps -a

# 실패한 컨테이너가 있다면 로그 확인
echo "Checking container logs..."
for container in $(sudo docker ps -a --format "{{.Names}}"); do
  echo "=== Logs for $container ==="
  sudo docker logs $container
  echo "=========================="
done

# nginx 컨테이너가 실패했다면 재시작
if ! sudo docker ps | grep -q "nginx"; then
  echo "Nginx container failed to start. Retrying..."
  # SSL 인증서 확인
  echo "Checking SSL certificates..."
  ls -la /etc/letsencrypt/live/$DOMAIN/

  # nginx 컨테이너만 재시작
  sudo docker-compose -f /home/ubuntu/srv/ubuntu/docker-compose.prod.yaml up -d --build nginx
  sleep 5
  sudo docker logs nginx
fi
