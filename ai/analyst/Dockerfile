FROM python:3.13-slim

WORKDIR /app
ENV PYTHONPATH=/app \
    HOME=/home/appuser

COPY ai/analyst/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && mkdir -p /home/appuser \
    && chown -R 10001:10001 /app /home/appuser

COPY --chown=10001:10001 ai /app/ai
COPY --chown=10001:10001 evaluation /app/evaluation
COPY --chown=10001:10001 acceptance /app/acceptance
COPY --chown=10001:10001 data /app/data
COPY --chown=10001:10001 tests /app/tests
COPY --chown=10001:10001 pytest.ini /app/pytest.ini

USER 10001:10001

CMD ["uvicorn", "ai.analyst.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
