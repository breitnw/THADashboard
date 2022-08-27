FROM python:3.8.10

WORKDIR /var/www/
COPY . /var/www/

RUN pip install --upgrade pip
RUN apt-get update
#RUN apt-get -y install libsasl2-dev libldap2-dev libssl-dev
RUN pip install -r requirements.txt

#RUN addgroup -gid $GROUP_ID www
#RUN adduser --disabled-password --uid $USER_ID --gid $GROUP_ID www --shell /bin/sh

USER www
EXPOSE 5000

#CMD [ "gunicorn", "--config", "gunicorn-cfg.py", "run:app"]
CMD [ "python3", "__init__.py" ]
