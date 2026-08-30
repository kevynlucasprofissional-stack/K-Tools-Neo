import os
import sys
import subprocess
import shutil

# python CA.py
# Esse script serve para cortar audios em partes iguais
# ==============================================================================
# FUNÇÃO DE INSTALAÇÃO AUTOMÁTICA DE BIBLIOTECAS E FFMPEG
# ==============================================================================
def instalar_dependencias():
    # 1. Verifica e instala a biblioteca pydub
    try:
        import pydub
    except ImportError:
        print("Biblioteca 'pydub' não encontrada. Instalando automaticamente...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pydub"])
        print("Pydub instalado com sucesso!\n")

    # 2. Correção para Python 3.13+ (audioop-lts)
    try:
        import audioop
    except ImportError:
        try:
            import audioop_lts
        except ImportError:
            print("⚠️ Python 3.13+ detectado. Instalando biblioteca de compatibilidade 'audioop-lts'...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "audioop-lts"])
            print("Compatibilidade de áudio configurada!\n")

    # 3. Verifica se o FFmpeg e FFprobe já estão instalados no computador
    tem_ffmpeg = shutil.which("ffmpeg") is not None
    tem_ffprobe = shutil.which("ffprobe") is not None

    if tem_ffmpeg and tem_ffprobe:
        pass # Já instalado e configurado!
    else:
        print("⚠️ FFmpeg não encontrado no sistema. Verificando 'static-ffmpeg'...")
        try:
            import static_ffmpeg
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "static-ffmpeg"])
            import static_ffmpeg
        
        # Injeta o ffmpeg baixado no script atual
        static_ffmpeg.add_paths()

# Roda a verificação e instalação ANTES de iniciar a ferramenta principal
instalar_dependencias()
from pydub import AudioSegment

# ==============================================================================
# ⚙️ ZONA DE CONFIGURAÇÃO
# ==============================================================================

# 1. Pasta onde o arquivo original está. 
PASTA_ORIGEM = r"E:\KEVYN\150526 Visita Senador Daniel Agrobom\Audios"

# 2. Nome do arquivo de áudio original (com a extensão)
NOME_ARQUIVO_ORIGEM = "audio das lives - Visita Senador Daniel.mp3"

# 3. Pasta onde os áudios cortados serão salvos
PASTA_DESTINO = r"E:\KEVYN\150526 Visita Senador Daniel Agrobom\Audios"

# 4. Em quantas partes IGUAIS o áudio deve ser cortado?
NUMERO_DE_PARTES = 3

# 5. Formato de saída desejado para os áudios cortados (ex: 'mp3', 'wav', 'ogg', 'm4a', 'flac')
FORMATO_SAIDA = "m4a"

# ==============================================================================
# 🚀 CÓDIGO PRINCIPAL
# ==============================================================================

def cortar_audio():
    caminho_completo_origem = os.path.join(PASTA_ORIGEM, NOME_ARQUIVO_ORIGEM)
    
    # Verifica se o arquivo existe
    if not os.path.exists(caminho_completo_origem):
        print(f"ERRO: O arquivo '{caminho_completo_origem}' não foi encontrado.")
        print("Verifique se a pasta e o nome do arquivo na Zona de Configuração estão corretos.")
        return

    # Cria a pasta de destino se ela não existir
    if not os.path.exists(PASTA_DESTINO):
        os.makedirs(PASTA_DESTINO)

    print(f"\nCarregando o áudio: {NOME_ARQUIVO_ORIGEM} (Isso pode levar alguns segundos...)")
    
    try:
        audio = AudioSegment.from_file(caminho_completo_origem)
    except Exception as e:
        print(f"ERRO ao carregar o áudio: {e}")
        return

    duracao_total_ms = len(audio)
    tamanho_do_corte_ms = duracao_total_ms // NUMERO_DE_PARTES
    
    nome_base = os.path.splitext(NOME_ARQUIVO_ORIGEM)[0]

    print(f"Iniciando o corte em {NUMERO_DE_PARTES} partes iguais...\n")
    
    for i in range(NUMERO_DE_PARTES):
        tempo_inicio = i * tamanho_do_corte_ms
        
        # Garante que a última parte pegue até o exato final do áudio
        if i == NUMERO_DE_PARTES - 1:
            tempo_fim = duracao_total_ms
        else:
            tempo_fim = (i + 1) * tamanho_do_corte_ms

        # Corta o pedaço do áudio
        pedaco_audio = audio[tempo_inicio:tempo_fim]
        
        # Formata o nome do arquivo
        extensao_limpa = FORMATO_SAIDA.lower().replace('.', '')
        nome_arquivo_saida = f"{nome_base}_parte_{i+1}_de_{NUMERO_DE_PARTES}.{extensao_limpa}"
        caminho_saida = os.path.join(PASTA_DESTINO, nome_arquivo_saida)
        
        print(f"Exportando: {nome_arquivo_saida}...")
        
        # ======================================================================
        # 💡 TRADUTOR DE FORMATOS PARA O FFMPEG
        # ======================================================================
        formato_ffmpeg = extensao_limpa
        parametros = {}
        
        if formato_ffmpeg == "m4a":
            formato_ffmpeg = "ipod"      # Nome interno do ffmpeg para arquivos m4a
            parametros["codec"] = "aac"  # Codec de áudio correto para m4a
        # ======================================================================
        
        # Exporta o arquivo no formato escolhido com os parâmetros ajustados
        pedaco_audio.export(caminho_saida, format=formato_ffmpeg, **parametros)

    print("\n✅ Processo concluído com sucesso!")
    print(f"Os áudios foram salvos na pasta: '{os.path.abspath(PASTA_DESTINO)}'")

if __name__ == "__main__":
    cortar_audio()