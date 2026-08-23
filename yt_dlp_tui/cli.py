import argparse
import os
import re
import sys

from .downloader import download_media, smart_download, fetch_search_results
from .errors import ErrorKind, classify_failure, technical_summary
from .auth_cache import refresh_cookie_interactive
from .diagnostics.context import RunContext
from .diagnostics.logger import DiagnosticLogger
from .diagnostics.reporter import DiagnosticReporter
import atexit
import traceback


def _select_output_folder():
    """Ask the user where this run should save downloads.

    The choice is intentionally session-only: it is never persisted and there is
    no fallback/default download directory.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as e:
        print(f"  ✗ erro » seletor de pasta indisponível: {e}")
        return None

    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        root.update_idletasks()
        selected = filedialog.askdirectory(
            parent=root,
            title="Selecione a pasta onde os arquivos serão salvos",
            mustexist=True,
        )
        return os.path.abspath(selected) if selected else None
    except Exception as e:
        print(f"  ✗ erro » não foi possível abrir o seletor de pasta: {e}")
        return None
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


def _format_duration(seconds):
    if not seconds:
        return "?:??"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _quality_label(quality):
    return "best" if str(quality).lower() == "best" else f"{quality}p"


def _rename_file(filepath):
    new_name = input("  novo nome > ").strip()
    if not new_name:
        return
    # Rename is filename-only.  Never allow path separators to move a download
    # outside the directory selected for this run.
    if new_name in {".", ".."} or os.path.basename(new_name) != new_name or any(sep and sep in new_name for sep in (os.sep, os.altsep)):
        print("  ✗ nome inválido » informe apenas o nome do arquivo, sem pastas")
        return
    ext = os.path.splitext(filepath)[1]
    new_path = os.path.join(os.path.dirname(filepath), new_name + ext)
    try:
        os.rename(filepath, new_path)
        print(f"  salvo como » {new_name}{ext}")
    except OSError:
        print("  ✗ erro » não foi possível renomear o arquivo")


def _is_playlist_url(url):
    return "list=" in str(url).lower()


def interactive_mode(target):
    if not target:
        print("  ✗ nenhuma pasta de download foi selecionada")
        return

    os.system("cls" if os.name == "nt" else "clear")

    fmt = "audio"
    q_video = "1080"
    rename = False

    header = r"""
__   _______      ____  _     ____    _____ _   _ ___
\ \ / /_   _|    |  _ \| |   |  _ \  |_   _| | | |_ _|
 \ V /  | | _____| | | | |   | |_) |   | | | | | || |
  | |   | ||_____| |_| | |___|  __/    | | | |_| || |
  |_|   |_|      |____/|_____|_|       |_|  \___/|___|
"""
    print(header)
    print(f"  destino » {target}")
    print("  entrada » [link], [audio/video], [res], [?] ou [q] para sair")
    print("  " + "─" * 55)

    while True:
        try:
            curr_mode = "audio" if fmt == "audio" else f"video:{_quality_label(q_video)}"
            rename_tag = " +rename" if rename else ""
            prompt = f"\n  link ({curr_mode}{rename_tag}) > "
            url = input(prompt).strip()

            if not url:
                continue
            if url.lower() in ["exit", "quit", "q"]:
                break

            if url == "?":
                print("\n  [ comandos ]")
                print("  audio, video : alternar modo")
                print("  res          : alterar resolução do vídeo")
                print("  rename       : ativar/desativar renomeação")
                print("  s:<busca>    : buscar e baixar o primeiro resultado")
                print("  s3:<busca>   : buscar e escolher entre 3 resultados")
                print("  s5:<busca>   : buscar e escolher entre 5 resultados")
                print("  cache        : importar um novo cache/cookies.txt do YouTube")
                print("  open         : abrir a pasta desta execução")
                print("  <arquivo>.txt: baixar links listados no arquivo")
                print("  q            : sair")
                continue

            if url.lower() == "cache":
                refresh_cookie_interactive(manual=True)
                continue

            if url.lower() == "open":
                os.startfile(target)
                print("  abrindo pasta...")
                continue

            m = re.match(r"^s(\d*):", url, re.IGNORECASE)
            if m:
                count = int(m.group(1)) if m.group(1) else 1
                query = url[m.end():].strip()
                if not query:
                    continue
                print(f"  buscando: {query}")
                if count <= 1:
                    files = smart_download(
                        f"ytsearch1:{query}",
                        output_path=target,
                        file_format=fmt,
                        quality="best" if fmt == "audio" else q_video,
                        auth_refresh_callback=refresh_cookie_interactive,
                    )
                else:
                    results = fetch_search_results(query, count, auth_refresh_callback=refresh_cookie_interactive)
                    if not results:
                        print("  ✗ nenhum resultado encontrado")
                        continue
                    for i, r in enumerate(results, 1):
                        t = (r["title"][:50] + "..") if len(r["title"]) > 50 else r["title"]
                        ch = (r["uploader"][:20] + "..") if len(r["uploader"]) > 20 else r["uploader"]
                        print(f"  {i}. {t} [{_format_duration(r['duration'])} | {ch}]")
                    sel = input(f"  escolha [1-{len(results)}] ou ENTER para cancelar > ").strip()
                    if not sel or not sel.isdigit() or not (1 <= int(sel) <= len(results)):
                        continue
                    chosen = results[int(sel) - 1]
                    files = smart_download(
                        f"https://www.youtube.com/watch?v={chosen['id']}",
                        output_path=target,
                        file_format=fmt,
                        quality="best" if fmt == "audio" else q_video,
                        auth_refresh_callback=refresh_cookie_interactive,
                    )
                if rename and len(files) == 1:
                    _rename_file(files[0])
                continue

            if url.lower() == "rename":
                rename = not rename
                print(f"  renomear {'ativado' if rename else 'desativado'}")
                continue

            if url.lower() == "audio":
                fmt = "audio"
                print("  modo de áudio ativado (alta qualidade)")
                continue
            if url.lower() == "video":
                fmt = "video"
                print("  modo de vídeo ativado (MP4)")
                continue

            if url.lower() == "res" and fmt == "video":
                print("  1: 480p | 2: 720p | 3: 1080p | 4: best")
                sel = input("  escolha [1-4] > ").strip()
                opts = {"1": "480", "2": "720", "3": "1080", "4": "best"}
                if sel in opts:
                    q_video = opts[sel]
                    print(f"  resolução definida como {_quality_label(q_video)}")
                continue

            if url.lower().endswith(".txt"):
                if os.path.exists(url):
                    with open(url, "r", encoding="utf-8") as f:
                        links = [line.strip() for line in f if line.strip()]
                    print(f"  {len(links)} link(s) encontrados em {url}")
                    for i, link in enumerate(links):
                        print(f"  item {i + 1}/{len(links)}")
                        smart_download(
                            link,
                            output_path=target,
                            file_format=fmt,
                            quality="best" if fmt == "audio" else q_video,
                            auth_refresh_callback=refresh_cookie_interactive,
                        )
                else:
                    print("  ✗ erro » arquivo não encontrado")
                continue

            files = smart_download(
                url,
                output_path=target,
                file_format=fmt,
                quality="best" if fmt == "audio" else q_video,
                auth_refresh_callback=refresh_cookie_interactive,
            )
            if rename and len(files) == 1:
                if _is_playlist_url(url):
                    print("  aviso » renomear é aplicado apenas a vídeos individuais")
                else:
                    _rename_file(files[0])
            print("")
        except KeyboardInterrupt:
            _diag_logger.emit("cli", "SHUTDOWN", "Usuário encerrou execução")
            print("\naté mais.")
            break
        except Exception as e:
            failure = classify_failure(e)
            print(f"  ✗ {failure.user_message}")
            if failure.kind is ErrorKind.UNKNOWN:
                print(f"  detalhe » {technical_summary(failure)}")


def main():
    _diag_ctx = RunContext()
    _diag_logger = DiagnosticLogger(_diag_ctx)
    _diag_logger.emit('cli', 'START', 'Execução iniciada', data={'version': _diag_ctx.version})
    _reporter = DiagnosticReporter(_diag_ctx, _diag_logger)
    atexit.register(lambda: _reporter.write())

    def _crash_hook(exc_type, exc, tb):
        _reporter.crash(exc)
        _diag_logger.emit('cli', 'SHUTDOWN', 'Execução encerrada por exceção', level='ERROR', data={'exception': exc_type.__name__})
        traceback.print_exception(exc_type, exc, tb)
    sys.excepthook = _crash_hook
    parser = argparse.ArgumentParser(
        description="YT-DLP TUI: downloader resiliente de mídia do YouTube."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--n", metavar="URL", help="Baixar um vídeo individual")
    group.add_argument("--p", metavar="URL", help="Baixar uma playlist inteira")
    parser.add_argument(
        "-f", "--format", choices=["audio", "video"], default="audio", help="Formato de saída"
    )

    args = parser.parse_args()

    # Every process/run must explicitly choose its destination. This value lives
    # only in memory for the duration of this run and is never persisted.
    target = _select_output_folder()
    if not target:
        print("  cancelado » nenhuma pasta de download foi selecionada")
        return

    if len(sys.argv) == 1:
        interactive_mode(target)
        return

    if args.n or args.p:
        url = args.n or args.p
        is_playlist = bool(args.p)
        print(f"Iniciando download em modo {args.format.upper()}...")
        print(f"Salvando em: {target}")
        download_media(
            url,
            is_playlist=is_playlist,
            file_format=args.format,
            output_path=target,
            auth_refresh_callback=refresh_cookie_interactive,
        )
    else:
        interactive_mode(target)


if __name__ == "__main__":
    main()
