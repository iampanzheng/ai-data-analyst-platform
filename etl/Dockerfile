FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir psycopg[binary]==3.2.6
COPY etl/load_to_postgres.py /app/load_to_postgres.py
COPY data/raw/census/city_population_sample.csv /data/city_population_sample.csv
COPY data/raw/acs/acs_2024_city_profile_sample.csv /data/acs_2024_city_profile_sample.csv
COPY data/raw/bls/oews_2023_software_developers_metro_sample.csv /data/oews_2023_software_developers_metro_sample.csv
CMD ["python", "/app/load_to_postgres.py"]
