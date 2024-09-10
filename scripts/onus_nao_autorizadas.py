import paramiko
import time
import sys
import os
import re
from prettytable import PrettyTable

# Adiciona o caminho para o módulo de configuração
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
from config import hostname, port, username, password

def list_unauthorized_onus():
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        client.connect(hostname, port=port, username=username, password=password, timeout=10)
        
        channel = client.invoke_shell()
        time.sleep(1)
        
        command = "show pon onu uncfg"
        channel.send(command + "\n")
        time.sleep(2)
        
        output = channel.recv(65535).decode('utf-8')

        onu_lines = [line for line in output.splitlines() if re.search(r'^\S+.*ONU', line)]
        if onu_lines:
            qtd_onus = len(onu_lines)
            print(f"Foram encontradas {qtd_onus} ONUs para autorizar.")
            display_onu_table(onu_lines)
        else:
            print("Não há ONUs para serem autorizadas.")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        client.close()
    
    input("\nPressione Enter para voltar ao menu principal...")
    os.system('cls' if os.name == 'nt' else 'clear')  # Limpa o console

def display_onu_table(onu_lines):
    table = PrettyTable()
    table.field_names = ["SLOT", "PON", "SERIAL NUMBER"]

    for line in onu_lines:
        parts = line.split()
        if len(parts) >= 4:
            # Extrai slot e pon a partir de gpon_olt
            gpon_info = parts[0]  # Ex: gpon_olt-1/1/13
            slot, pon = gpon_info.split('/')[1:3]
            serial_number = parts[2]  # Serial number está na segunda posição

            # Formata o valor do slot
            formatted_slot = f"SLOT: {slot}"
            table.add_row([formatted_slot, pon, serial_number])

    print(table)

if __name__ == "__main__":
    list_unauthorized_onus()