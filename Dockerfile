FROM python:3.10-slim

WORKDIR /app

# Instala dependências do sistema necessárias para o XGBoost (se houver)
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando para rodar o pipeline
CMD ["python", "main.py"]
