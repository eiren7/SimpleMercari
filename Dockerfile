FROM python:3.11.3-slim-buster

WORKDIR /app

COPY python/requirements.txt python/requirements.txt

RUN pip3 install -r python/requirements.txt

COPY python  /app/python

COPY db/mercari.sqlite3 db/mercari.sqlite3

EXPOSE 9000

CMD ["uvicorn", "python.main:app", "--host", "0.0.0.0", "--port", "9000"]