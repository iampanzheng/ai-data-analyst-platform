FROM python:3.13-slim

WORKDIR /app
ENV HOME=/home/appuser

RUN pip install --no-cache-dir psycopg[binary]==3.2.6 \
    && mkdir -p /home/appuser /data \
    && chown -R 10001:10001 /app /home/appuser /data

COPY --chown=10001:10001 etl/load_to_postgres.py /app/load_to_postgres.py
COPY --chown=10001:10001 data/raw/census/city_population_sample.csv /data/city_population_sample.csv
COPY --chown=10001:10001 data/raw/acs/acs_2024_city_profile_sample.csv /data/acs_2024_city_profile_sample.csv
COPY --chown=10001:10001 data/raw/bls/oews_2023_software_developers_metro_sample.csv /data/oews_2023_software_developers_metro_sample.csv

USER 10001:10001

CMD ["python", "/app/load_to_postgres.py"]
