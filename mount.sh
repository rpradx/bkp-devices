#!/bin/bash

# Diretório de logs
LOG_DIR="/root/backup/log"
LOG_FILE="${LOG_DIR}/mount_backup_$(date +'%d_%m_%Y').log"

# Garantir que o diretório de logs exista
mkdir -p "$LOG_DIR"

# Verificar se o ponto de montagem está ativo
VERIFICA=$(mount | grep -c 'backup')

if [ "$VERIFICA" -eq 1 ]; then
    echo "$(date +'%d/%m/%Y %H:%M:%S') - O compartilhamento já está montado." >> "$LOG_FILE"
else
    # Verifica se o diretório de montagem existe
    if [ ! -d /mnt/backup ]; then
        echo "$(date +'%d/%m/%Y %H:%M:%S') - O diretório /mnt/backup não existe. Criando o diretório..." >> "$LOG_FILE"
        mkdir -p /mnt/backup
    fi

    # Tenta desmontar, se necessário, e monta o compartilhamento
    echo "$(date +'%d/%m/%Y %H:%M:%S') - Tentando montar o compartilhamento..." >> "$LOG_FILE"
    umount -l /mnt/backup 2>> "$LOG_FILE"  # Redireciona os erros para o log

    mount -t cifs //"IP_SERVER"/bkp-clientes /mnt/backup/ -o credentials=/root/backup/scripts/.smbcredentials,vers=3.0 2>> "$LOG_FILE"

    # Verificar se a montagem foi bem-sucedida
    if mount | grep -q 'backup'; then
        echo "$(date +'%d/%m/%Y %H:%M:%S') - Compartilhamento montado com sucesso em /mnt/backup." >> "$LOG_FILE"
    else
        echo "$(date +'%d/%m/%Y %H:%M:%S') - Erro ao montar o compartilhamento. Verifique os logs de erro." >> "$LOG_FILE"
    fi
fi