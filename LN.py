## Esse código serve para listar o nome de todos os arquivos dentro de um pasta incluindo suas subpastas
# python LN.py
# ==============================================================================
# ZONA DE CONFIGURAÇÃO
# ==============================================================================

# 1. Caminho da pasta que você quer ler. 
# (Mantenha o 'r' antes das aspas para evitar erros com as barras do Windows)
DIRETORIO_ALVO = r"D:\CURSOS"

# 2. O que você quer extrair?
# True = Traz o caminho completo (ex: C:\pasta\arquivo.txt)
# False = Traz apenas o nome do arquivo (ex: arquivo.txt)
INCLUIR_CAMINHO_COMPLETO = True

# 3. Exportação
GERAR_ARQUIVO_EXCEL = True                   # Se True, vai auto-instalar bibliotecas e gerar um Excel
NOME_ARQUIVO_EXCEL = "lista_arquivos.xlsx"   # Nome do arquivo Excel que será gerado

# ==============================================================================
# FIM DA ZONA DE CONFIGURAÇÃO - NÃO PRECISA ALTERAR NADA ABAIXO DESTA LINHA
# ==============================================================================

import os
import sys
import subprocess

def verificar_e_instalar_bibliotecas():
    """Verifica se as bibliotecas necessárias para o Excel existem, senão as instala."""
    bibliotecas_necessarias = {'pandas': 'pandas', 'openpyxl': 'openpyxl'}
    
    for lib, pacote in bibliotecas_necessarias.items():
        try:
            __import__(lib)
        except ImportError:
            print(f"[*] Biblioteca '{lib}' não encontrada. Instalando automaticamente...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])
                print(f"[+] '{lib}' instalada com sucesso!")
            except Exception as e:
                print(f"[-] Erro ao instalar '{lib}': {e}")
                sys.exit(1)

def listar_arquivos(diretorio):
    """Lista todos os arquivos do diretório e suas subpastas."""
    if not os.path.exists(diretorio):
        print(f"[-] Erro: O diretório '{diretorio}' não existe.")
        sys.exit(1)

    lista_final = []
    print(f"[*] Escaneando a pasta: {diretorio}...")

    # os.walk percorre a pasta raiz e todas as subpastas automaticamente
    for pasta_atual, subpastas, arquivos in os.walk(diretorio):
        for nome_arquivo in arquivos:
            if INCLUIR_CAMINHO_COMPLETO:
                # Junta o caminho da pasta com o nome do arquivo
                caminho = os.path.join(pasta_atual, nome_arquivo)
                lista_final.append(caminho)
            else:
                lista_final.append(nome_arquivo)
                
    return lista_final

def main():
    # 1. Obter a lista de arquivos
    arquivos = listar_arquivos(DIRETORIO_ALVO)
    
    if not arquivos:
        print("[!] Nenhum arquivo encontrado nesta pasta ou subpastas.")
        return

    print(f"[+] Foram encontrados {len(arquivos)} arquivos.\n")

    # 2. Exibir no terminal (mostra apenas os 10 primeiros se forem muitos, para não travar a tela)
    limite_exibicao = 10
    for arq in arquivos[:limite_exibicao]:
        print(f" - {arq}")
    
    if len(arquivos) > limite_exibicao:
        print(f"   ... e mais {len(arquivos) - limite_exibicao} arquivos.")

    # 3. Exportar para Excel (se configurado)
    if GERAR_ARQUIVO_EXCEL:
        print("\n[*] Preparando para gerar o Excel...")
        verificar_e_instalar_bibliotecas()
        
        import pandas as pd # Importado aqui para garantir que já foi auto-instalado
        
        try:
            df = pd.DataFrame(arquivos, columns=["Nome / Caminho do Arquivo"])
            df.to_excel(NOME_ARQUIVO_EXCEL, index=False)
            print(f"[+] SUCESSO! Lista salva no arquivo: '{NOME_ARQUIVO_EXCEL}' na mesma pasta deste script.")
        except Exception as e:
            print(f"[-] Erro ao gerar o arquivo Excel: {e}")

if __name__ == "__main__":
    main()