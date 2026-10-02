FROM python:3.13-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY ai/analyst/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ai /app/ai
COPY evaluation /app/evaluation
COPY data /app/data
COPY tests /app/tests
COPY pytest.ini /app/pytest.ini

CMD ["uvicorn", "ai.analyst.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
