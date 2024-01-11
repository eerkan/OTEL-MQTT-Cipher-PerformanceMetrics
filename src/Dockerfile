FROM python:3.12.1
COPY requirements.txt /opt/app/requirements.txt
WORKDIR /opt/app
RUN pip install --no-cache-dir -r requirements.txt
COPY . /opt/app
CMD ["python", "-u", "main.py"]
