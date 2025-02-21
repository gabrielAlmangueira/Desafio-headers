FROM python:3.12-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo de dependências e instala-os
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os arquivos da aplicação para o container
COPY . .

# Expõe a porta usada pela aplicação (padrão Flask: 5000)
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "app.py"]