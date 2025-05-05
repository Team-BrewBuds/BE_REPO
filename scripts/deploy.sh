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

  # Create ssl directory if it doesn't exist
  sudo mkdir -p /home/ubuntu/srv/ubuntu/ssl/live/$DOMAIN
  sudo mkdir -p /home/ubuntu/srv/ubuntu/ssl/archive/$DOMAIN

  # Copy certificates
  sudo cp /etc/letsencrypt/live/$DOMAIN/* /home/ubuntu/srv/ubuntu/ssl/live/$DOMAIN/
  sudo cp /etc/letsencrypt/archive/$DOMAIN/* /home/ubuntu/srv/ubuntu/ssl/archive/$DOMAIN/

  # Set proper permissions
  sudo chown -R ubuntu:ubuntu /home/ubuntu/srv/ubuntu/ssl
fi

echo "start docker-compose up: ubuntu"
sudo docker-compose -f /home/ubuntu/srv/ubuntu/docker-compose.prod.yaml up --build -d
