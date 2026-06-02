#!/usr/bin/env python3
"""
kali_setup.py
Script di setup unificato per Kali Linux e Windows.
Raggruppa:
  - Installazione Sliver C2 (Kali)
  - Installazione xrdp (Kali)
  - Clone repository GitHub (Kali)
  - Installazione xfreerdp (Kali)
  - Installazione impacket in virtualenv (Kali)
  - Installazione Firefox + RSAT AD Tools (Windows)
"""

import os
import sys
import subprocess
import shutil
import getpass
import re
from pathlib import Path

# ───────────────────────────────────────────────────────────────────────────────
# COLORI
# ───────────────────────────────────────────────────────────────────────────────

BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"

# ───────────────────────────────────────────────────────────────────────────────
# HELPERS COMUNI
# ───────────────────────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"{GREEN}[+]{RESET} {msg}")

def warn(msg: str):
    print(f"{YELLOW}[!]{RESET} {msg}")

def err(msg: str):
    print(f"{RED}[-]{RESET} {msg}")

def section(title: str):
    pad = max(0, 40 - len(title))
    print(f"\n{BOLD}{CYAN}── {title} {'─' * pad}{RESET}")

def run(cmd: str, check=True, env=None) -> subprocess.CompletedProcess:
    """Esegue un comando shell con output live."""
    print(f"  {YELLOW}${RESET} {cmd}")
    process = subprocess.Popen(
        cmd, shell=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=env or os.environ.copy()
    )
    for line in process.stdout:
        print(f"    {line}", end="")
    process.wait()
    if check and process.returncode != 0:
        err(f"Comando fallito (exit {process.returncode}): {cmd}")
        sys.exit(process.returncode)
    return subprocess.CompletedProcess(cmd, process.returncode)

def run_list(cmd: list, check=True, cwd=None) -> subprocess.CompletedProcess:
    """Esegue un comando come lista con output live."""
    print(f"  {YELLOW}${RESET} {' '.join(str(c) for c in cmd)}")
    process = subprocess.Popen(
        cmd, text=True, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=os.environ.copy()
    )
    for line in process.stdout:
        print(f"    {line}", end="")
    process.wait()
    if check and process.returncode != 0:
        err(f"Comando fallito (exit {process.returncode})")
        sys.exit(process.returncode)
    return subprocess.CompletedProcess(cmd, process.returncode)

def run_sudo(cmd: str, password: str, check=True) -> subprocess.CompletedProcess:
    """Esegue un comando con sudo -S, password via stdin, output live."""
    print(f"  {YELLOW}${RESET} sudo {cmd}")
    process = subprocess.Popen(
        f"sudo -S {cmd}", shell=True, text=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=os.environ.copy()
    )
    process.stdin.write(password + "\n")
    process.stdin.flush()
    process.stdin.close()
    for line in process.stdout:
        print(f"    {line}", end="")
    process.wait()
    if check and process.returncode != 0:
        err(f"Comando fallito (exit {process.returncode}): {cmd}")
        sys.exit(process.returncode)
    return subprocess.CompletedProcess(cmd, process.returncode)

def run_sudo_E(cmd: str, password: str, check=True) -> subprocess.CompletedProcess:
    """Esegue un comando con sudo -SE (env preservato), password via stdin."""
    full_cmd = f"sudo -SE sh -c {repr(cmd)}"
    print(f"  {YELLOW}${RESET} {cmd}")
    result = subprocess.run(
        full_cmd, shell=True, text=True,
        input=password + "\n",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env=os.environ.copy()
    )
    if result.stdout.strip():
        for line in result.stdout.strip().splitlines():
            print(f"    {line}")
    if check and result.returncode != 0:
        err(f"Comando fallito (exit {result.returncode}): {cmd}")
        sys.exit(result.returncode)
    return result

def ask_sudo_password(msg: str = "verrà usata per tutti i comandi privilegiati") -> str:
    """Chiede la password sudo (nascosta) e la verifica."""
    print(f"\n{BOLD}Password sudo{RESET} ({msg})")
    while True:
        password = getpass.getpass("  Inserisci la password sudo: ")
        result = subprocess.run(
            "sudo -S true", input=password + "\n",
            shell=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            log("Password sudo verificata.")
            return password
        warn("Password errata, riprova.")

def check_root():
    if os.geteuid() != 0:
        err("Questo modulo richiede di essere eseguito come root.")
        sys.exit(1)

# ───────────────────────────────────────────────────────────────────────────────
# MENU
# ───────────────────────────────────────────────────────────────────────────────

MENU_ITEMS = [
    ("Installa Sliver C2",                                  "kali"),
    ("Installa xrdp",                                       "kali"),
    ("Clone CVE-2025-47812-poc, KeePass Password Dumper e ligolo-ng", "kali"),
    ("Installa xfreerdp",                                   "kali"),
    ("Installa impacket (virtualenv)",                      "kali"),
    ("Installa KeePass 2.x",                                "kali"),
    ("Installa Go 1.26.2",                                  "kali"),
    ("Installa .NET 10",                                    "kali"),
    ("Esegui tutto (Kali)",                                 "kali"),
]

def banner():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════╗
║           Kali/Windows Setup Suite          ║
║   sliver · xrdp · repos · rdp · impacket   ║
╚══════════════════════════════════════════════╝{RESET}
""")

def print_menu():
    print(f"{BOLD}Seleziona un'operazione:{RESET}\n")
    for i, (label, platform) in enumerate(MENU_ITEMS, 1):
        tag = f"{CYAN}[kali]{RESET}   " if platform == "kali" else f"{YELLOW}[win]{RESET}    "
        print(f"  {BOLD}{i}{RESET}) {tag}{label}")
    print(f"\n  {BOLD}0{RESET}) Esci\n")

def ask_menu_choice() -> int:
    while True:
        try:
            raw = input(f"{BOLD}Scelta:{RESET} ").strip()
            choice = int(raw)
            if 0 <= choice <= len(MENU_ITEMS):
                return choice
            warn(f"Inserisci un numero tra 0 e {len(MENU_ITEMS)}.")
        except ValueError:
            warn("Inserisci un numero valido.")

# ───────────────────────────────────────────────────────────────────────────────
# MODULO 1 — SLIVER
# ───────────────────────────────────────────────────────────────────────────────

SLIVER_INSTALL_SCRIPT = "/tmp/sliver-install.sh"
SLIVER_INSTALL_URL    = "https://sliver.sh/install"
ARMORY_PACKAGES       = ["mimikatz", "rubeus"]

def sliver_download_and_fix():
    section("STEP 1 — Download e fix sliver-install.sh")
    log(f"Download da {SLIVER_INSTALL_URL} ...")
    run(f'curl -L -o {SLIVER_INSTALL_SCRIPT} {SLIVER_INSTALL_URL}')

    content  = Path(SLIVER_INSTALL_SCRIPT).read_text()
    original = content
    content  = re.sub(
        r'(SLIVER_PLATFORM\s*=\s*["\'])linux(["\'])',
        r'\1linux-amd64\2', content
    )
    if content == original:
        warn("Pattern SLIVER_PLATFORM='linux' non trovato. Controlla manualmente.")
    else:
        Path(SLIVER_INSTALL_SCRIPT).write_text(content)
        log("Fix applicato: SLIVER_PLATFORM → linux-amd64")
    run(f"chmod +x {SLIVER_INSTALL_SCRIPT}")

def sliver_install(password: str):
    section("STEP 2 — Esecuzione sliver-install.sh")
    log("Avvio installazione (potrebbe richiedere qualche minuto)...")
    run_sudo_E(SLIVER_INSTALL_SCRIPT, password)

def sliver_systemd():
    section("STEP 3 — Abilitazione servizio systemd")
    run("systemctl enable sliver")
    run("systemctl start sliver", check=False)
    result = run("systemctl is-active sliver", check=False)
    if "active" in result.stdout:
        log("Servizio sliver attivo.")
    else:
        warn("Servizio sliver non attivo. Avvialo con: sudo systemctl start sliver")

def sliver_armory(proxy: str):
    section("STEP 4 — Installazione pacchetti armory")
    log(f"Proxy armory: {proxy}")
    sliver_bin = shutil.which("sliver") or "/usr/local/bin/sliver"
    if not Path(sliver_bin).exists():
        err(f"Binario sliver non trovato in {sliver_bin}.")
        warn(f"Esegui manualmente:\n  sliver\n"
             f"  armory install mimikatz -p {proxy}\n"
             f"  armory install rubeus   -p {proxy}")
        return
    for pkg in ARMORY_PACKAGES:
        log(f"Installazione armory: {pkg}")
        result = run(f"{sliver_bin} armory install {pkg} -p {proxy}", check=False)
        if result.returncode == 0:
            log(f"{pkg} installato.")
        else:
            warn(f"Fallito. Esegui manualmente: armory install {pkg} -p {proxy}")

def install_sliver():
    section("═══ SLIVER C2 ═══")
    check_root()
    print(f"\n{BOLD}Proxy per armory{RESET} (es: http://10.80.254.254:3128)")
    while True:
        proxy = input("  Inserisci il proxy: ").strip()
        if proxy:
            break
        warn("Il proxy non può essere vuoto.")
    password = ask_sudo_password("necessaria per sudo -E")

    sliver_download_and_fix()
    sliver_install(password)
    sliver_systemd()
    sliver_armory(proxy)

    section("RIEPILOGO — Sliver")
    print(f"""
  {GREEN}✔{RESET} sliver-install.sh scaricato e fixato
  {GREEN}✔{RESET} Installazione eseguita
  {GREEN}✔{RESET} Servizio systemd abilitato

  {YELLOW}Comandi manuali (se armory non completato):{RESET}
    sudo systemctl start sliver
    sliver
    armory install mimikatz -p {proxy}
    armory install rubeus   -p {proxy}
""")

# ───────────────────────────────────────────────────────────────────────────────
# MODULO 2 — XRDP
# ───────────────────────────────────────────────────────────────────────────────

def install_xrdp():
    section("═══ XRDP ═══")
    password = ask_sudo_password()

    section("STEP 1 — apt update")
    log("Aggiorno i repository...")
    run_sudo("apt update", password)
    log("Lista pacchetti aggiornata.")

    section("STEP 2 — Installazione xrdp")
    log("Avvio installazione xrdp...")
    warn("L'installazione potrebbe bloccarsi su xorgxrdp: applico il fix automaticamente.")
    result = run_sudo("apt install xrdp -y", password, check=False)
    if result.returncode != 0:
        warn("apt install xrdp fallito. Applico fix xorgxrdp...")
    else:
        log("xrdp installato. Applico fix xorgxrdp per sicurezza.")
    run_sudo("apt install xorgxrdp --fix-missing -y", password)
    log("Installazione xrdp completata.")

    section("STEP 3 — Abilitazione servizio xrdp")
    run_sudo("systemctl enable xrdp", password)
    log("Servizio xrdp abilitato all'avvio.")

    section("STEP 4 — Avvio servizio xrdp")
    run_sudo("systemctl start xrdp", password)
    result = run_sudo("systemctl is-active xrdp", password, check=False)
    if "active" in (result.stdout or ""):
        log("Servizio xrdp attivo.")
    else:
        warn("Servizio non attivo. Verifica con: sudo systemctl status xrdp")

    section("STEP 5 — Aggiunta xrdp al gruppo ssl-cert")
    log("Aggiungo xrdp al gruppo ssl-cert...")
    run_sudo("adduser xrdp ssl-cert", password)
    log("Fatto.")
    warn("Potrebbe servire: sudo systemctl restart xrdp")

    section("RIEPILOGO — xrdp")
    print(f"""
  {GREEN}✔{RESET} apt update eseguito
  {GREEN}✔{RESET} xrdp installato (con fix xorgxrdp)
  {GREEN}✔{RESET} Servizio abilitato e avviato
  {GREEN}✔{RESET} xrdp aggiunto al gruppo ssl-cert
""")

# ───────────────────────────────────────────────────────────────────────────────
# MODULO 3 — CLONE REPOS
# ───────────────────────────────────────────────────────────────────────────────

REPOS = [
    {"url": "https://github.com/4m3rr0r/CVE-2025-47812-poc.git",       "name": "CVE-2025-47812-poc"},
    {"url": "https://github.com/vdohney/keepass-password-dumper.git",  "name": "keepass-password-dumper"},
    {"url": "https://github.com/nicocha30/ligolo-ng.git",              "name": "ligolo-ng"},
]

def clone_repos():
    section("═══ CLONE REPOSITORY ═══")

    result = subprocess.run(["which", "git"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        err("git non trovato. Installalo con: sudo apt install git -y")
        sys.exit(1)
    log("git disponibile.")

    print(f"\n{BOLD}Directory di destinazione{RESET} (lascia vuoto per directory corrente)")
    raw = input("  Inserisci il percorso: ").strip()
    dest = Path(raw).expanduser().resolve() if raw else Path.cwd()
    if not dest.exists():
        warn(f"'{dest}' non esiste. La creo...")
        dest.mkdir(parents=True)
    log(f"Destinazione: {dest}")

    for repo in REPOS:
        name   = repo["name"]
        url    = repo["url"]
        target = dest / name
        section(f"Clone — {name}")
        log(f"URL: {url}")

        if target.exists():
            warn(f"'{target}' esiste già.")
            choice = input("  Fare git pull? [s/N] ").strip().lower()
            if choice == "s":
                result = subprocess.run(["git", "-C", str(target), "pull"], text=True)
                log(f"'{name}' aggiornato." if result.returncode == 0 else f"git pull fallito per '{name}'.")
            else:
                warn(f"Salto '{name}'.")
            continue

        log(f"Clono in: {target}")
        result = subprocess.run(["git", "clone", url, str(target)], text=True)
        if result.returncode == 0:
            log(f"'{name}' clonato con successo.")
        else:
            err(f"Clone fallito (exit {result.returncode}).")

    section("RIEPILOGO — Clone repos")
    print(f"\n  {YELLOW}Repository in: {BOLD}{dest}{RESET}\n")
    for repo in REPOS:
        target = dest / repo["name"]
        status = f"{GREEN}✔{RESET}" if target.exists() else f"{RED}✘{RESET}"
        print(f"  {status} {repo['name']}\n      {target}")
    print()

# ───────────────────────────────────────────────────────────────────────────────
# MODULO 4 — XFREERDP
# ───────────────────────────────────────────────────────────────────────────────

def install_xfreerdp():
    section("═══ XFREERDP ═══")

    section("STEP 1 — Verifica installazione esistente")
    result = subprocess.run(["which", "xfreerdp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        path = result.stdout.strip()
        log(f"xfreerdp già installato: {path}")
        ver = subprocess.run(["xfreerdp", "--version"],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if ver.stdout.strip():
            log(f"Versione: {ver.stdout.strip().splitlines()[0]}")
        print(f"\n  {GREEN}✔{RESET} xfreerdp già presente, nessuna azione necessaria.\n")
        return

    log("xfreerdp non trovato. Procedo con l'installazione.")
    password = ask_sudo_password()

    section("STEP 2 — apt update")
    run_sudo("apt update", password)
    log("Lista pacchetti aggiornata.")

    section("STEP 3 — Installazione freerdp2-x11")
    log("Il pacchetto 'freerdp2-x11' fornisce il comando xfreerdp...")
    run_sudo("apt install freerdp2-x11 -y", password)
    log("Installazione completata.")

    result = subprocess.run(["which", "xfreerdp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        log(f"xfreerdp disponibile in: {result.stdout.strip()}")
    else:
        warn("xfreerdp non trovato nel PATH. Apri un nuovo terminale e riprova.")

    section("RIEPILOGO — xfreerdp")
    print(f"""
  {GREEN}✔{RESET} apt update eseguito
  {GREEN}✔{RESET} freerdp2-x11 installato

  {YELLOW}Esempio:{RESET}
    xfreerdp /v:<IP> /u:<utente> /p:<password> /dynamic-resolution
""")

# ───────────────────────────────────────────────────────────────────────────────
# MODULO 5 — IMPACKET
# ───────────────────────────────────────────────────────────────────────────────

DEFAULT_VENV_PATH = Path.home() / "impacket-venv"

def install_impacket():
    section("═══ IMPACKET (virtualenv) ═══")

    # Verifica dipendenze
    section("STEP 1 — Verifica dipendenze")
    python = shutil.which("python3")
    if not python:
        err("python3 non trovato. Installalo con: sudo apt install python3 -y")
        sys.exit(1)
    r = subprocess.run(["python3", "--version"], capture_output=True, text=True)
    log(f"python3: {r.stdout.strip()}")

    pip = shutil.which("pip3") or shutil.which("pip")
    if not pip:
        err("pip non trovato. Installalo con: sudo apt install python3-pip -y")
        sys.exit(1)
    r = subprocess.run([pip, "--version"], capture_output=True, text=True)
    log(f"pip: {r.stdout.strip()}")

    r = subprocess.run(["python3", "-m", "venv", "--help"], capture_output=True, text=True)
    if r.returncode != 0:
        err("Modulo venv non disponibile. Installalo con: sudo apt install python3-venv -y")
        sys.exit(1)
    log("modulo venv: disponibile")

    # Percorso venv
    print(f"\n{BOLD}Directory del virtualenv{RESET} (lascia vuoto per: {DEFAULT_VENV_PATH})")
    raw = input("  Inserisci il percorso: ").strip()
    venv_path = Path(raw).expanduser().resolve() if raw else DEFAULT_VENV_PATH

    if venv_path.exists():
        pip_bin = venv_path / "bin" / "pip"
        if pip_bin.exists():
            r = subprocess.run([str(pip_bin), "show", "impacket"], capture_output=True, text=True)
            if r.returncode == 0:
                warn(f"impacket già installato in '{venv_path}'.")
                for line in r.stdout.strip().splitlines():
                    print(f"    {line}")
                choice = input("\n  Reinstallare/aggiornare? [s/N] ").strip().lower()
                if choice != "s":
                    log("Installazione saltata.")
                    _impacket_activation_info(venv_path)
                    return
            else:
                warn("Venv esistente senza impacket. Procedo.")
        else:
            warn(f"'{venv_path}' esiste ma non sembra un venv.")
            if input("  Continuare? [s/N] ").strip().lower() != "s":
                return

    log(f"Percorso virtualenv: {venv_path}")

    section("STEP 2 — Creazione virtualenv")
    run_list(["python3", "-m", "venv", str(venv_path)])
    log("Virtualenv creato.")

    section("STEP 3 — Installazione impacket")
    pip_bin = venv_path / "bin" / "pip"
    log("Aggiorno pip nel venv...")
    run_list([str(pip_bin), "install", "--upgrade", "pip"])
    log("Installo impacket...")
    run_list([str(pip_bin), "install", "impacket"])

    r = subprocess.run([str(pip_bin), "show", "impacket"], capture_output=True, text=True)
    if r.returncode == 0:
        ver_line = next((l for l in r.stdout.splitlines() if l.startswith("Version:")), "")
        log(f"impacket installato correttamente. {ver_line}")
    else:
        warn("Verifica manuale fallita, ma l'installazione potrebbe essere andata a buon fine.")

    section("RIEPILOGO — impacket")
    print(f"""
  {GREEN}✔{RESET} Virtualenv creato in: {BOLD}{venv_path}{RESET}
  {GREEN}✔{RESET} impacket installato
""")
    _impacket_activation_info(venv_path)

def _impacket_activation_info(venv_path: Path):
    print(f"""
  {YELLOW}Attiva il virtualenv:{RESET}
    source {venv_path}/bin/activate

  {YELLOW}Verifica impacket:{RESET}
    python3 -c "import impacket; print(impacket.__version__)"

  {YELLOW}Disattiva quando hai finito:{RESET}
    deactivate
""")

# ───────────────────────────────────────────────────────────────────────────────
# MODULO 6 — KEEPASS 2.x
# ───────────────────────────────────────────────────────────────────────────────

def install_keepass():
    section("═══ KEEPASS 2.x ═══")

    # Controlla se già installato
    section("STEP 1 — Verifica installazione esistente")
    result = subprocess.run(["which", "keepass2"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        log(f"KeePass 2 già installato: {result.stdout.strip()}")
        r = subprocess.run(["keepass2", "--version"], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True)
        if r.stdout.strip():
            log(f"Versione: {r.stdout.strip().splitlines()[0]}")
        print(f"\n  {GREEN}✔{RESET} KeePass 2 già presente, nessuna azione necessaria.\n")
        return

    log("KeePass 2 non trovato. Procedo con l'installazione.")
    password = ask_sudo_password()

    section("STEP 2 — apt update")
    log("Aggiorno i repository...")
    run_sudo("apt update", password)
    log("Lista pacchetti aggiornata.")

    section("STEP 3 — Installazione keepass2")
    log("Installo keepass2 (include mono come dipendenza)...")
    warn("L'installazione di mono può richiedere qualche minuto.")
    run_sudo("apt install keepass2 -y", password)
    log("Installazione completata.")

    # Verifica finale
    result = subprocess.run(["which", "keepass2"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        log(f"keepass2 disponibile in: {result.stdout.strip()}")
    else:
        warn("keepass2 non trovato nel PATH dopo l'installazione.")
        warn("Verifica con: apt list --installed | grep keepass")

    section("RIEPILOGO — KeePass 2")
    print(f"""
  {GREEN}✔{RESET} apt update eseguito
  {GREEN}✔{RESET} keepass2 installato

  {YELLOW}Avvio:{RESET}
    keepass2
    keepass2 /path/to/database.kdbx
""")

# ───────────────────────────────────────────────────────────────────────────────
# MODULO 7 — GO 1.26.2
# ───────────────────────────────────────────────────────────────────────────────

GO_VERSION  = "1.26.2"
GO_TARBALL  = f"go{GO_VERSION}.linux-amd64.tar.gz"
GO_URL      = f"https://go.dev/dl/{GO_TARBALL}"
GO_INSTALL  = "/usr/local/go"

def install_go():
    section("═══ GO 1.26.2 ═══")
    password = ask_sudo_password()

    # STEP 1: Rimozione versioni precedenti
    section("STEP 1 — Rimozione installazioni precedenti di Go")
    if Path(GO_INSTALL).exists():
        log(f"Trovata installazione esistente in {GO_INSTALL}. La rimuovo...")
        run_sudo(f"rm -rf {GO_INSTALL}", password)
        log("Installazione precedente rimossa.")
    else:
        log("Nessuna installazione precedente trovata in /usr/local/go.")

    # Rimuove eventuali pacchetti apt di go
    result = subprocess.run(
        "dpkg -l | grep -E '^ii.*golang'",
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if result.stdout.strip():
        log("Trovati pacchetti golang via apt. Li rimuovo...")
        run_sudo("apt remove --purge -y golang golang-go golang-src", password, check=False)
        run_sudo("apt autoremove -y", password, check=False)
        log("Pacchetti apt golang rimossi.")
    else:
        log("Nessun pacchetto golang via apt trovato.")

    # STEP 2: Download
    section(f"STEP 2 — Download Go {GO_VERSION}")
    log(f"URL: {GO_URL}")
    dest = f"/tmp/{GO_TARBALL}"
    run(f"curl -L -o {dest} {GO_URL}")
    log("Download completato.")

    # STEP 3: Estrazione in /usr/local
    section("STEP 3 — Estrazione in /usr/local")
    log(f"Estraggo {GO_TARBALL} in /usr/local ...")
    run_sudo(f"tar -C /usr/local -xzf {dest}", password)
    log("Estrazione completata.")

    # STEP 4: Configura PATH in /etc/profile.d
    section("STEP 4 — Configurazione PATH")
    profile_file = "/etc/profile.d/go.sh"
    go_path_line = 'export PATH=$PATH:/usr/local/go/bin'
    # Controlla se già presente
    result = subprocess.run(
        f"grep -qF '/usr/local/go/bin' {profile_file} 2>/dev/null",
        shell=True
    )
    if result.returncode != 0:
        run_sudo(f"sh -c 'echo \"{go_path_line}\" > {profile_file}'", password)
        log(f"PATH aggiornato in {profile_file}")
    else:
        log("PATH già configurato.")

    # Pulizia
    subprocess.run(["rm", "-f", dest])
    log("Archivio temporaneo rimosso.")

    # Verifica
    result = subprocess.run(
        ["/usr/local/go/bin/go", "version"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        log(f"Verifica: {result.stdout.strip()}")
    else:
        warn("Verifica fallita. Riapri il terminale e prova: go version")

    section("RIEPILOGO — Go")
    print(f"""
  {GREEN}✔{RESET} Versioni precedenti rimosse
  {GREEN}✔{RESET} Go {GO_VERSION} installato in /usr/local/go
  {GREEN}✔{RESET} PATH configurato in {profile_file}

  {YELLOW}Ricarica il PATH con:{RESET}
    source /etc/profile.d/go.sh
    go version
""")

# ───────────────────────────────────────────────────────────────────────────────
# MODULO 8 — .NET 10
# ───────────────────────────────────────────────────────────────────────────────

DOTNET_VERSION      = "10"
DOTNET_INSTALL_DIR  = "/usr/share/dotnet"
DOTNET_SCRIPT_URL   = "https://dot.net/v1/dotnet-install.sh"
DOTNET_SCRIPT       = "/tmp/dotnet-install.sh"

def install_dotnet():
    section("═══ .NET 10 ═══")
    password = ask_sudo_password()

    # STEP 1: Rimozione versioni precedenti
    section("STEP 1 — Rimozione installazioni precedenti di .NET")

    # Rimuove pacchetti apt dotnet
    result = subprocess.run(
        "dpkg -l | grep -E '^ii.*(dotnet|aspnet)'",
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if result.stdout.strip():
        log("Trovati pacchetti .NET via apt. Li rimuovo...")
        run_sudo("apt remove --purge -y 'dotnet*' 'aspnet*'", password, check=False)
        run_sudo("apt autoremove -y", password, check=False)
        log("Pacchetti apt .NET rimossi.")
    else:
        log("Nessun pacchetto .NET via apt trovato.")

    # Rimuove installazioni manuali in /usr/share/dotnet e ~/.dotnet
    for dotnet_dir in [DOTNET_INSTALL_DIR, str(Path.home() / ".dotnet")]:
        if Path(dotnet_dir).exists():
            log(f"Rimuovo directory esistente: {dotnet_dir}")
            if dotnet_dir.startswith("/usr"):
                run_sudo(f"rm -rf {dotnet_dir}", password)
            else:
                run(f"rm -rf {dotnet_dir}")
            log(f"{dotnet_dir} rimossa.")
        else:
            log(f"Nessuna installazione trovata in {dotnet_dir}.")

    # Rimuove eventuali link simbolici in /usr/bin
    for link in ["/usr/bin/dotnet"]:
        if Path(link).exists() or Path(link).is_symlink():
            log(f"Rimuovo link simbolico: {link}")
            run_sudo(f"rm -f {link}", password)

    # STEP 2: Download script ufficiale Microsoft
    section("STEP 2 — Download script di installazione Microsoft")
    log(f"URL: {DOTNET_SCRIPT_URL}")
    run(f"curl -L -o {DOTNET_SCRIPT} {DOTNET_SCRIPT_URL}")
    run(f"chmod +x {DOTNET_SCRIPT}")
    log("Script scaricato.")

    # STEP 3: Installazione con script ufficiale
    section(f"STEP 3 — Installazione .NET {DOTNET_VERSION} (SDK + Runtime)")
    log(f"Installo .NET SDK {DOTNET_VERSION} in {DOTNET_INSTALL_DIR} ...")
    warn("L'installazione potrebbe richiedere qualche minuto.")
    run_sudo(
        f"{DOTNET_SCRIPT} --channel {DOTNET_VERSION} --install-dir {DOTNET_INSTALL_DIR}",
        password
    )
    log("Installazione SDK completata.")

    # STEP 4: Link simbolico e PATH
    section("STEP 4 — Configurazione PATH e link simbolico")
    dotnet_bin = f"{DOTNET_INSTALL_DIR}/dotnet"
    if Path(dotnet_bin).exists():
        run_sudo(f"ln -sf {dotnet_bin} /usr/bin/dotnet", password)
        log("Link simbolico /usr/bin/dotnet creato.")
    else:
        warn(f"Binario dotnet non trovato in {DOTNET_INSTALL_DIR}. Verifica manualmente.")

    profile_file = "/etc/profile.d/dotnet.sh"
    result = subprocess.run(
        f"grep -qF '{DOTNET_INSTALL_DIR}' {profile_file} 2>/dev/null",
        shell=True
    )
    if result.returncode != 0:
        run_sudo(
            f"sh -c 'echo \"export PATH=\\$PATH:{DOTNET_INSTALL_DIR}\" > {profile_file}'",
            password
        )
        log(f"PATH aggiornato in {profile_file}")
    else:
        log("PATH già configurato.")

    # Pulizia
    subprocess.run(["rm", "-f", DOTNET_SCRIPT])
    log("Script temporaneo rimosso.")

    # Verifica
    result = subprocess.run(["/usr/bin/dotnet", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        log(f"Verifica: dotnet {result.stdout.strip()}")
    else:
        warn("Verifica fallita. Riapri il terminale e prova: dotnet --version")

    section("RIEPILOGO — .NET")
    print(f"""
  {GREEN}✔{RESET} Versioni precedenti rimosse
  {GREEN}✔{RESET} .NET {DOTNET_VERSION} installato in {DOTNET_INSTALL_DIR}
  {GREEN}✔{RESET} Link simbolico: /usr/bin/dotnet
  {GREEN}✔{RESET} PATH configurato in {profile_file}

  {YELLOW}Verifica con:{RESET}
    dotnet --version
    dotnet --list-sdks
""")

# ───────────────────────────────────────────────────────────────────────────────
# ESEGUI TUTTO (KALI)
# ───────────────────────────────────────────────────────────────────────────────

def run_all_kali():
    section("═══ ESEGUI TUTTO — KALI ═══")
    warn("Verranno eseguiti in sequenza: Sliver, xrdp, clone repos, xfreerdp, impacket, KeePass, Go, .NET.")
    confirm = input("  Continuare? [s/N] ").strip().lower()
    if confirm != "s":
        log("Operazione annullata.")
        return
    install_sliver()
    install_xrdp()
    clone_repos()
    install_xfreerdp()
    install_impacket()
    install_keepass()
    install_go()
    install_dotnet()
    section("═══ SETUP KALI COMPLETATO ═══")
    log("Tutti i moduli eseguiti.")

# ───────────────────────────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────────────────────────

ACTIONS = [
    install_sliver,
    install_xrdp,
    clone_repos,
    install_xfreerdp,
    install_impacket,
    install_keepass,
    install_go,
    install_dotnet,
    run_all_kali,
]

def main():
    banner()
    while True:
        print_menu()
        choice = ask_menu_choice()
        if choice == 0:
            log("Uscita.")
            sys.exit(0)
        ACTIONS[choice - 1]()
        input(f"\n{BOLD}Premi Invio per tornare al menu...{RESET}")
        print("\n" + "─" * 50 + "\n")

if __name__ == "__main__":
    main()
