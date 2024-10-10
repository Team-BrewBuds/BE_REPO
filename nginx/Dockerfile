FROM nginx:1.19.0-alpine

# 기존 설정 파일 지우고
RUN rm /etc/nginx/conf.d/default.conf

# 직접 설정한 nginx.conf 파일로 기존 설정 파일 대체
COPY nginx.conf /etc/nginx/conf.d