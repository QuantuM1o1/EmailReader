FROM python:3.11
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
ENV NAME World
CMD ["python", "emailReader.py"]