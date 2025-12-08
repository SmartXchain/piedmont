# pull official base image
FROM python:3.12-slim

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# WeasyPrint native deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    graphviz \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    fonts-dejavu \
    shared-mime-info \
    netcat-traditional \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# copy entrypoint.sh
COPY entrypoint.sh .
RUN sed -i 's/\r$//g' entrypoint.sh && chmod +x entrypoint.sh

# copy project
COPY . .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
