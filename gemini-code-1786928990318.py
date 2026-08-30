import sys
import subprocess
import os

# ==========================================
# 1. SISTEMA DE AUTO-INSTALAÇÃO DE DEPENDÊNCIAS
# ==========================================
def install_requirements():
    try:
        import customtkinter
    except ImportError:
        print("Biblioteca 'customtkinter' não encontrada. Instalando automaticamente...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
            print("Instalação concluída com sucesso!")
        except Exception as e:
            print(f"Erro ao instalar dependências: {e}")
            sys.exit(1)

# Executa a verificação antes de iniciar a interface
install_requirements()

# Agora podemos importar com segurança
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading

# ==========================================
# 2. LÓGICA DO APLICATIVO E INTERFACE (GUI)
# ==========================================
class FileSplitterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.title("Divisor Inteligente de TXT")
        self.geometry("550x420")
        self.resizable(False, False)
        
        # Tema e Cores (UX/UI Moderna)
        ctk.set_appearance_mode("dark")  # Modo escuro
        ctk.set_default_color_theme("blue")

        self.filepath = None

        self.build_ui()

    def build_ui(self):
        # Título
        self.lbl_title = ctk.CTkLabel(self, text="Divisor de Arquivos de Texto", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_title.pack(pady=(20, 5))

        self.lbl_subtitle = ctk.CTkLabel(self, text="Separe arquivos grandes em partes de tamanhos iguais", text_color="gray", font=ctk.CTkFont(size=12))
        self.lbl_subtitle.pack(pady=(0, 20))

        # Seleção de Arquivo
        self.frame_file = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_file.pack(padx=20, fill="x", pady=10)

        self.entry_file = ctk.CTkEntry(self.frame_file, placeholder_text="Selecione um arquivo .txt...", state="disabled")
        self.entry_file.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self.btn_browse = ctk.CTkButton(self.frame_file, text="Procurar Arquivo", command=self.browse_file, width=120)
        self.btn_browse.pack(side="right")

        # Configuração de Partes
        self.frame_parts = ctk.CTkFrame(self)
        self.frame_parts.pack(padx=20, fill="x", pady=15)

        self.lbl_parts = ctk.CTkLabel(self.frame_parts, text="Número de partes para dividir:", font=ctk.CTkFont(size=14))
        self.lbl_parts.pack(pady=(15, 5))

        self.slider_parts = ctk.CTkSlider(self.frame_parts, from_=2, to=50, number_of_steps=48, command=self.update_slider_label)
        self.slider_parts.pack(padx=20, pady=5, fill="x")
        self.slider_parts.set(2) # Valor padrão

        self.lbl_slider_val = ctk.CTkLabel(self.frame_parts, text="2 partes", font=ctk.CTkFont(size=16, weight="bold"), text_color="#3B8ED0")
        self.lbl_slider_val.pack(pady=(0, 15))

        # Progresso
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate")
        self.progress_bar.pack(padx=20, fill="x", pady=15)
        self.progress_bar.set(0)

        self.lbl_status = ctk.CTkLabel(self, text="Aguardando arquivo...", text_color="gray")
        self.lbl_status.pack(pady=(0, 10))

        # Botão de Ação
        self.btn_split = ctk.CTkButton(self, text="Dividir Arquivo Agora", height=40, font=ctk.CTkFont(size=15, weight="bold"), command=self.start_split_thread)
        self.btn_split.pack(padx=20, fill="x", pady=(0, 20))

    def update_slider_label(self, value):
        parts = int(value)
        self.lbl_slider_val.configure(text=f"{parts} partes")

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Selecione o arquivo de texto",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        if filepath:
            self.filepath = filepath
            # Atualiza o campo visual
            self.entry_file.configure(state="normal")
            self.entry_file.delete(0, "end")
            self.entry_file.insert(0, self.filepath)
            self.entry_file.configure(state="disabled")
            
            # Atualiza status
            tamanho_mb = os.path.getsize(filepath) / (1024 * 1024)
            self.lbl_status.configure(text=f"Arquivo carregado: {tamanho_mb:.2f} MB")

    def start_split_thread(self):
        if not self.filepath:
            messagebox.showwarning("Aviso", "Por favor, selecione um arquivo primeiro.")
            return
        if not os.path.exists(self.filepath):
            messagebox.showerror("Erro", "O arquivo selecionado não foi encontrado.")
            return

        # Desativa os botões para evitar cliques duplos durante o processamento
        self.btn_split.configure(state="disabled", text="Processando...")
        self.btn_browse.configure(state="disabled")
        self.slider_parts.configure(state="disabled")
        self.progress_bar.set(0)

        # Roda o processamento em uma thread separada para não travar a UI
        num_parts = int(self.slider_parts.get())
        thread = threading.Thread(target=self.split_logic, args=(self.filepath, num_parts))
        thread.start()

    def split_logic(self, filepath, num_parts):
        try:
            file_size = os.path.getsize(filepath)
            target_chunk_size = file_size / num_parts
            
            base_name, ext = os.path.splitext(filepath)
            
            self.lbl_status.configure(text="Lendo arquivo original...")

            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i in range(num_parts):
                    out_name = f"{base_name}_parte{i+1}{ext}"
                    current_chunk_size = 0
                    
                    self.lbl_status.configure(text=f"Gerando parte {i+1} de {num_parts}...")
                    
                    with open(out_name, 'w', encoding='utf-8') as out:
                        for line in f:
                            out.write(line)
                            current_chunk_size += len(line.encode('utf-8'))
                            
                            # Se atingiu o tamanho ideal e não é a última parte, quebra para o próximo arquivo
                            if current_chunk_size >= target_chunk_size and i < num_parts - 1:
                                break
                    
                    # Atualiza a barra de progresso
                    progress = (i + 1) / num_parts
                    self.progress_bar.set(progress)

            self.lbl_status.configure(text="Divisão concluída com sucesso!", text_color="#47e10c")
            messagebox.showinfo("Sucesso", f"O arquivo foi dividido em {num_parts} partes iguais e salvo na mesma pasta do original.")

        except Exception as e:
            self.lbl_status.configure(text="Erro ao dividir arquivo.", text_color="red")
            messagebox.showerror("Erro", f"Ocorreu um erro durante a divisão:\n{str(e)}")
        
        finally:
            # Restaura a interface
            self.btn_split.configure(state="normal", text="Dividir Arquivo Agora")
            self.btn_browse.configure(state="normal")
            self.slider_parts.configure(state="normal")

# ==========================================
# 3. INICIA A APLICAÇÃO
# ==========================================
if __name__ == "__main__":
    app = FileSplitterApp()
    app.mainloop()