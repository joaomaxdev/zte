import os
import sys
import time
import paramiko
import re

# Adicionar o caminho do arquivo de configuração
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
from config import hostname, port, username, password

def execute_command(channel, command):
    """Executa um comando na OLT e retorna a saída."""
    channel.send(command + '\n')
    time.sleep(2)
    output = ''
    while channel.recv_ready():
        output += channel.recv(65536).decode('utf-8')
    return output

def provision_onu(channel, slot, pon, position, serial_number, vlan):
    """
    Aprovisiona uma única ONU usando o número de série fornecido.
    """
    try:
        command = f"interface gpon-olt-1/{slot}/{pon} onu {position} type ONU model-name {serial_number}"
        execute_command(channel, command)
        print(f"ONU {serial_number} configurada na posição {position} no slot {slot}, pon {pon}.")

        command_vlan = f"service-port {position} vport 1 user-vlan {vlan} vlan {vlan} port gpon-olt-1/{slot}/{pon} onu {position}"
        execute_command(channel, command_vlan)
        print(f"VLAN {vlan} configurada para a ONU {serial_number}.")

    except Exception as e:
        print(f"Erro ao provisionar ONU {serial_number}: {str(e)}")

def provision_onu_mass(channel, slot, pon, vlan):
    """Aprovisiona ONUs em massa para um determinado slot e pon."""
    command = f"show pon onu uncfg gpon_olt-1/{slot}/{pon}"
    output = execute_command(channel, command)
    
    onu_list = []
    for line in output.splitlines():
        if line.startswith("gpon_olt") and line.strip():
            parts = line.split()
            if len(parts) >= 4:
                serial_number = parts[2]
                onu_list.append(serial_number)

    if not onu_list:
        print("Nenhuma ONU não autorizada encontrada.")
        return

    print(f"ONUs não autorizadas encontradas no SLOT {slot} | PON {pon}:")
    for serial in onu_list:
        print(f"Serial Number: {serial}")
    
    confirm = input("Deseja provisionar todas essas ONUs? (s/n): ")
    if confirm.lower() != 's':
        return

    print("AGUARDE O APROVISIONAMENTO...")
    for position, serial_number in enumerate(onu_list, start=1):
        provision_onu(channel, slot, pon, position, serial_number, vlan)
        print(f"ONU {serial_number} aprovisionada com sucesso na posição {position}.")
    
    print("Todas as ONUs foram aprovisionadas com sucesso.")

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, port=port, username=username, password=password)
        channel = client.invoke_shell()

        slot = int(input("Digite o número do SLOT: "))
        pon = int(input("Digite o número do PON: "))

        command = f"show pon onu uncfg gpon_olt-1/{slot}/{pon}"
        output = execute_command(channel, command)

        onu_list = []
        for line in output.splitlines():
            if line.startswith("gpon_olt") and line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    serial_number = parts[2]
                    onu_list.append(serial_number)

        if not onu_list:
            print("Nenhuma ONU não autorizada encontrada.")
            return

        print(f"ONUs não autorizadas encontradas no SLOT {slot} | PON {pon}:")
        for serial in onu_list:
            print(f"Serial Number: {serial}")

        confirm = input("Deseja provisionar todas essas ONUs? (s/n): ")
        if confirm.lower() != 's':
            return

        vlan = int(input("Digite a VLAN para as ONUs: "))
        provision_onu_mass(channel, slot, pon, vlan)
        print("Provisionamento em massa concluído.")

    finally:
        client.close()

if __name__ == "__main__":
    main()
