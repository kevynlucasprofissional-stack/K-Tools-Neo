# -*- coding: utf-8 -*-
#  Junta vários arquivos .md em um único arquivo, com separadores para identificar o início e o fim de cada arquivo original.
# python JM.py

#==============================================================================
# ZONA DE CONFIGURAÇÃO
# Modifique as variáveis abaixo de acordo com a sua necessidade.
#==============================================================================

# Caminho para a pasta onde os seus arquivos .md estão salvos.
# Exemplo para Windows: "C:\\Users\\SeuUsuario\\Desktop\\Meus_Textos"
# Exemplo para Linux ou Mac: "/home/SeuUsuario/documentos/artigos"
PASTA_DE_ENTRADA = r"F:\ARQUIVOS\CONCEITOS DE CONTEÚDO\MEU PRIVADO\Todos os vídeos\MD"

# Caminho para a pasta onde o arquivo final será salvo.
# Exemplo para Windows: "C:\\Users\\SeuUsuario\\Desktop\\Resultado"
# Exemplo para Linux ou Mac: "/home/SeuUsuario/documentos/final"
PASTA_DE_SAIDA = r"F:\ARQUIVOS\CONCEITOS DE CONTEÚDO\MEU PRIVADO\Todos os vídeos\MD"

# O nome que você deseja para o arquivo .md final que será gerado.
NOME_DO_ARQUIVO_DE_SAIDA = "Conteúdos_unidos.md"

#==============================================================================
# FIM DA ZONA DE CONFIGURAÇÃO
# Não é necessário modificar nada abaixo desta linha para o uso básico.
#==============================================================================

import os
import glob

def juntar_arquivos_md(pasta_entrada, pasta_saida, nome_arquivo_saida):
    """
    Junta vários arquivos .md em um único arquivo, com separadores
    para identificar o início e o fim de cada arquivo original.
    """
    # Garante que a pasta de saída exista. Se não, ela será criada.
    if not os.path.exists(pasta_saida):
        print(f"A pasta de saída '{pasta_saida}' não existe. Criando...")
        os.makedirs(pasta_saida)

    # Constrói o caminho completo para o arquivo de saída.
    caminho_arquivo_saida = os.path.join(pasta_saida, nome_arquivo_saida)

    # Busca por todos os arquivos .md na pasta de entrada.
    arquivos_md = glob.glob(os.path.join(pasta_entrada, '*.md'))

    if not arquivos_md:
        print(f"Nenhum arquivo .md foi encontrado em '{pasta_entrada}'.")
        return

    # Ordena os arquivos em ordem alfabética para uma junção previsível.
    arquivos_md.sort()

    print(f"Arquivos .md encontrados: {len(arquivos_md)}")
    for arquivo in arquivos_md:
        print(f"  - {os.path.basename(arquivo)}")

    # Abre o arquivo de saída no modo de escrita ('w').
    # O 'with' garante que o arquivo será fechado corretamente no final.
    with open(caminho_arquivo_saida, 'w', encoding='utf-8') as outfile:
        # Itera sobre cada arquivo .md encontrado.
        for nome_arquivo in arquivos_md:
            # Escreve o separador de início do arquivo.
            outfile.write(f'\\n---\\n')
            outfile.write(f'<!-- INÍCIO DO ARQUIVO: {os.path.basename(nome_arquivo)} -->\\n')
            outfile.write(f'---\\n\\n')

            # Abre o arquivo .md atual no modo de leitura ('r').
            with open(nome_arquivo, 'r', encoding='utf-8') as infile:
                # Lê todo o conteúdo do arquivo e o escreve no arquivo de saída.
                outfile.write(infile.read())

            # Escreve o separador de fim do arquivo.
            outfile.write(f'\\n\\n---\\n')
            outfile.write(f'<!-- FIM DO ARQUIVO: {os.path.basename(nome_arquivo)} -->\\n')
            outfile.write(f'---\\n\\n')
    
    print(f"\\nSucesso! Os arquivos foram juntados em '{caminho_arquivo_saida}'")

if __name__ == "__main__":
    # Verifica se os caminhos de configuração foram alterados.
    if PASTA_DE_ENTRADA == "sua_pasta_de_entrada_aqui" or PASTA_DE_SAIDA == "sua_pasta_de_saida_aqui":
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ATENÇÃO: Por favor, configure as variáveis       !!!")
        print("!!! 'PASTA_DE_ENTRADA' e 'PASTA_DE_SAIDA' no topo    !!!")
        print("!!! do script antes de executar.                     !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        # Chama a função principal com as configurações definidas.
        juntar_arquivos_md(PASTA_DE_ENTRADA, PASTA_DE_SAIDA, NOME_DO_ARQUIVO_DE_SAIDA)