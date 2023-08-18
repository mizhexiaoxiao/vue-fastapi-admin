FROM node:18.8.0-alpine3.16 as web

WORKDIR /opt/vue-fastapi-admin
COPY /web ./web
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories \
    && cd /opt/vue-fastapi-admin/web && npm i -g pnpm --registry=https://registry.npmmirror.com \
    && pnpm i && pnpm run build


FROM python:3.11-slim

WORKDIR /opt/vue-fastapi-admin
ADD . .
COPY /deploy/entrypoint.sh .

RUN sed -i s@/deb.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list.d/debian.sources \
    && sed -i s@/security.debian.org/@/mirrors.aliyun.com/@g /etc/apt/sources.list.d/debian.sources

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev bash nginx vim curl procps net-tools\
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN pip install poetry -i https://pypi.tuna.tsinghua.edu.cn/simple\
    && poetry config virtualenvs.create false \
    && poetry install

COPY --from=web /opt/vue-fastapi-admin/web/dist /opt/vue-fastapi-admin/web/dist
ADD /deploy/web.conf /etc/nginx/sites-available/web.conf
RUN rm -f /etc/nginx/sites-enabled/default \ 
    && ln -s /etc/nginx/sites-available/web.conf /etc/nginx/sites-enabled/ 

ENV LANG=zh_CN.UTF-8
EXPOSE 80

ENTRYPOINT [ "sh", "entrypoint.sh" ]