import sys
import subprocess
import importlib.util

def instalar_dependencias():
    """Verifica e instala automaticamente dependências ausentes."""
    # O moviepy é a principal biblioteca para processamento de vídeo
    if importlib.util.find_spec("moviepy") is None:
        print("=" * 70)
        print("A biblioteca 'moviepy' não foi detectada no seu ambiente Python.")
        print("Iniciando a instalação automática via pip...")
        print("Por favor, aguarde alguns instantes...")
        print("=" * 70)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "moviepy"])
            print("\nInstalação realizada com sucesso!\n")
        except Exception as e:
            print(f"\nNão foi possível instalar a biblioteca 'moviepy' automaticamente: {e}")
            print("Por favor, tente instalar manualmente abrindo o seu terminal e digitando:")
            print("pip install moviepy")
            input("\nPressione Enter para sair...")
            sys.exit(1)

# Executa a verificação/instalação antes de inicializar o restante do programa
instalar_dependencias()

# Importações do sistema e interface gráfica
import os
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Importação dos componentes de vídeo com suporte a diferentes versões do moviepy
try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
except ImportError:
    try:
        from moviepy import VideoFileClip, concatenate_videoclips
    except ImportError:
        VideoFileClip = None
        concatenate_videoclips = None


class VideoMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unificador de Vídeos Sequenciais")
        self.root.geometry("650x500")
        self.root.minsize(600, 450)
        
        # Lista para armazenar o caminho completo de cada arquivo de vídeo
        self.video_list = []
        
        # Controle de estado para processos ativos
        self.is_processing = False
        
        self.create_widgets()
        
        # Intercepta a tentativa de fechamento da janela para gerenciar o processo
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Frame de container principal
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título principal
        title_label = ttk.Label(
            main_frame, 
            text="Unificador de Vídeos", 
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(pady=(0, 5))
        
        # Descrição/Instrução breve
        desc_label = ttk.Label(
            main_frame, 
            text="Selecione arquivos isolados ou uma pasta inteira. O programa organizará os arquivos automaticamente em ordem de sequência antes de unificá-los.",
            font=("Helvetica", 9),
            wraplength=550,
            justify=tk.CENTER
        )
        desc_label.pack(pady=(0, 15))
        
        # Frame superior para os botões de controle de arquivos
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_select_files = ttk.Button(
            btn_frame, 
            text="Selecionar Vídeos Individuais", 
            command=self.select_files
        )
        self.btn_select_files.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.btn_select_folder = ttk.Button(
            btn_frame, 
            text="Selecionar Pasta de Vídeos", 
            command=self.select_folder
        )
        self.btn_select_folder.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.btn_clear = ttk.Button(
            btn_frame, 
            text="Limpar Fila", 
            command=self.clear_list,
            state=tk.DISABLED
        )
        self.btn_clear.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Frame central contendo a Lista de arquivos e as barras de rolagem
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar_y.set, 
            xscrollcommand=scrollbar_x.set,
            font=("Consolas", 10),
            selectmode=tk.SINGLE,
            activestyle='none',
            bg="#fafafa",
            fg="#333333",
            highlightthickness=1,
            highlightcolor="#ccc"
        )
        self.listbox.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_y.config(command=self.listbox.yview)
        scrollbar_x.config(command=self.listbox.xview)
        
        # Label informativo com contador
        self.info_label = ttk.Label(main_frame, text="Nenhum vídeo carregado.", font=("Helvetica", 9, "italic"))
        self.info_label.pack(pady=5)
        
        # Barra de progresso visual indeterminado
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Label de status das operações
        self.status_label = ttk.Label(
            main_frame, 
            text="Pronto", 
            font=("Helvetica", 10, "bold"),
            foreground="gray"
        )
        self.status_label.pack(pady=5)
        
        # Botão final de processamento
        self.btn_merge = ttk.Button(
            main_frame, 
            text="Juntar Vídeos e Salvar", 
            command=self.start_merge_process,
            state=tk.DISABLED
        )
        self.btn_merge.pack(fill=tk.X, pady=(10, 0))

    def select_files(self):
        # Abre caixa de diálogo para seleção de múltiplos arquivos
        files = filedialog.askopenfilenames(
            title="Selecione os vídeos para juntar",
            filetypes=[
                ("Arquivos de Vídeo", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"),
                ("Todos os arquivos", "*.*")
            ]
        )
        if files:
            for file in files:
                if file not in self.video_list:
                    self.video_list.append(file)
            self.sort_and_display_videos()

    def select_folder(self):
        # Abre caixa de diálogo para seleção de um diretório
        folder = filedialog.askdirectory(title="Selecione a pasta com os vídeos")
        if folder:
            valid_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')
            files = [
                os.path.join(folder, f) for f in os.listdir(folder)
                if f.lower().endswith(valid_extensions)
            ]
            if not files:
                messagebox.showwarning("Aviso", "Nenhum arquivo de vídeo compatível foi encontrado na pasta.")
                return
            
            # Substitui a fila atual para evitar mesclagem acidental de diretórios diferentes
            self.video_list = files
            self.sort_and_display_videos()

    def clear_list(self):
        self.video_list = []
        self.sort_and_display_videos()
        self.status_label.config(text="Fila limpa", foreground="gray")

    def natural_sort_key(self, path):
        filename = os.path.basename(path)
        # Função para ordenação natural: separa blocos de números de strings ordinárias.
        # Assim, garante-se que "2_video" venha antes de "10_video" (ao invés de ordem lexicográfica pura)
        # e funciona para caracteres alfabéticos (A, B, C...)
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', filename)]

    def sort_and_display_videos(self):
        # Ordenação natural da lista de arquivos
        self.video_list.sort(key=self.natural_sort_key)
        
        # Atualização do componente visual de exibição
        self.listbox.delete(0, tk.END)
        for idx, video in enumerate(self.video_list, start=1):
            filename = os.path.basename(video)
            self.listbox.insert(tk.END, f"[{idx:02d}] {filename}")
        
        count = len(self.video_list)
        if count > 0:
            self.info_label.config(text=f"{count} vídeo(s) na fila para processamento.")
            self.btn_clear.config(state=tk.NORMAL)
            self.btn_merge.config(state=tk.NORMAL)
        else:
            self.info_label.config(text="Nenhum vídeo carregado.")
            self.btn_clear.config(state=tk.DISABLED)
            self.btn_merge.config(state=tk.DISABLED)

    def start_merge_process(self):
        if not self.video_list:
            return
        
        if VideoFileClip is None or concatenate_videoclips is None:
            messagebox.showerror("Erro", "A biblioteca 'moviepy' apresentou problemas no carregamento. Reinicie o script.")
            return

        # Solicita ao usuário o local e o nome do arquivo resultante
        output_path = filedialog.asksaveasfilename(
            title="Salvar vídeo final como",
            defaultextension=".mp4",
            filetypes=[("Vídeo MP4", "*.mp4")]
        )
        if not output_path:
            return
        
        # Configura a interface para estado de execução ativa
        self.is_processing = True
        self.toggle_ui(state=tk.DISABLED)
        self.status_label.config(text="Processando vídeos... Aguarde por favor.", foreground="blue")
        self.progress.start(10)

        # Inicia o processamento pesado em uma thread paralela, prevenindo travamentos do Tkinter
        threading.Thread(target=self.merge_videos, args=(output_path,), daemon=True).start()

    def merge_videos(self, output_path):
        clips = []
        try:
            # Carrega cada elemento individual na memória
            for path in self.video_list:
                clips.append(VideoFileClip(path))
            
            # Compara as dimensões (resolução) dos arquivos
            sizes = [clip.size for clip in clips]
            all_same_size = all(size == sizes[0] for size in sizes)
            
            # Se todas as resoluções forem idênticas, usa o método 'chain' (muito mais rápido)
            # Se houver resoluções ou orientações mistas, recorre ao 'compose' para prevenir erros
            if all_same_size:
                final_clip = concatenate_videoclips(clips, method="chain")
            else:
                final_clip = concatenate_videoclips(clips, method="compose")
            
            # Escreve o arquivo final no disco
            final_clip.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                logger=None  # Desativa logs redundantes no terminal
            )
            
            # Fecha todos os objetos de mídia para liberação do sistema de arquivos
            final_clip.close()
            for clip in clips:
                clip.close()
                
            self.root.after(0, self.on_success, output_path)
            
        except Exception as e:
            # Garante liberação de recursos em caso de falhas
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            self.root.after(0, self.on_failure, str(e))

    def on_success(self, output_path):
        self.is_processing = False
        self.progress.stop()
        self.toggle_ui(state=tk.NORMAL)
        self.status_label.config(text="Processamento concluído com sucesso!", foreground="green")
        messagebox.showinfo("Sucesso", f"Os vídeos foram combinados!\n\nSalvo em:\n{output_path}")

    def on_failure(self, error_msg):
        self.is_processing = False
        self.progress.stop()
        self.toggle_ui(state=tk.NORMAL)
        self.status_label.config(text="Erro no processamento.", foreground="red")
        messagebox.showerror("Erro de Processamento", f"Ocorreu uma falha ao tentar unificar os vídeos:\n\n{error_msg}")

    def toggle_ui(self, state):
        self.btn_select_files.config(state=state)
        self.btn_select_folder.config(state=state)
        self.btn_clear.config(state=state)
        self.btn_merge.config(state=state)

    def on_closing(self):
        if self.is_processing:
            if messagebox.askokcancel("Sair", "O processamento ainda está sendo executado em segundo plano. Deseja realmente interromper e sair?"):
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoMergerApp(root)
    root.mainloop()