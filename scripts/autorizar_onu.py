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
    time.sleep(2)  # Aumentar o tempo para garantir que o comando seja processado
    output = ''
    while channel.recv_ready():
        output += channel.recv(65536).decode('utf-8')
    return output

def parse_ranges(ranges_str):
    """Converte a string de intervalos em uma lista de números."""
    ranges_str = ranges_str.replace(" ", "").strip('<>')
    ranges = ranges_str.split(',')
    numbers = []
    
    for r in ranges:
        if '-' not in r:
            numbers.append(int(r))
        else:
            start, end = map(int, r.split('-'))
            numbers.extend(range(start, end + 1))
    
    return numbers

def parse_occupied_slots(output):
    """Parseia a saída para determinar os slots ocupados e retorna um array com todos os números."""
    match = re.search(r'<([^>]*)>', output)  # Captura as posições ocupadas
    if match:
        occupied = match.group(1)
        return parse_ranges(occupied)
    return []

def choose_onu(onu_list):
    """Escolhe uma ONU da lista e retorna o slot e pon correspondentes."""
    for index, onu in enumerate(onu_list):
        print(f"[{index + 1}] - {onu}")
    
    while True:
        try:
            choice = int(input("Escolha uma opção da lista: ")) - 1
            if choice < 0 or choice >= len(onu_list):
                raise IndexError  # Raise an error if out of range
            break  # Break the loop if valid
        except ValueError:
            print("Por favor, insira um número válido.")
        except IndexError:
            print("Escolha um número dentro da lista.")
    
    selected_onu = onu_list[choice]
    slot, pon = map(int, re.findall(r'SLOT (\d+) \| PON (\d+)', selected_onu)[0])
    return slot, pon

def get_onu_list(channel):
    """Executa o comando para obter a lista de ONUs e retorna uma lista formatada com SERIAL_NUMBER."""
    command = "show pon onu uncfg"
    output = execute_command(channel, command)
    
    onu_list = []
    for line in output.splitlines():
        if line.startswith("gpon_olt") and line.strip():  # Filtra apenas as linhas relevantes
            parts = line.split()
            if len(parts) >= 4:
                slot_pon = parts[0].split('/')
                if len(slot_pon) >= 3:  # Verifica se há pelo menos 3 partes
                    serial_number = parts[2]  # Captura o SERIAL_NUMBER
                    onu_info = f"{serial_number} ESTÁ NO SLOT {slot_pon[1]} | PON {slot_pon[2]}"
                    onu_list.append(onu_info)
    
    return onu_list

def get_serial_number(channel, slot, pon):
    """Captura o SERIAL_NUMBER usando o comando show pon onu uncfg."""
    command = "show pon onu uncfg"
    output = execute_command(channel, command)
    
    # Encontrar o SN correspondente ao slot e PON
    match = re.search(rf'gpon_olt-1/{slot}/{pon}\s+\w+\s+(\w+)', output)
    if match:
        return match.group(1)
    return None

def provision_onu(channel, slot, pon, position, serial_number, vlan):
    """Aprovisiona a ONU usando os comandos fornecidos."""
    commands = [
        "conf t",
        f"interface gpon_olt-1/{slot}/{pon}",
        f"onu {position} type BRIDGE SN {serial_number}",
        "exit",
        f"interface gpon_onu-1/{slot}/{pon}:{position}",
        "tcont 4 profile 1G",
        "gemport 1 tcont 4",
        "exit",
        f"interface vport-1/{slot}/{pon}.{position}:1",
        f"service-port 1 user-vlan {vlan} vlan {vlan}",
        "exit"
    ]

    for command in commands:
        execute_command(channel, command)

def get_return_signal(slot, pon, onu):
    command = f"show pon power attenuation gpon_onu-1/{slot}/{pon}:{onu}"
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=port, username=username, password=password, timeout=10)
        
        channel = client.invoke_shell()
        time.sleep(1)
        
        channel.send(command + "\n")
        time.sleep(5)  # Aumentar o tempo para garantir que o comando seja processado
        
        output = channel.recv(65535).decode('utf-8')
        return parse_output(output)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

def parse_output(output):
    sfp_output_signal = ""
    cto_expected_signal = ""
    un_power = ""
    return_signal = ""

    up_pattern = re.compile(r'up\s+Rx\s+:\s*([-+]?\d*\.\d+|\d+)\(dbm\)\s+Tx:\s*([-+]?\d*\.\d+|\d+)\(dbm\)')
    down_pattern = re.compile(r'down\s+Tx\s*:\s*([-+]?\d*\.\d+|\d+)\(dbm\)\s+Rx:\s*([-+]?\d*\.\d+|\d+)')

    for line in output.splitlines():
        up_match = up_pattern.search(line)
        down_match = down_pattern.search(line)

        if up_match:
            return_signal = up_match.group(1)
            un_power = up_match.group(2)

        if down_match:
            sfp_output_signal = down_match.group(1)
            cto_expected_signal = down_match.group(2)

    return {
        "SFP Output Signal": sfp_output_signal,
        "CTO Expected Signal": cto_expected_signal,
        "UN Power": un_power,
        "Return Signal": return_signal,
    }

def print_results(signals, slot, pon, onu):
    print(f"\nZTE C650 | SLOT: {slot} PON: {pon} ONU: {onu}")
    print("-" * 30)
    print(f"{'Saída SFP Gbic:':<20} {signals['SFP Output Signal']}")
    print(f"{'Sinal esperado CTO:':<20} {signals['CTO Expected Signal']}")
    print(f"{'Potência ONU:':<20} {signals['UN Power']}")
    print(f"{'Sinal de retorno ONU:':<20} {signals['Return Signal']}")
    print("-" * 30)

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, port=port, username=username, password=password)
        channel = client.invoke_shell()

        # Obter a lista de ONUs dinamicamente
        onu_list = get_onu_list(channel)

        if not onu_list:
            print("Nenhuma ONU encontrada.")
            return

        slot, pon = choose_onu(onu_list)

        serial_number = get_serial_number(channel, slot, pon)
        if not serial_number:
            print("Erro ao capturar o SERIAL_NUMBER.")
            return

        command = f"show interface gpon_onu-1/{slot}/{pon}:?"
        output = execute_command(channel, command)

        occupied_numbers = parse_occupied_slots(output)

        total_slots = set(range(1, 129))
        available_slots = total_slots - set(occupied_numbers)

        print("As vagas ocupadas são:", occupied_numbers)
        print(f"SLOT {slot} | PON {pon} HA {len(available_slots)} VAGAS DISPONÍVEIS: {sorted(available_slots)}")

        if available_slots:
            position = min(available_slots)
            vlan = int(input("Digite a VLAN para a ONU: "))
            print("AGUARDE O APROVISIONAMENTO...")

            provision_onu(channel, slot, pon, position, serial_number, vlan)
            print(f"ONU {serial_number} APROVISIONADA COM SUCESSO!")
            print(f"SLOT: {slot} | PON: {pon} | VLAN: {vlan}")

            signals = get_return_signal(slot, pon, serial_number)
            print_results(signals, slot, pon, serial_number)
        else:
            print("Não há posições disponíveis para aprovisionar a ONU.")

    finally:
        client.close()

if __name__ == "__main__":
    main()