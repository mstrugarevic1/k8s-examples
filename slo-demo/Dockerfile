FROM python:3.11-slim

# Create a non-root user
RUN useradd -m appuser
USER appuser
WORKDIR /home/appuser

# Install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser app.py .

EXPOSE 8080

CMD ["python", "app.py"]
