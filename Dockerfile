FROM python:3.8.10

ARG USER_ID=1000
ARG GROUP_ID=1000

WORKDIR /var/www/
COPY requirements.txt /var/www/

RUN pip install --upgrade pip
RUN apt-get update
RUN pip install -r requirements.txt

RUN addgroup --gid $GROUP_ID www
RUN adduser --disabled-password --uid $USER_ID --gid $GROUP_ID www --shell /bin/sh

COPY app /var/www/app
COPY gunicorn.sh /var/www/

RUN chown -R $USER_ID:$GROUP_ID /var/www/

USER www
EXPOSE 5000

#CMD [ "flask", "run", "--host", "0.0.0.0"]
ENTRYPOINT ["./gunicorn.sh"]