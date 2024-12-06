#!/usr/bin/env python3

import sys
import csv
import logging
from netmiko import ConnectHandler
import os
import shutil
from datetime import datetime
import re

# Definindo o nome fixo do arquivo CSV
csv_file = "/root/backup/scripts/cisco.csv"

# Variável para o nome do cliente
cliente = sys.argv[1]

# Verifique se o arquivo CSV existe
if not os.path.isfile(csv_file):
    print(f"Erro: o arquivo {csv_file} não foi encontrado.")
    sys.exit(1)

# Configuração do log
log_directory = f"/root/backup/{cliente}/RT/log"
os.makedirs(log_directory, exist_ok=True)  # Garantir que o diretório de log exista
log_filename = os.path.join(log_directory, 'backup_rt_cisco.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, mode='a'),  # Registra no arquivo (em modo de anexar)
        logging.StreamHandler()  # Exibe no terminal
    ]
)

# Função para processar cada linha do CSV
def process_hosts_from_csv(csv_file):
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            host = row['host']
            username = row['username']
            password = row['password']
            port = row['port']
            identificacao = row['identificacao']
            
            # Limpeza da variável de identificação
            identificacao = re.sub(r'[^a-zA-Z0-9_-]', '', identificacao)
            
            # Chamada para a função de backup
            backup_device(host, username, password, port, identificacao)

# Função para realizar o backup de cada dispositivo
def backup_device(host, username, password, port, identificacao):
    logging.info(f"Iniciando o backup para o dispositivo: {identificacao} (Host: {host})")

    # Definir os detalhes da conexão SSH
    device = {
        'device_type': 'cisco_ios',
        'host': host,
        'username': username,
        'password': password,
        'port': port,
        'secret': password,
        'verbose': True,
        'timeout': 60,
        'banner_timeout': 60
    }

    # Estabelecer a conexão SSH
    try:
        net_connect = ConnectHandler(**device)

        commands = [
            "show running-config"
        ]

        # Executar os comandos
        output = ""
        for command in commands:
            logging.info(f"Executando comando: {command} no dispositivo: {identificacao}")
            output += net_connect.send_command_timing(command) + "\n"

        # Fechar a conexão
        net_connect.disconnect()

        # Criar o nome do arquivo com base na identificação e data atual
        current_time = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        backup_dir = f"/root/backup/{cliente}/RT"
        filename = f"{backup_dir}/bkp_{identificacao}_{current_time}.txt"

        # Garantir que o diretório do cliente exista
        os.makedirs(backup_dir, exist_ok=True)

        # Salvar o log no arquivo com o nome gerado
        os.makedirs(os.path.dirname(filename), exist_ok=True)  # Garantir que o diretório exista
        with open(filename, 'w') as log_file:
            log_file.write(output)
            log_file.write("\n\n--- End of session log ---\n")

        logging.info(f"Backup do dispositivo {identificacao} realizado com sucesso. Arquivo salvo em: {filename}")

        # Copiar o arquivo de backup para a unidade de redundância
        redundancy_backup_dir = f"/mnt/backup/{cliente}/RT"
        os.makedirs(redundancy_backup_dir, exist_ok=True)  # Criar diretório no destino, caso não exista
        redundancy_filename = os.path.join(redundancy_backup_dir, f"bkp_{identificacao}_{current_time}.txt")

        # Copiar o backup
        shutil.copy(filename, redundancy_filename)
        logging.info(f"Backup copiado para a unidade de redundância em: {redundancy_filename}")

    except Exception as e:
        logging.error(f"Erro ao conectar com {host}: {e}")

# Iniciar o processo de leitura do arquivo CSV
process_hosts_from_csv(csv_file)