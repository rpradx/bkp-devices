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
csv_file = "/root/backup/scripts/devices.csv"

# Variável para o nome do cliente
cliente = sys.argv[1]

# Verifique se o arquivo CSV existe
if not os.path.isfile(csv_file):
    print(f"Erro: o arquivo {csv_file} não foi encontrado.")
    sys.exit(1)

# Configuração do log
log_directory = f"/root/backup/{cliente}/log"  # Diretório de log agora inclui o cliente
os.makedirs(log_directory, exist_ok=True)  # Garantir que o diretório de log exista
log_filename = os.path.join(log_directory, 'backup_{tipo}_{vendor}.log')  # Arquivo de log inclui tipo e vendor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, mode='a'),  # Registra no arquivo (em modo de anexar)
        logging.StreamHandler()  # Exibe no terminal
    ]
)

# Mapeamento de dispositivos e comandos
devices_map = {
    'huawei-rt': ('huawei', 'display current-configuration | no-more'),
    'huawei-olt': ('huawei_smartax', 'display current-configuration | no-more'),  # Adicionando enable() para OLT
    'mikrotik': ('mikrotik_routeros', 'export terse'),
    'cisco': ('cisco_ios', 'show running-config'),
    'huawei-sw': ('huawei', [
        "screen-length 0 temporary",
        "display current-configuration"
    ])
}

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
            tipo = row['tipo'].upper()
            vendor = row['vendor'].upper()

            # Limpeza da variável de identificação
            identificacao = re.sub(r'[^a-zA-Z0-9_-]', '', identificacao)

            # Chamada para a função de backup
            backup_device(host, username, password, port, identificacao, tipo, vendor)

# Função para realizar o backup de cada dispositivo
def backup_device(host, username, password, port, identificacao, tipo, vendor):
    logging.info(f"Iniciando o backup para o dispositivo: {identificacao} (Host: {host})")

    # Verifique se o tipo de dispositivo existe no mapeamento devices_map
    if vendor not in devices_map:
        logging.error(f"Erro: Vendor '{vendor}' não encontrado em devices_map.")
        return

    device_info = devices_map[vendor]  # Busca o tipo do Netmiko e o comando correspondente
    device_type_netmiko, command = device_info

    # Definir os detalhes da conexão SSH
    device = {
        'device_type': device_type_netmiko,
        'host': host,
        'username': username,
        'password': password,
        'port': port,
        'secret': password,
        'verbose': True,
        'timeout': 120,
        'banner_timeout': 120,
    }

    # Estabelecer a conexão SSH
    try:
        net_connect = ConnectHandler(**device)

        # Lógica de execução dos comandos
        if vendor == 'huawei-olt':
            net_connect.enable()
            output = net_connect.send_command_timing(command)
        elif vendor == 'huawei-sw':
            for cmd in command:
                logging.info(f"Executando comando: {cmd} no dispositivo: {identificacao}")
                output = net_connect.send_command(cmd, delay_factor=2)
        else:
            logging.info(f"Executando comando: {command} no dispositivo: {identificacao}")
            output = net_connect.send_command(command, delay_factor=2)

        # Fechar a conexão
        net_connect.disconnect()

        # Criar o nome do arquivo com base na identificação e data atual
        current_time = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        backup_dir = f"/root/backup/{cliente}/{tipo}/{identificacao}"  # Diretório de backup inclui o tipo e identificacao
        os.makedirs(backup_dir, exist_ok=True)  # Criar diretório baseado no tipo

        # Salvar o log no arquivo com o nome gerado
        log_filename = os.path.join(log_directory, f'backup_{tipo}_{vendor}.log')  # Nome do log inclui tipo e vendor
        os.makedirs(os.path.dirname(log_filename), exist_ok=True)
        with open(log_filename, 'a') as log_file:
            log_file.write(f"{current_time} - Backup iniciado para: {identificacao} ({host})\n")
            log_file.write(output)
            log_file.write("\n\n--- End of session log ---\n")

        # Criar o nome do arquivo de backup
        filename = os.path.join(backup_dir, f"bkp_{identificacao}_{current_time}.txt")

        # Garantir que o diretório do cliente e tipo exista
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Salvar o arquivo de backup
        with open(filename, 'w') as backup_file:
            backup_file.write(output)
            backup_file.write("\n\n--- End of session log ---\n")

        logging.info(f"Backup do dispositivo {identificacao} realizado com sucesso. Arquivo salvo em: {filename}")

        # Copiar o arquivo de backup para a unidade de redundância
        redundancy_backup_dir = f"/mnt/backup/{cliente}/{tipo}/{identificacao}"  # Diretório de redundância inclui o tipo e identificacao
        os.makedirs(redundancy_backup_dir, exist_ok=True)  # Criar diretório de redundância baseado no tipo
        redundancy_filename = os.path.join(redundancy_backup_dir, f"bkp_{identificacao}_{current_time}.txt")

        # Copiar o backup
        shutil.copy(filename, redundancy_filename)
        logging.info(f"Backup copiado para a unidade de redundância em: {redundancy_filename}")

    except Exception as e:
        logging.error(f"Erro ao conectar com {host}: {e}")

# Iniciar o processo de leitura do arquivo CSV
process_hosts_from_csv(csv_file)
