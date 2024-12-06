
# Script para Backup de Switches e Roteadores e OLTs

Este script realiza o backup das configurações de equipamentos, tanto de Switches quanto de Roteadores e OLTs, gerando arquivos `.txt` com as configurações coletadas através dos comandos `"display current" | "show run"`.

## Tabela de Conteúdos

1. [Requisitos](#requisitos)
2. [Como Executar](#como-executar)
    1. [Preparação do Ambiente](#preparação-do-ambiente)
    2. [Configuração de Permissões](#configuração-de-permissões)
3. [Configuração do Crontab](#configuração-do-crontab)
4. [Licença](#licença)

## Requisitos

Para executar o script, você precisará ter o seguinte instalado:

- [Netmiko](https://pypi.org/project/netmiko/1.4.1/) para automação de conexões SSH com os equipamentos Huawei.

Você pode instalar o Netmiko usando o seguinte comando:

```bash
pip install netmiko
```

## Como Executar

### Preparação do Ambiente

1. **Criação dos diretórios** para armazenar o backup e os scripts:

   ```bash
   mkdir -p /root/backup/scripts
   ```

2. **Mover os arquivos de script e configuração** para o diretório adequado:

   ```bash
   ## CISCO ##
   mv backup-rt-cisco.py /root/backup/scripts
   mv cisco.csv /root/backup/scripts
   
   ## HUAWEI ##
   mv backup-sw-huawei.py /root/backup/scripts
   mv backup-router-huawei.py /root/backup/scripts
   mv backup-olt-huawei.py /root/backup/scripts
   mv switchs.csv /root/backup/scripts
   mv routers.csv /root/backup/scripts
   mv olts.csv /root/backup/scripts
   ```

### Configuração de Permissões

3. **Samba**: Se você estiver utilizando o Samba para compartilhar arquivos de backup, mova o arquivo `.smbcredentials` e configure as permissões adequadas:

   ```bash
   mv .smbcredentials /root/backup/scripts
   chmod 600 /root/backup/scripts/.smbcredentials
   ```

4. **Mount**: Caso seja necessário montar um compartilhamento de rede, mova o script `mount.sh` e ajuste as permissões:

   ```bash
   mv mount.sh /root/backup/scripts
   chmod 750 /root/backup/scripts/mount.sh
   ```

## Configuração do Crontab

Para automatizar o processo de backup e montagem, adicione as seguintes entradas ao seu `crontab`.

```bash
####################################################
#                       HUAWEI                     #
####################################################

##################
# BACKUP SWITCHS #
##################
10 23 * * 3,6 /usr/bin/python3 /root/backup/scripts/backup_sw_huawei.py CLIENTE

##################
# BACKUP ROUTERS #
##################
20 23 * * 3,6 /usr/bin/python3 /root/backup/scripts/backup_router_huawei.py CLIENTE

##################
# BACKUP OLTs    #
##################
30 23 * * 1,3,6 /usr/bin/python3 /root/backup/scripts/backup_olt_huawei.py CLIENTE

###################################################
#                       CISCO                     #
###################################################

##################
# BACKUP ROUTERS #
##################
20 23 * * 3,6 /usr/bin/python3 /root/backup/scripts/backup_rt_cisco.py CLIENTE

##########################
# MOUNT COMPARTILHAMENTO #
##########################
*/10 * * * * /root/backup/scripts/mount.sh
```

Para editar o crontab, execute o comando:

```bash
crontab -e
```
