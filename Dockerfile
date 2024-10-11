
FROM python:3.10


WORKDIR /app


COPY requirements.txt ./


RUN pip install --no-cache-dir -r requirements.txt


COPY . .


RUN chmod 755 ./uploaded_images && \
    chown -R nobody:nogroup ./uploaded_images && \
    chmod 755 ./static && \
    chown -R nobody:nogroup ./static


EXPOSE 5000


CMD ["python3", "api.py"]

