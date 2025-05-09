FROM python:3.10-slim

WORKDIR /app

# Define build arguments
ARG OPENAI_API_KEY
ARG OPENAI_MODEL=gpt-3.5-turbo
ARG ADMIN_REGISTRATION_SECRET=admin123

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV OPENAI_MODEL=${OPENAI_MODEL}
ENV ADMIN_REGISTRATION_SECRET=${ADMIN_REGISTRATION_SECRET}

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
