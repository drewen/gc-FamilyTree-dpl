FROM python:2.7
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y sqlite3 libsqlite3-dev
COPY . /var/www/familytree
WORKDIR /var/www/familytree
RUN pip install -r requirements.txt
RUN mkdir /db

EXPOSE 8051
