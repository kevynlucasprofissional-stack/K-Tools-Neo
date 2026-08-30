# dhcp_monitor_gui.py
# Monitor DHCP local com GUI CustomTkinter + Scapy
# Use apenas em redes próprias ou com autorização.
#
# Windows:
# 1) Rode o PowerShell/CMD como Administrador.
# 2) Instale o Npcap manualmente: https://npcap.com/
# 3) Execute: python dhcp_monitor_gui.py
#
# O script tenta instalar automaticamente:
# - customtkinter
# - scapy

import csv
import ctypes
import importlib
import os
import platform
import queue
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path


# ============================================================
# Bootstrap de dependências Python
# ============================================================

REQUIRED_PACKAGES = {
    "customtkinter": "customtkinter",
    "scapy": "scapy",
}


def ensure_package(import_name: str, pip_name: str | None = None):
    """
    Importa um pacote. Se não existir, tenta instalar via pip e importar de novo.
    """
    pip_name = pip_name or import_name

    try:
        return importlib.import_module(import_name)
    except ModuleNotFoundError:
        print(f"[setup] Biblioteca ausente: {import_name}. Tentando instalar {pip_name}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade", pip_name]
            )
        except subprocess.CalledProcessError as exc:
            print(f"[erro] Não foi possível instalar {pip_name}.")
            print(exc)
            raise

        return importlib.import_module(import_name)


for module_name, package_name in REQUIRED_PACKAGES.items():
    ensure_package(module_name, package_name)


# Imports após garantir dependências
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from scapy.all import AsyncSniffer, BOOTP, DHCP, Ether, IP, UDP, conf
    from scapy.all import get_if_list
except Exception as exc:
    print("[erro] Scapy foi instalado, mas não conseguiu carregar corretamente.")
    print(exc)
    raise


# Tenta importar listagem detalhada de interfaces no Windows
try:
    from scapy.arch.windows import get_windows_if_list
except Exception:
    get_windows_if_list = None


# ============================================================
# Utilitários
# ============================================================

def is_windows() -> bool:
    return platform.system().lower() == "windows"


def is_admin() -> bool:
    """
    Verifica se o processo está rodando como administrador/root.
    """
    try:
        if is_windows():
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        return os.geteuid() == 0
    except Exception:
        return False


def safe_decode(value):
    """
    Decodifica bytes vindos das opções DHCP sem quebrar em caracteres estranhos.
    """
    if value is None:
        return None

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip("\x00").strip()

    if isinstance(value, (list, tuple)):
        return ", ".join(safe_decode(v) for v in value)

    return str(value)


def mac_from_bootp(packet):
    """
    Tenta extrair MAC pelo BOOTP caso não exista camada Ethernet.
    """
    try:
        bootp = packet[BOOTP]
        hlen = int(getattr(bootp, "hlen", 6) or 6)
        raw = bytes(bootp.chaddr)[:hlen]
        if len(raw) >= 6:
            return ":".join(f"{b:02x}" for b in raw[:6])
    except Exception:
        return None

    return None


def normalize_ip(value):
    if value is None:
        return None

    text = safe_decode(value)
    if not text or text == "0.0.0.0":
        return None

    return text


def now_text():
    return datetime.now().strftime("%d-%m-%Y às %H:%M:%S")


def packet_is_dhcp_like(packet) -> bool:
    """
    Filtro Python complementar. Útil quando o filtro BPF está desligado.
    """
    try:
        if packet.haslayer(DHCP):
            return True

        if packet.haslayer(UDP):
            sport = int(packet[UDP].sport)
            dport = int(packet[UDP].dport)
            return sport in (67, 68) or dport in (67, 68)

    except Exception:
        return False

    return False


def extract_dhcp_info(packet) -> dict:
    """
    Extrai informações úteis do pacote DHCP de maneira defensiva.
    Nem todo pacote DHCP possui hostname, vendor ID ou requested_addr.
    """
    info = {
        "timestamp": now_text(),
        "message_type": None,
        "mac": None,
        "hostname": None,
        "vendor_id": None,
        "requested_ip": None,
        "assigned_ip": None,
        "client_ip": None,
        "server_id": None,
        "src_ip": None,
        "dst_ip": None,
        "summary": None,
        "raw_options": None,
    }

    try:
        info["summary"] = packet.summary()
    except Exception:
        info["summary"] = "Resumo indisponível"

    if packet.haslayer(Ether):
        info["mac"] = safe_decode(packet[Ether].src)

    if not info["mac"]:
        info["mac"] = mac_from_bootp(packet)

    if packet.haslayer(IP):
        info["src_ip"] = normalize_ip(packet[IP].src)
        info["dst_ip"] = normalize_ip(packet[IP].dst)

    if packet.haslayer(BOOTP):
        bootp = packet[BOOTP]
        info["client_ip"] = normalize_ip(getattr(bootp, "ciaddr", None))
        info["assigned_ip"] = normalize_ip(getattr(bootp, "yiaddr", None))

    # DHCP options
    options_as_text = []

    if packet.haslayer(DHCP):
        for item in packet[DHCP].options:
            if not isinstance(item, tuple) or len(item) < 2:
                continue

            label = item[0]
            value = item[1]

            label_text = safe_decode(label)
            value_text = safe_decode(value)
            options_as_text.append(f"{label_text}={value_text}")

            if label == "message-type":
                info["message_type"] = value_text

            elif label == "requested_addr":
                info["requested_ip"] = normalize_ip(value)

            elif label == "hostname":
                info["hostname"] = value_text

            elif label == "vendor_class_id":
                info["vendor_id"] = value_text

            elif label == "server_id":
                info["server_id"] = normalize_ip(value)

    info["raw_options"] = " | ".join(options_as_text) if options_as_text else None

    # Melhor IP principal para exibir
    # DHCP Discover/Request: costuma vir em requested_ip.
    # DHCP Offer/Ack: costuma vir em assigned_ip.
    info["main_ip"] = (
        info["requested_ip"]
        or info["assigned_ip"]
        or info["client_ip"]
        or "não informado"
    )

    return info


def compact_packet_line(info: dict) -> str:
    return (
        f"[{info['timestamp']}] "
        f"Tipo={info.get('message_type') or 'DHCP'} | "
        f"MAC={info.get('mac') or 'não informado'} | "
        f"Host={info.get('hostname') or 'não informado'} | "
        f"Vendor={info.get('vendor_id') or 'não informado'} | "
        f"IP={info.get('main_ip') or 'não informado'}"
    )


# ============================================================
# GUI
# ============================================================

class DHCPMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Monitor DHCP - Scapy + CustomTkinter")
        self.geometry("1100x720")
        self.minsize(920, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.queue = queue.Queue()
        self.sniffer = None
        self.is_sniffing = False
        self.captured_rows = []
        self.iface_map = {}

        self._build_ui()
        self._load_interfaces()
        self._render_environment_status()

        self.after(150, self._drain_queue)

    # --------------------------
    # UI
    # --------------------------

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Monitor DHCP",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.grid(row=0, column=0, padx=16, pady=(12, 2), sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Captura Discover, Offer, Request e Ack na rede local.",
            text_color="#b5b5b5",
        )
        subtitle.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        self.env_label = ctk.CTkLabel(
            header,
            text="Verificando ambiente...",
            anchor="e",
            justify="right",
        )
        self.env_label.grid(row=0, column=1, rowspan=2, padx=16, pady=12, sticky="e")

        controls = ctk.CTkFrame(self)
        controls.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        controls.grid_columnconfigure(1, weight=1)
        controls.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(controls, text="Interface:").grid(
            row=0, column=0, padx=(12, 6), pady=(12, 6), sticky="w"
        )

        self.iface_combo = ctk.CTkComboBox(
            controls,
            values=["Padrão do Scapy"],
            width=420,
        )
        self.iface_combo.set("Padrão do Scapy")
        self.iface_combo.grid(row=0, column=1, padx=6, pady=(12, 6), sticky="ew")

        self.refresh_btn = ctk.CTkButton(
            controls,
            text="Atualizar interfaces",
            command=self._load_interfaces,
            width=150,
        )
        self.refresh_btn.grid(row=0, column=2, padx=6, pady=(12, 6), sticky="w")

        ctk.CTkLabel(controls, text="Filtro BPF:").grid(
            row=1, column=0, padx=(12, 6), pady=6, sticky="w"
        )

        self.filter_entry = ctk.CTkEntry(controls)
        self.filter_entry.insert(0, "udp and (port 67 or port 68)")
        self.filter_entry.grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        self.use_bpf_var = tk.BooleanVar(value=True)
        self.use_bpf_check = ctk.CTkCheckBox(
            controls,
            text="Usar filtro BPF",
            variable=self.use_bpf_var,
        )
        self.use_bpf_check.grid(row=1, column=2, padx=6, pady=6, sticky="w")

        self.show_incomplete_var = tk.BooleanVar(value=True)
        self.show_incomplete_check = ctk.CTkCheckBox(
            controls,
            text="Mostrar pacotes incompletos",
            variable=self.show_incomplete_var,
        )
        self.show_incomplete_check.grid(row=1, column=3, padx=6, pady=6, sticky="w")

        button_bar = ctk.CTkFrame(self)
        button_bar.grid(row=3, column=0, padx=16, pady=(8, 16), sticky="ew")
        button_bar.grid_columnconfigure(6, weight=1)

        self.start_btn = ctk.CTkButton(
            button_bar,
            text="Iniciar captura",
            command=self.start_capture,
            width=140,
        )
        self.start_btn.grid(row=0, column=0, padx=(12, 6), pady=12)

        self.stop_btn = ctk.CTkButton(
            button_bar,
            text="Parar",
            command=self.stop_capture,
            width=100,
            state="disabled",
        )
        self.stop_btn.grid(row=0, column=1, padx=6, pady=12)

        self.clear_btn = ctk.CTkButton(
            button_bar,
            text="Limpar tela",
            command=self.clear_log,
            width=120,
        )
        self.clear_btn.grid(row=0, column=2, padx=6, pady=12)

        self.save_btn = ctk.CTkButton(
            button_bar,
            text="Salvar CSV",
            command=self.save_csv,
            width=120,
        )
        self.save_btn.grid(row=0, column=3, padx=6, pady=12)

        self.copy_btn = ctk.CTkButton(
            button_bar,
            text="Copiar log",
            command=self.copy_log,
            width=120,
        )
        self.copy_btn.grid(row=0, column=4, padx=6, pady=12)

        self.status_label = ctk.CTkLabel(
            button_bar,
            text="Status: parado",
            anchor="e",
            text_color="#b5b5b5",
        )
        self.status_label.grid(row=0, column=6, padx=12, pady=12, sticky="e")

        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=2, column=0, padx=16, pady=8, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(log_frame, wrap="none")
        self.log_text.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")

        self._append_log("Pronto.")
        self._append_log("Dica: no Windows, rode como Administrador e instale o Npcap.")

    def _render_environment_status(self):
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        admin_text = "Administrador: sim" if is_admin() else "Administrador: não"
        os_text = f"Sistema: {platform.system()} {platform.release()}"
        self.env_label.configure(
            text=f"Python {python_ver}\n{os_text}\n{admin_text}"
        )

        if is_windows() and not is_admin():
            self._append_log(
                "Aviso: você não está rodando como Administrador. "
                "A captura pode falhar ou não mostrar pacotes."
            )

    # --------------------------
    # Interfaces
    # --------------------------

    def _load_interfaces(self):
        self.iface_map = {"Padrão do Scapy": None}
        display_values = ["Padrão do Scapy"]

        try:
            if is_windows() and get_windows_if_list:
                interfaces = get_windows_if_list()

                for iface in interfaces:
                    name = iface.get("name") or ""
                    description = iface.get("description") or "Sem descrição"
                    mac = iface.get("mac") or "sem MAC"
                    ips = ", ".join(iface.get("ips") or []) or "sem IP"

                    display = f"{description} | {mac} | {ips}"
                    self.iface_map[display] = name
                    display_values.append(display)

            else:
                interfaces = get_if_list()
                for name in interfaces:
                    self.iface_map[name] = name
                    display_values.append(name)

            self.iface_combo.configure(values=display_values)
            if self.iface_combo.get() not in display_values:
                self.iface_combo.set("Padrão do Scapy")

            self._append_log(f"Interfaces carregadas: {len(display_values) - 1}")

        except Exception as exc:
            self._append_log(f"Erro ao listar interfaces: {exc}")
            self.iface_combo.configure(values=["Padrão do Scapy"])
            self.iface_combo.set("Padrão do Scapy")

    # --------------------------
    # Captura
    # --------------------------

    def start_capture(self):
        if self.is_sniffing:
            return

        selected_display = self.iface_combo.get()
        iface = self.iface_map.get(selected_display)

        bpf_filter = self.filter_entry.get().strip()
        use_bpf = self.use_bpf_var.get()

        if is_windows() and not is_admin():
            proceed = messagebox.askyesno(
                "Permissão de administrador",
                "Você não está rodando como Administrador.\n\n"
                "No Windows, a captura de pacotes costuma precisar de permissão elevada.\n\n"
                "Deseja tentar mesmo assim?"
            )
            if not proceed:
                return

        try:
            conf.use_pcap = True
        except Exception:
            pass

        self._append_log("")
        self._append_log("Iniciando captura...")
        self._append_log(f"Interface: {selected_display}")
        self._append_log(f"Filtro BPF: {bpf_filter if use_bpf else 'desativado'}")

        try:
            self.sniffer = AsyncSniffer(
                iface=iface,
                filter=bpf_filter if use_bpf and bpf_filter else None,
                lfilter=packet_is_dhcp_like,
                prn=self._on_packet,
                store=False,
            )

            self.sniffer.start()
            self.is_sniffing = True

            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.status_label.configure(text="Status: capturando...")

        except Exception as exc:
            self.is_sniffing = False
            self.sniffer = None
            self._append_log("Erro ao iniciar captura.")
            self._append_log(str(exc))
            self._append_log(traceback.format_exc())

            if is_windows():
                self._append_log(
                    "Possível causa no Windows: Npcap ausente, interface errada "
                    "ou script sem permissão de Administrador."
                )

            messagebox.showerror(
                "Erro ao iniciar captura",
                f"Não foi possível iniciar a captura:\n\n{exc}"
            )

    def stop_capture(self):
        if not self.is_sniffing:
            return

        self._append_log("Parando captura...")

        try:
            if self.sniffer:
                self.sniffer.stop()
        except Exception as exc:
            self._append_log(f"Aviso ao parar sniffer: {exc}")

        self.sniffer = None
        self.is_sniffing = False

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="Status: parado")
        self._append_log("Captura parada.")

    def _on_packet(self, packet):
        """
        Chamado pela thread do Scapy. Não atualiza GUI diretamente.
        """
        try:
            info = extract_dhcp_info(packet)

            has_core_info = bool(
                info.get("mac")
                or info.get("hostname")
                or info.get("requested_ip")
                or info.get("assigned_ip")
                or info.get("message_type")
            )

            if not self.show_incomplete_var.get() and not has_core_info:
                return

            line = compact_packet_line(info)

            self.captured_rows.append(info)
            self.queue.put(("packet", line, info))

        except Exception as exc:
            self.queue.put(("error", f"Erro ao processar pacote: {exc}", None))

    def _drain_queue(self):
        try:
            while True:
                kind, message, info = self.queue.get_nowait()

                if kind == "packet":
                    self._append_log(message)

                    if info and info.get("raw_options"):
                        self._append_log(f"    Opções: {info['raw_options']}")

                elif kind == "error":
                    self._append_log(message)

        except queue.Empty:
            pass

        self.after(150, self._drain_queue)

    # --------------------------
    # Log e CSV
    # --------------------------

    def _append_log(self, text: str):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def clear_log(self):
        self.log_text.delete("1.0", "end")
        self.captured_rows.clear()
        self._append_log("Log limpo.")

    def copy_log(self):
        content = self.log_text.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(content)
        self._append_log("Log copiado para a área de transferência.")

    def save_csv(self):
        if not self.captured_rows:
            messagebox.showinfo("Sem dados", "Ainda não há pacotes capturados para salvar.")
            return

        default_name = f"dhcp_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = filedialog.asksaveasfilename(
            title="Salvar CSV",
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        )

        if not filepath:
            return

        fieldnames = [
            "timestamp",
            "message_type",
            "mac",
            "hostname",
            "vendor_id",
            "requested_ip",
            "assigned_ip",
            "client_ip",
            "server_id",
            "src_ip",
            "dst_ip",
            "main_ip",
            "summary",
            "raw_options",
        ]

        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for row in self.captured_rows:
                    writer.writerow({key: row.get(key) for key in fieldnames})

            self._append_log(f"CSV salvo em: {filepath}")
            messagebox.showinfo("CSV salvo", f"Arquivo salvo com sucesso:\n{filepath}")

        except Exception as exc:
            self._append_log(f"Erro ao salvar CSV: {exc}")
            messagebox.showerror("Erro ao salvar CSV", str(exc))

    def on_closing(self):
        if self.is_sniffing:
            self.stop_capture()
        self.destroy()


def main():
    app = DHCPMonitorApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
