FROM python:3.7-alpine
MAINTAINER PUDE_TECH

RUN echo http://mirrors.aliyun.com/alpine/v3.9/main > /etc/apk/repositories
RUN echo http://mirrors.aliyun.com/alpine/v3.9/community >> /etc/apk/repositories
RUN apk update
RUN apk --update add --no-cache gcc
RUN apk --update add --no-cache g++
RUN apk --update add --no-cache tzdata
RUN apk --update add --no-cache libffi-dev
RUN apk --update add --no-cache libxslt-dev
RUN apk --update add --no-cache jpeg-dev
RUN apk --update add --no-cache vim

RUN apk add --update nginx && rm -rf /var/cache/apk/*

ENV  TIME_ZONE Asia/Shanghai
ENV PIPURL "https://mirrors.aliyun.com/pypi/simple"

RUN echo "${TIME_ZONE}" > /etc/timezone
RUN ln -sf /usr/share/zoneinfo/${TIME_ZONE} /etc/localtime

WORKDIR /logs
WORKDIR /back_server

COPY . .

COPY ./run_docker.sh .
COPY ./ngcors.conf /etc/nginx/conf.d/ngcors.conf
RUN ["chmod", "+x", "./run_docker.sh"]


RUN pip --no-cache-dir install  -i ${PIPURL} --upgrade pip
RUN pip --no-cache-dir install  -i ${PIPURL} -r requirements.txt


# RUN python -m http.server 8001
RUN mkdir /run/nginx
RUN cd /run/nginx
RUN touch nginx.pid

CMD [ "./run_docker.sh" ]

