#!/usr/bin/env python3

import sys
import csv
import logging
from netmiko import ConnectHandler
import os
import shutil
from datetime import datetime
import re
import glob

# Quantidade de backups a serem mantidos
MAX_BACKUPS = 4

# Definindo o nome fixo do arquivo CSV
csv_file = "/root/backup/scripts/devices.csv"

# Variável para o nome do cliente
cliente = sys.argv[1].upper()

# Verifique se o arquivo CSV existe
if not os.path.isfile(csv_file):
    print(f"Erro: o arquivo {csv_file} não foi encontrado.")
    sys.exit(1)

# Função para verificar se a unidade de redundância está montada
def check_redundancy_mount():
    # Verifica se o ponto de montagem '/mnt/backup' está presente na saída do comando 'mount'
    if not os.path.ismount("/mnt/backup"):
        logging.error("Erro: A unidade de redundância não está montada em /mnt/backup.")
        return False
    return True

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
    'huawei-olt': ('huawei_smartax', 'display current-configuration | no-more'),
    'mikrotik': ('mikrotik_routeros', 'export terse'),
    'cisco': ('cisco_ios', 'show running-config'),
    'datacom': ('cisco_ios', 'show running-config | nomore'),
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
            vendor = row['vendor']

            # Limpeza da variável de identificação
            identificacao = re.sub(r'[^a-zA-Z0-9_-]', '', identificacao)

            # Chamada para a função de backup
            backup_device(host, username, password, port, identificacao, tipo, vendor)
            # Após o backup, chamar a função de retenção
            retain_backups(cliente, tipo, identificacao)

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
        elif vendor == 'datacom':
            logging.info(f"Executando comando: {command} no dispositivo {identificacao}")
            output = net_connect.send_command_timing(command)
        else:
            logging.info(f"Executando comando: {command} no dispositivo: {identificacao}")
            output = net_connect.send_command(command, delay_factor=2)

        # Fechar a conexão
        net_connect.disconnect()

        # Criar o nome do arquivo com base na identificação e data atual
        current_time = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        backup_dir = f"/root/backup/{cliente}/{tipo}/{identificacao}"  # Diretório de backup inclui o tipo e identificacao
        os.makedirs(backup_dir, exist_ok=True)  # Criar diretório baseado no tipo

        # Criar o nome do arquivo de backup
        filename = os.path.join(backup_dir, f"bkp_{identificacao}_{current_time}.txt")

        # Garantir que o diretório do cliente e tipo exista
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        # Salvar o arquivo de backup
        with open(filename, 'w') as backup_file:
            backup_file.write(output)
            backup_file.write("\n\n--- End of session log ---\n")

        logging.info(f"Backup do dispositivo {identificacao} realizado com sucesso. Arquivo salvo em: {filename}")

        # Verificar se a unidade de redundância está montada antes de copiar o backup
        if not check_redundancy_mount():
            logging.error(f"Backup não foi copiado para a unidade de redundância devido ao erro de montagem.")
            return  # Impede a cópia para a unidade de redundância se não estiver montada

        # Copiar o arquivo de backup para a unidade de redundância
        redundancy_backup_dir = f"/mnt/backup/{cliente}/{tipo}/{identificacao}"  # Diretório de redundância inclui o tipo e identificacao
        os.makedirs(redundancy_backup_dir, exist_ok=True)  # Criar diretório de redundância baseado no tipo
        redundancy_filename = os.path.join(redundancy_backup_dir, f"bkp_{identificacao}_{current_time}.txt")

        # Copiar o backup
        shutil.copy(filename, redundancy_filename)
        logging.info(f"Backup copiado para a unidade de redundância em: {redundancy_filename}")

    except Exception as e:
        logging.error(f"Erro ao conectar com {host}: {e}")

# Função de retenção de backups, mantendo apenas os backups mais recentes
def retain_backups(cliente, tipo, identificacao, max_backups=MAX_BACKUPS):
    # Diretório de backup original
    backup_dir = f"/root/backup/{cliente}/{tipo}/{identificacao}"

    # Diretório de backup na unidade de redundância
    backup_dir_redundancia = f"/mnt/backup/{cliente}/{tipo}/{identificacao}"

    # Verifica se o diretório de backup original existe
    if os.path.exists(backup_dir):
        # Obter todos os arquivos de backup no diretório original
        backups = sorted(glob.glob(f"{backup_dir}/*.txt"), key=os.path.getmtime, reverse=True)

        # Se houver mais backups do que o permitido, excluir os mais antigos
        if len(backups) > max_backups:
            backups_to_delete = backups[max_backups:]  # Pega os backups mais antigos, além dos mais recentes
            for backup in backups_to_delete:
                logging.info(f"Excluindo backup antigo no diretório original: {backup}")
                os.remove(backup)

    # Verifica se o diretório de backup na unidade de redundância existe
    if os.path.exists(backup_dir_redundancia):
        # Obter todos os arquivos de backup no diretório de redundância
        backups_redundancia = sorted(glob.glob(f"{backup_dir_redundancia}/*.txt"), key=os.path.getmtime, reverse=True)

        # Se houver mais backups do que o permitido, excluir os mais antigos
        if len(backups_redundancia) > max_backups:
            backups_to_delete_redundancia = backups_redundancia[max_backups:]  # Pega os backups mais antigos, além dos mais recentes
            for backup in backups_to_delete_redundancia:
                logging.info(f"Excluindo backup antigo na unidade de redundância: {backup}")
                os.remove(backup)

# Iniciar o processo de leitura do arquivo CSV
process_hosts_from_csv(csv_file)
