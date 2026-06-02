# kali_setup.py

Script Python unificato per l'automazione del setup di macchine **Kali Linux**.
Espone un menu interattivo da cui eseguire i singoli moduli o l'intera suite in sequenza.

---

## Requisiti

- Python 3.6+
- Kali Linux (testato su Kali Rolling)
- Connessione a internet
- Accesso sudo

Non richiede dipendenze esterne: usa solo la libreria standard Python.

---

## Avvio

```bash
python3 kali_setup.py
```

> Alcuni moduli richiedono i privilegi sudo. La password viene chiesta interattivamente
> all'avvio del singolo modulo, verificata prima di procedere, e mai scritta su disco.

---

## Menu

```
  1) Installa Sliver C2
  2) Installa xrdp
  3) Clone CVE-2025-47812-poc, KeePass Password Dumper e ligolo-ng
  4) Installa xfreerdp
  5) Installa impacket (virtualenv)
  6) Installa KeePass 2.x
  7) Installa Go 1.26.2
  8) Installa .NET 10
  9) Esegui tutto (Kali)

  0) Esci
```

Dopo ogni operazione lo script torna al menu, permettendo di eseguire più moduli
nella stessa sessione senza rilanciare lo script.

---

## Moduli

### 1 · Sliver C2

Installa il framework C2 [Sliver](https://github.com/BishopFox/sliver).

**Operazioni:**
- Scarica lo script di installazione da `https://sliver.sh/install`
- Applica il fix `SLIVER_PLATFORM="linux"` → `"linux-amd64"` via regex
- Esegue l'installazione con `sudo -E` (variabili d'ambiente preservate)
- Abilita e avvia il servizio `systemd`
- Installa i pacchetti armory **mimikatz** e **rubeus** tramite proxy

**Input richiesti all'avvio:**
| Input | Descrizione |
|-------|-------------|
| Proxy armory | Es. `http://10.80.254.254:3128` — usato per `armory install` |
| Password sudo | Necessaria per `sudo -E` |

> Lo script deve essere eseguito come **root** (`sudo python3 kali_setup.py`).

---

### 2 · xrdp

Installa e configura il server RDP per accesso remoto grafico alla macchina Kali.

**Operazioni:**
1. `apt update`
2. `apt install xrdp -y` — con fix automatico `apt install xorgxrdp --fix-missing` in caso di blocco
3. `systemctl enable xrdp`
4. `systemctl start xrdp`
5. `adduser xrdp ssl-cert` — necessario per l'accesso ai certificati TLS

**Input richiesti:** password sudo.

**Note:** se la sessione RDP non si avvia, eseguire `sudo systemctl restart xrdp`.

---

### 3 · Clone repository GitHub

Clona i seguenti repository:

| Repository | Descrizione |
|------------|-------------|
| [`CVE-2025-47812-poc`](https://github.com/4m3rr0r/CVE-2025-47812-poc) | Proof of concept per CVE-2025-47812 |
| [`keepass-password-dumper`](https://github.com/vdohney/keepass-password-dumper) | Tool per il dump delle password da database KeePass |
| [`ligolo-ng`](https://github.com/nicocha30/ligolo-ng) | Tunneling avanzato per pivoting di rete tramite TUN interface |

**Input richiesti:** directory di destinazione (default: directory corrente).

Se la cartella esiste già, lo script propone di eseguire `git pull` invece di fallire.

**Requisiti:** `git` installato (`sudo apt install git -y`).

---

### 4 · xfreerdp

Installa il client RDP `xfreerdp` per connettersi a macchine Windows o altri server RDP.

**Operazioni:**
1. Controlla se `xfreerdp` è già presente nel PATH — se sì, esce senza fare nulla
2. `apt update`
3. `apt install freerdp2-x11 -y`

**Input richiesti:** password sudo (solo se l'installazione è necessaria).

**Utilizzo base:**
```bash
xfreerdp /v:<IP> /u:<utente> /p:<password> /dynamic-resolution
```

---

### 5 · impacket (virtualenv)

Installa [impacket](https://github.com/fortra/impacket) in un **virtualenv Python dedicato**,
isolato dal sistema per evitare conflitti di dipendenze.

**Operazioni:**
1. Verifica la disponibilità di `python3`, `pip` e del modulo `venv`
2. Chiede la directory dove creare il venv (default: `~/impacket-venv`)
3. Controlla se impacket è già installato nel venv — propone aggiornamento se sì
4. Crea il virtualenv e aggiorna pip al suo interno
5. Installa impacket con `pip install impacket`

**Input richiesti:** percorso del virtualenv.

**Non richiede sudo.**

**Utilizzo:**
```bash
source ~/impacket-venv/bin/activate
python3 -c "import impacket; print(impacket.__version__)"
# tool disponibili: secretsdump, psexec, smbclient, ...
deactivate
```

---

### 6 · KeePass 2.x

Installa KeePass 2 tramite apt.

**Operazioni:**
1. Controlla se `keepass2` è già nel PATH — se sì, esce senza fare nulla
2. `apt update`
3. `apt install keepass2 -y` (include `mono` come dipendenza — l'installazione può richiedere alcuni minuti)

**Input richiesti:** password sudo (solo se l'installazione è necessaria).

**Utilizzo:**
```bash
keepass2
keepass2 /path/to/database.kdbx
```

---

### 7 · Go 1.26.2

Installa Go 1.26.2 da tarball ufficiale, rimuovendo prima eventuali versioni precedenti.

**Operazioni:**
1. Rimuove `/usr/local/go` se presente
2. Rimuove pacchetti apt `golang`, `golang-go`, `golang-src` se presenti
3. Scarica `go1.26.2.linux-amd64.tar.gz` da `https://go.dev/dl/`
4. Estrae in `/usr/local`
5. Configura il PATH in `/etc/profile.d/go.sh`

**Input richiesti:** password sudo.

**Dopo l'installazione:**
```bash
source /etc/profile.d/go.sh
go version
```

---

### 8 · .NET 10

Installa .NET SDK 10 tramite lo script ufficiale Microsoft, rimuovendo prima versioni precedenti.

**Operazioni:**
1. Rimuove pacchetti apt `dotnet*` e `aspnet*` se presenti
2. Rimuove `/usr/share/dotnet` e `~/.dotnet` se presenti
3. Rimuove il link simbolico `/usr/bin/dotnet` se presente
4. Scarica lo script ufficiale da `https://dot.net/v1/dotnet-install.sh`
5. Installa .NET SDK canale `10` in `/usr/share/dotnet`
6. Crea il link simbolico `/usr/bin/dotnet`
7. Configura il PATH in `/etc/profile.d/dotnet.sh`

**Input richiesti:** password sudo.

**Dopo l'installazione:**
```bash
dotnet --version
dotnet --list-sdks
```

---

### 9 · Esegui tutto (Kali)

Esegue tutti i moduli in sequenza dopo conferma esplicita dell'utente:

```
Sliver → xrdp → Clone repos → xfreerdp → impacket → KeePass → Go → .NET
```

Ogni modulo chiederà i propri input (password sudo, percorsi, proxy) al momento opportuno.

---

## File prodotti / modificati

| Path | Modulo | Descrizione |
|------|--------|-------------|
| `/tmp/sliver-install.sh` | Sliver | Script temporaneo, rimosso dopo l'uso |
| `/usr/local/bin/sliver` | Sliver | Binario principale |
| `/etc/profile.d/go.sh` | Go | Configurazione PATH |
| `/usr/local/go/` | Go | Directory di installazione Go |
| `/etc/profile.d/dotnet.sh` | .NET | Configurazione PATH |
| `/usr/share/dotnet/` | .NET | Directory di installazione .NET |
| `/usr/bin/dotnet` | .NET | Link simbolico al binario |
| `~/impacket-venv/` | impacket | Virtualenv Python |
