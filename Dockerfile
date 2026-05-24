# Usa a imagem oficial do Playwright com Python que já vem com os navegadores instalados
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Define a pasta de trabalho
WORKDIR /app

# Instala fuso horário para suportar America/Sao_Paulo sem dar erro
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ="America/Sao_Paulo"
RUN apt-get update && apt-get install -y tzdata

# Copia os arquivos de configuração primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala o Gunicorn (servidor de produção para Flask) e as dependências
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Instala os navegadores do Playwright (apenas chromium)
RUN playwright install chromium

# Copia o resto do código
COPY . .

# Expõe a porta 5000 (O Render vai usar a variável de ambiente PORT, mas 5000 é padrão do Flask)
EXPOSE 5000

# Comando para iniciar o servidor web usando Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "--workers", "1", "--threads", "2", "app:app"]
