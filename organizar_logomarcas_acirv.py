from pathlib import Path
import shutil
import sys

# ============================================================
# CONFIGURAÇÃO
# ============================================================

DRIVE_ROOT = Path(r"H:\Meu Drive")
DEST_ROOT = Path(r"C:\Users\Kevyn Lucas\Downloads\LOGOMARCAS - ACIRV E PROJETOS")

# Se quiser apenas testar sem copiar, mude para True.
DRY_RUN = False

PROJECTS = [
    "00 - ACIRV",
    "01 - ACIRV MULHER",
    "02 - CAM ACIRV",
    "03 - CONECTA ACIRV",
    "04 - CONECTA SAÚDE",
    "05 - CAFÉ ENTRE AMIGOS",
    "06 - EMPREGA ACIRV",
    "07 - ALERVE",
    "08 - SUDOEXPO",
    "09 - CONQUISTA",
    "10 - QUEM INDICA FORTALECE",
    "11 - FÓRUM",
    "99 - A IDENTIFICAR",
]

SUBFOLDERS = [
    "PNG",
    "PDF - VETOR",
    "EDITÁVEIS",
]


# ============================================================
# ARQUIVOS IDENTIFICADOS NO DRIVE
# Formato:
# ("PASTA DO PROJETO", r"caminho relativo dentro de H:\Meu Drive")
# ============================================================

FILES_TO_COPY = [
    # --------------------------------------------------------
    # 00 - ACIRV
    # --------------------------------------------------------
    ("00 - ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Acirv Nova Logo (1).pdf"),
    ("00 - ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Acirv Nova Logo.pdf"),
    ("00 - ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Logo ACIRV-01.png"),
    ("00 - ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Logo ACIRV-02.png"),
    ("00 - ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Logo ACIRV.pdf"),

    ("00 - ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\ACIRV LOGO - SEM FUNDO.png"),
    ("00 - ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\ACIRV LOGO.png"),
    ("00 - ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Acirv Nova Logo.pdf"),
    ("00 - ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo ACIRV-02.png"),

    ("00 - ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Todos os projetos da ACIRV\Acirv Nova Logo.pdf"),
    ("00 - ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Todos os projetos da ACIRV\LOGO ACIRV - ALTA - SEM FUNDO.png"),

    ("00 - ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV\Materiais\LOGO ACIRV.png"),
    ("00 - ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV\Materiais\LOGO ACIRV.psd"),

    # --------------------------------------------------------
    # 01 - ACIRV MULHER
    # --------------------------------------------------------
    ("01 - ACIRV MULHER", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Logo ACIRV Mulher.pdf"),
    ("01 - ACIRV MULHER", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Todos os projetos da ACIRV\Logo ACIRV Mulher.pdf"),
    ("01 - ACIRV MULHER", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Todos os projetos da ACIRV\logo branca ACIRV Mulher.png"),

    # --------------------------------------------------------
    # 02 - CAM ACIRV
    # --------------------------------------------------------
    ("02 - CAM ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\08-09-25 - Nova Logo CAM-01.png"),
    ("02 - CAM ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\08-09-25 - Nova Logo CAM-02.png"),
    ("02 - CAM ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\08-09-25 - Nova Logo CAM-03.png"),
    ("02 - CAM ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\08-09-25 - Nova Logo CAM-04.png"),
    ("02 - CAM ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\LOGO CAM1.png"),
    ("02 - CAM ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Todos os projetos da ACIRV\LOGO CAM1.png"),

    # --------------------------------------------------------
    # 03 - CONECTA ACIRV
    # --------------------------------------------------------
    ("03 - CONECTA ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\conecta acirv (6) (1).pdf"),
    ("03 - CONECTA ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV\Materiais\Logo Conecta.png"),
    ("03 - CONECTA ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV\Materiais\LOGO CONECTA.psd"),
    ("03 - CONECTA ACIRV", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Todos os projetos da ACIRV\Logo Conecta.png"),

    # --------------------------------------------------------
    # 04 - CONECTA SAÚDE
    # --------------------------------------------------------
    ("04 - CONECTA SAÚDE", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV\Materiais\LOGO CONECTA SAÚDE - HQ COLOR.png"),
    ("04 - CONECTA SAÚDE", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV\Materiais\Logo Conecta Saúde - HQ.png"),
    ("04 - CONECTA SAÚDE", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV\Materiais\Logo Conecta Saúde.png"),
    ("04 - CONECTA SAÚDE", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV\Materiais\LOGO CONECTA SAÚDE.psd"),

    # --------------------------------------------------------
    # 05 - CAFÉ ENTRE AMIGOS
    # --------------------------------------------------------
    ("05 - CAFÉ ENTRE AMIGOS", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Logo Café Entre Amigos.png"),

    # --------------------------------------------------------
    # 06 - EMPREGA ACIRV
    # --------------------------------------------------------
    ("06 - EMPREGA ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Logo Emprega ACIRV_Prancheta 1.png"),
    ("06 - EMPREGA ACIRV", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Logo Emprega ACIRV_Prancheta 1 (1).png"),

    # --------------------------------------------------------
    # 07 - ALERVE
    # --------------------------------------------------------
    ("07 - ALERVE", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Logo ALERVE.pdf"),

    # --------------------------------------------------------
    # 08 - SUDOEXPO
    # --------------------------------------------------------
    ("08 - SUDOEXPO", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Logo SudoExpo.png"),
    ("08 - SUDOEXPO", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\logos sudoexpo B&V P&V.pdf"),
    ("08 - SUDOEXPO", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\LOGO SUDOEXPO.png"),
    ("08 - SUDOEXPO", r"GESTÃO 2025 2028\SUDOEXPO - 2026\MATERIAIS LANÇAMENTO SUDOEXPO\SUDOEXPO 2026\PSDS\LOGOTIPO-3D.psd"),

    # --------------------------------------------------------
    # 09 - CONQUISTA
    # --------------------------------------------------------
    ("09 - CONQUISTA", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\LOGOMARCA CONQUISTA VETOR OK-01 2.png"),
    ("09 - CONQUISTA", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\LOGOMARCA CONQUISTA VETOR OK-01 2 (1).png"),

    # --------------------------------------------------------
    # 10 - QUEM INDICA FORTALECE
    # --------------------------------------------------------
    ("10 - QUEM INDICA FORTALECE", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\LOGO QUEM INDICA FORTALECE.png"),
    ("10 - QUEM INDICA FORTALECE", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\LOGO QUEM INDICA FORTALECE (1).png"),

    # --------------------------------------------------------
    # 11 - FÓRUM
    # --------------------------------------------------------
    ("11 - FÓRUM", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo_Forum\Logo_Forum\Logo_Forum.ai"),

    ("11 - FÓRUM", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo_Forum\Logo_Forum\PDFs\Logo_PDF_Branca.pdf"),
    ("11 - FÓRUM", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo_Forum\Logo_Forum\PDFs\Logo_PDF_Colorida.pdf"),
    ("11 - FÓRUM", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo_Forum\Logo_Forum\PDFs\Logo_PDF_Curvas_Branca.pdf"),
    ("11 - FÓRUM", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo_Forum\Logo_Forum\PDFs\Logo_PDF_Curvas_Colorida.pdf"),
    ("11 - FÓRUM", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo_Forum\Logo_Forum\PDFs\Logo_PDF_Curvas_Preta.pdf"),
    ("11 - FÓRUM", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo_Forum\Logo_Forum\PDFs\Logo_PDF_Preta.pdf"),

    ("11 - FÓRUM", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo_Forum\Logo_Forum\PNGs\Logo_Branca.png"),
    ("11 - FÓRUM", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo_Forum\Logo_Forum\PNGs\Logo_Colorida.png"),
    ("11 - FÓRUM", r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Identidade Visual\Logo_Forum\Logo_Forum\PNGs\Logo_Preta.png"),

    # --------------------------------------------------------
    # 99 - A IDENTIFICAR
    # --------------------------------------------------------
    ("99 - A IDENTIFICAR", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Colorida.png"),
    ("99 - A IDENTIFICAR", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Negativa.png"),
    ("99 - A IDENTIFICAR", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\Positiva.png"),
    ("99 - A IDENTIFICAR", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\logo (1).png"),
    ("99 - A IDENTIFICAR", r"GESTÃO 2025 2028\LOGOS DOS PROJETOS ACIRV\logo (2).pdf"),
]


# ============================================================
# FUNÇÕES
# ============================================================

def get_type_folder(file_path: Path) -> str:
    """Define em qual subpasta o arquivo deve ser colocado."""
    ext = file_path.suffix.lower()

    if ext == ".png":
        return "PNG"

    if ext == ".pdf":
        return "PDF - VETOR"

    if ext in {".ai", ".psd", ".svg", ".eps"}:
        return "EDITÁVEIS"

    # Caso futuramente seja adicionado outro formato,
    # ele ficará em EDITÁVEIS para não sair da estrutura definida.
    return "EDITÁVEIS"


def unique_destination(destination: Path) -> Path:
    """
    Evita sobrescrever arquivos de mesmo nome.
    Ex.:
        Logo.pdf
        Logo (2).pdf
        Logo (3).pdf
    """
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    counter = 2

    while True:
        candidate = destination.with_name(f"{stem} ({counter}){suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def create_structure():
    """Cria a estrutura completa de pastas."""
    print("\nCriando estrutura...\n")

    if not DRY_RUN:
        DEST_ROOT.mkdir(parents=True, exist_ok=True)

    for project in PROJECTS:
        project_path = DEST_ROOT / project

        if not DRY_RUN:
            project_path.mkdir(parents=True, exist_ok=True)

        for subfolder in SUBFOLDERS:
            path = project_path / subfolder
            if not DRY_RUN:
                path.mkdir(parents=True, exist_ok=True)


def copy_files():
    copied = []
    missing = []
    errors = []

    total = len(FILES_TO_COPY)

    for index, (project, relative_path) in enumerate(FILES_TO_COPY, start=1):
        source = DRIVE_ROOT / relative_path

        type_folder = get_type_folder(source)
        target_dir = DEST_ROOT / project / type_folder
        target = unique_destination(target_dir / source.name)

        print(f"[{index:02d}/{total:02d}] {project}")
        print(f"   Origem : {source}")
        print(f"   Destino: {target}")

        if not source.exists():
            print("   [NÃO ENCONTRADO]\n")
            missing.append(str(source))
            continue

        try:
            if not DRY_RUN:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

            copied.append((str(source), str(target)))
            print("   [OK]\n")

        except Exception as exc:
            errors.append((str(source), str(exc)))
            print(f"   [ERRO] {exc}\n")

    return copied, missing, errors


def print_summary(copied, missing, errors):
    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)

    print(f"\nPasta final:")
    print(DEST_ROOT)

    print(f"\nArquivos previstos : {len(FILES_TO_COPY)}")
    print(f"Copiados           : {len(copied)}")
    print(f"Não encontrados    : {len(missing)}")
    print(f"Erros              : {len(errors)}")

    if missing:
        print("\n" + "-" * 70)
        print("ARQUIVOS NÃO ENCONTRADOS")
        print("-" * 70)
        for item in missing:
            print(item)

    if errors:
        print("\n" + "-" * 70)
        print("ERROS")
        print("-" * 70)
        for source, error in errors:
            print(f"{source}")
            print(f"  -> {error}")

    if DRY_RUN:
        print("\nATENÇÃO: DRY_RUN=True. Nenhum arquivo foi realmente copiado.")

    print("\nConcluído.")


def main():
    print("=" * 70)
    print("ORGANIZADOR DE LOGOMARCAS - ACIRV")
    print("=" * 70)

    if not DRIVE_ROOT.exists():
        print("\nERRO:")
        print(f"O diretório de origem não foi encontrado:")
        print(DRIVE_ROOT)
        print("\nVerifique se o Google Drive está montado como unidade H:.")
        input("\nPressione ENTER para sair...")
        sys.exit(1)

    print(f"\nOrigem : {DRIVE_ROOT}")
    print(f"Destino: {DEST_ROOT}")

    create_structure()
    copied, missing, errors = copy_files()
    print_summary(copied, missing, errors)

    input("\nPressione ENTER para fechar...")


if __name__ == "__main__":
    main()
