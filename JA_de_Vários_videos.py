import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# python JA_de_Vários_videos.py
# ==========================================
# INSTALADOR AUTOMÁTICO DE DEPENDÊNCIAS
# ==========================================
def install_dependencies():
    try:
        import moviepy
    except ImportError:
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showinfo("Instalação Necessária", 
                            "A biblioteca de processamento de vídeo ('moviepy') não foi encontrada.\n\n"
                            "O programa fará o download e instalação automaticamente agora. Isso pode levar alguns minutos. Clique em OK e aguarde.")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "moviepy"])
            messagebox.showinfo("Sucesso", "Biblioteca instalada com sucesso! O programa vai iniciar agora.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao instalar a biblioteca automaticamente.\nErro: {e}")
            sys.exit(1)
        temp_root.destroy()

install_dependencies()

# ==========================================
# IMPORTAÇÃO CORRIGIDA PARA MOVIEPY 2.X+
# ==========================================
try:
    # Tenta importar do jeito novo (MoviePy 2.0+)
    from moviepy import VideoFileClip, concatenate_audioclips
except ImportError:
    # Fallback para versões mais antigas (MoviePy 1.x)
    from moviepy.editor import VideoFileClip, concatenate_audioclips

# ==========================================
# INTERFACE GRÁFICA (GUI) E LÓGICA PRINCIPAL
# ==========================================
class AudioExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extrator e Unificador de Áudios")
        self.root.geometry("550x300")
        self.root.resizable(False, False)

        # Variáveis
        self.input_folder = tk.StringVar()
        self.output_file = tk.StringVar()

        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("TLabel", font=("Arial", 10))

        # Frame principal
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Seleção da pasta de origem
        ttk.Label(frame, text="1. Pasta com os vídeos:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.ent_input = ttk.Entry(frame, textvariable=self.input_folder, width=45, state='readonly')
        self.ent_input.grid(row=1, column=0, sticky=tk.W, pady=(0, 15), padx=(0, 10))
        ttk.Button(frame, text="Procurar...", command=self.browse_input).grid(row=1, column=1, pady=(0, 15))

        # Seleção do arquivo de destino
        ttk.Label(frame, text="2. Onde salvar e formato do áudio final:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.ent_output = ttk.Entry(frame, textvariable=self.output_file, width=45, state='readonly')
        self.ent_output.grid(row=3, column=0, sticky=tk.W, pady=(0, 15), padx=(0, 10))
        ttk.Button(frame, text="Salvar como...", command=self.browse_output).grid(row=3, column=1, pady=(0, 15))

        # Status
        self.lbl_status = ttk.Label(frame, text="Pronto para iniciar.", foreground="blue")
        self.lbl_status.grid(row=4, column=0, columnspan=2, pady=(10, 15), sticky=tk.W)

        # Botão de Iniciar
        self.btn_processar = ttk.Button(frame, text="Extrair e Unir Áudios", command=self.start_processing)
        self.btn_processar.grid(row=5, column=0, columnspan=2, ipadx=20, ipady=5)

    def browse_input(self):
        folder = filedialog.askdirectory(title="Selecione a pasta com os vídeos")
        if folder:
            self.input_folder.set(folder)

    def browse_output(self):
        filetypes = [
            ("Áudio MP3", "*.mp3"),
            ("Áudio WAV", "*.wav")
        ]
        filepath = filedialog.asksaveasfilename(
            title="Salvar áudio unificado como...",
            defaultextension=".mp3",
            filetypes=filetypes
        )
        if filepath:
            self.output_file.set(filepath)

    def update_status(self, msg, color="blue"):
        self.root.after(0, lambda: self.lbl_status.config(text=msg, foreground=color))

    def start_processing(self):
        if not self.input_folder.get():
            messagebox.showwarning("Aviso", "Por favor, selecione a pasta com os vídeos.")
            return
        if not self.output_file.get():
            messagebox.showwarning("Aviso", "Por favor, escolha onde salvar o áudio final.")
            return

        self.btn_processar.config(state=tk.DISABLED)
        thread = threading.Thread(target=self.process_videos)
        thread.start()

    def process_videos(self):
        folder = self.input_folder.get()
        output_path = self.output_file.get()
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv')

        try:
            self.update_status("Procurando vídeos na pasta...")
            
            # Pega todos os vídeos da pasta e ordena em ordem alfabética
            files = [f for f in os.listdir(folder) if f.lower().endswith(video_extensions)]
            files.sort()

            if not files:
                self.update_status("Nenhum vídeo encontrado na pasta selecionada!", "red")
                self.root.after(0, lambda: self.btn_processar.config(state=tk.NORMAL))
                return

            video_clips = []
            audio_clips = []

            for i, filename in enumerate(files):
                self.update_status(f"Extraindo áudio do vídeo {i+1} de {len(files)}...")
                video_path = os.path.join(folder, filename)
                
                # Carrega o vídeo
                clip = VideoFileClip(video_path)
                video_clips.append(clip)
                
                # Verifica se há áudio
                if clip.audio is not None:
                    audio_clips.append(clip.audio)
                else:
                    print(f"Vídeo ignorado (sem áudio): {filename}")

            if not audio_clips:
                self.update_status("Nenhum dos vídeos possui faixas de áudio!", "red")
                return

            self.update_status("Unindo todos os áudios (Isso pode demorar um pouco)...", "orange")
            final_audio = concatenate_audioclips(audio_clips)

            self.update_status("Salvando arquivo final (Codificando áudio)...", "orange")
            final_audio.write_audiofile(output_path, logger=None)

            self.update_status("Processo concluído com sucesso!", "green")
            self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"Áudio gerado com sucesso em:\n{output_path}"))

            # Libera a memória fechando os arquivos
            try:
                final_audio.close()
                for ac in audio_clips:
                    ac.close()
                for vc in video_clips:
                    vc.close()
            except AttributeError:
                pass # Ignora caso a versão não exija/suporte fechar

        except Exception as e:
            self.update_status("Ocorreu um erro durante o processo.", "red")
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro crítico:\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.btn_processar.config(state=tk.NORMAL))

# Inicialização do Aplicativo
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioExtractorApp(root)
    root.mainloop()