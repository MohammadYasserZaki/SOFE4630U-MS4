FROM python:3.9
RUN pip install google-cloud-pubsub
COPY *.json ./
COPY main.py ./
CMD python -u ./main.py
