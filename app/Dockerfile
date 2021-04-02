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
RUN apk add --no-cache mariadb-dev build-base
RUN apk add --no-cache g++ freetype-dev jpeg-dev

ENV  TIME_ZONE Asia/Shanghai
ENV PIPURL "https://pypi.tuna.tsinghua.edu.cn/simple"

RUN echo "${TIME_ZONE}" > /etc/timezone
RUN ln -sf /usr/share/zoneinfo/${TIME_ZONE} /etc/localtime

WORKDIR webapps

COPY . .
COPY run.sh .
RUN ["chmod", "+x", "./run.sh"]
RUN ls
RUN pip --no-cache-dir install -i ${PIPURL} --upgrade pip
RUN pip --no-cache-dir install -i ${PIPURL} -r requirements.txt

# CMD ./run.sh
CMD python -m http.server 8080