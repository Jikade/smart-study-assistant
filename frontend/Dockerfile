FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY . /usr/share/nginx/html

COPY config.docker.js /usr/share/nginx/html/config.js

EXPOSE 80

HEALTHCHECK \
  --interval=10s \
  --timeout=5s \
  --retries=10 \
  CMD wget -q --spider http://127.0.0.1/ || exit 1