# Esse código junta vários arquivos de audio em um só
# python ja.py
import os
import sys
import subprocess

# ==========================================================
# ZONA DE CONFIGURAÇÃO (EDITE APENAS AQUI)
# ==========================================================

# 1. Caminho da pasta onde estão os áudios que você quer juntar
PASTA_ENTRADA = r'E:\KEVYN\150526 Visita Senador Daniel Agrobom\Audios'

# 2. Onde o arquivo final deve ser salvo?
PASTA_SAIDA = r'E:\KEVYN\150526 Visita Senador Daniel Agrobom\Audios'

# 3. Qual o nome final do arquivo que vai ser gerado? (Use .mp3)
NOME_ARQUIVO_FINAL = 'audio das lives - Visita Senador Daniel.mp3'

# ==========================================================

def preparar_sistema():
    """Garante que o motor de áudio está instalado"""
    try:
        import imageio_ffmpeg
    except ImportError:
        print("Instalando motor de áudio necessário...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "imageio-ffmpeg"])
        import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def juntar_audios():
    ffmpeg_exe = preparar_sistema()

    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)

    # Lista arquivos e ordena
    extensoes = ('.mp3', '.wav', '.m4a', '.ogg', '.flac', '.opus')
    arquivos = [f for f in os.listdir(PASTA_ENTRADA) if f.lower().endswith(extensoes)]
    arquivos.sort()

    if not arquivos:
        print(f"Erro: Nenhum áudio encontrado em {PASTA_ENTRADA}")
        return

    print(f"Encontrados {len(arquivos)} arquivos. Iniciando processamento...")

    # Cria lista temporária para o motor de áudio
    lista_path = os.path.join(PASTA_SAIDA, 'temp_lista.txt')
    with open(lista_path, 'w', encoding='utf-8') as f:
        for nome in arquivos:
            caminho_abs = os.path.abspath(os.path.join(PASTA_ENTRADA, nome)).replace('\\', '/')
            f.write(f"file '{caminho_abs}'\n")

    caminho_final = os.path.join(PASTA_SAIDA, NOME_ARQUIVO_FINAL)

    # O COMANDO MÁGICO:
    # -c:a libmp3lame: Converte qualquer áudio estranho para MP3 real
    # -q:a 2: Mantém uma qualidade alta (VBR)
    comando = [
        ffmpeg_exe, '-y', '-f', 'concat', '-safe', '0',
        '-i', lista_path, '-c:a', 'libmp3lame', '-q:a', '2', caminho_final
    ]

    print("Convertendo e juntando... Aguarde um instante...")
    try:
        processo = subprocess.run(comando, capture_output=True, text=True)
        if processo.returncode == 0:
            print(f"\n✅ SUCESSO ABSOLUTO!")
            print(f"Arquivo: {NOME_ARQUIVO_FINAL}")
            print(f"Pasta: {PASTA_SAIDA}")
        else:
            print(f"\n❌ Erro no motor de áudio:")
            print(processo.stderr)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
    finally:
        if os.path.exists(lista_path):
            os.remove(lista_path)

if __name__ == "__main__":
    juntar_audios()