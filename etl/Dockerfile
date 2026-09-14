FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir psycopg[binary]==3.2.6
COPY etl/load_to_postgres.py /app/load_to_postgres.py
COPY data/raw/census/city_population_sample.csv /data/city_population_sample.csv
CMD ["python", "/app/load_to_postgres.py"]
