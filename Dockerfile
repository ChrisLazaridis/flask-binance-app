FROM python:3.11
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/
RUN python -m venv venv
SHELL ["venv/Scripts/activate"]
ENV PYTHONPATH="${PYTHONPATH}:/app"
EXPOSE 5000
CMD ["python", "website/app.py"]

