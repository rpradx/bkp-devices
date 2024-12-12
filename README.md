
# Script para Backup de Switches, Roteadores e OLTs

Este script realiza o backup das configurações de equipamentos, tanto de Switches quanto de Roteadores e OLTs, gerando arquivos `.txt` com as configurações.

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
   mv backup-devices.py /root/backup/scripts
   mv devices.csv /root/backup/scripts
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
##################
# BACKUP DEVICES #
##################
0 23 */2 * * /usr/bin/python3 /root/backup/scripts/backup-devices.py "CLIENTE"

##########################
# MOUNT COMPARTILHAMENTO #
##########################
*/10 * * * * /root/backup/scripts/mount.sh
```

Para editar o crontab, execute o comando:

```bash
crontab -e
```
