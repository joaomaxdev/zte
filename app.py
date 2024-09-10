import sys
import os
import subprocess
import pyfiglet

def display_title():
    ascii_art = pyfiglet.figlet_format("ZTE C650 SCRIPTS", font="big", width=80)
    print(ascii_art)

def main_menu():
    os.system('cls' if os.name == 'nt' else 'clear')  # Limpa a tela
    display_title()  # Exibe a arte ASCII
    print("         🇳​​​​​🇪​​​​​🇽​​​​​🇺​​​​​🇸​​​​​​")

    print("=" * 50)
    print("           MENU PRINCIPAL")
    print("=" * 50)
    
    while True:
        print("[1] ➤  ONUS NÃO AUTORIZADAS")
        print("[2] ➤  PESQUISAR ONU POR SN")
        print("[3] ➤  SINAL DE RETORNO")
        print("[4] ➤  AUTORIZAR ONU")
        print("[5] ➤  AUTORIZAR ONU EM MASSA")
        print("=" * 50)
        print("Selecione uma opção (ou 'sair' para encerrar):")
        
        choice = input("Digite sua escolha: ")
        
        if choice == "1":
            run_script("onus_nao_autorizadas.py")
        elif choice == "2":
            run_script("pesquisar_onu_por_sn.py")
        elif choice == "3":
            run_script("sinal_de_retorno.py")
        elif choice == "4":
            run_script("autorizar_onu.py")
        elif choice == "5":
            run_script("autorizar_onu_em_massa.py")
        elif choice.lower() == 'sair':
            print("Saindo...")
            break
        else:
            print("Escolha inválida! Por favor, selecione novamente.")

def run_script(script_name):
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', script_name)
        subprocess.run([sys.executable, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ocorreu um erro ao executar {script_name}: {e}")
    except FileNotFoundError:
        print(f"O arquivo {script_name} não foi encontrado.")

if __name__ == "__main__":
    main_menu()