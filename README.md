#  Automated Requirements Labeling Tool

Questo progetto fornisce una pipeline di scripting in **Python** per pre-elaborare, identificare e categorizzare parole e frasi chiave all'interno di un dataset di requisiti software.  
La pipeline utilizza **dizionari personalizzati** e l'analisi del contesto grammaticale tramite la libreria **spaCy** per etichettare in modo intelligente i termini, producendo un dataset strutturato in formato **CSV** pronto per ulteriori analisi.

---

##  Features

- **Pre-elaborazione Automatica** – Pulisce i file di dataset in formato `.arff`, rimuovendo intestazioni e commenti.  
- **ID Univoci** – Assegna un ID progressivo e univoco (es. `R1`, `R2`, ...) a ciascun requisito per un facile tracciamento.  
- **Etichettatura Basata su Dizionari** – Utilizza una directory di file `.txt` come dizionari, dove ogni file rappresenta una categoria semantica (es. `noun.txt`, `verb.txt`, `adj.txt`).  
- **Matching Contestuale Intelligente** – Sfrutta il modello di **Natural Language Processing (NLP)** di **spaCy** per eseguire il *Part-of-Speech* (POS) tagging, disambiguando parole con ruoli multipli.  
- **Supporto per Frasi Multi-parola** – Usa la libreria **FlashText** per individuare frasi multi-parola (es. “user interface”, “data base”).  
- **Output Strutturato** – Genera un file `Labeled_Dataset.csv` ben formattato, ideale per analisi o addestramento di modelli ML.

---

## Workflow del Progetto

Il processo è composto da due passaggi principali, gestiti da due script separati.

### 1️ Input iniziale: `Dataset.arff`
Contiene il dataset grezzo dei requisiti.

### 2️ Esecuzione di `AssociazioneID.py`
Legge `Dataset.arff`, lo pulisce e assegna un ID a ogni requisito.

**Output:** `Dataset_With_R_ID.txt` → requisiti identificati e numerati.

### 3️ Esecuzione di `tool.py` (con la directory `NewDict/`)
Analizza ed etichetta i requisiti usando i dizionari.

**Output:** `Labeled_Dataset.csv` → dataset finale con parole/frasi etichettate per categoria.

---

##  Struttura della Directory

```bash
/progetto/
│
├── NewDict/
│   ├── noun.txt
│   ├── verb.txt
│   ├── adj.txt
│   └── ... (altri dizionari .txt)
│
├── Dataset.arff
├── AssociazioneID.py
├── tool.py
│
├── Dataset_With_R_ID.txt
│── Labeled_Dataset.csv
│
└── README.md
```

---

## Prerequisiti e Installazione

### 🐍 Python
Assicurati di avere **Python 3.7 o superiore** installato.

### 📦 Librerie Necessarie
Installa le dipendenze richieste:
```bash
pip install spacy flashtext
```

### 💬 Modello spaCy
Scarica il modello linguistico inglese utilizzato da `tool.py`:
```bash
python -m spacy download en_core_web_sm
```

---

##  Guida all'Uso

### Passo 1: Preparazione dei File di Input
- Inserisci il tuo dataset iniziale nella root del progetto, chiamato `Dataset.arff`.
- Popola la directory `NewDict/` con i file `.txt` (uno per categoria).  
  - Il nome del file diventa il nome della categoria (es. `noun.txt` → categoria *noun*).  
  - Ogni riga deve contenere una parola o frase.

### Passo 2: Esegui `AssociazioneID.py`
Esegue la pulizia e crea il file con ID univoci.

```bash
python AssociazioneID.py
```

Genera `Dataset_With_R_ID.txt` con righe come:
```
R1: The system shall record user data.
```

### Passo 3: Esegui `tool.py`
Analizza e etichetta i requisiti.

```bash
python tool.py
```

Genera `Labeled_Dataset.csv`, contenente le etichette per parole/frasi trovate.

---

##  Logica di `tool.py`

### 1. Caricamento e Ottimizzazione dei Dizionari (`load_all_dicts_optimized`)
- **Parole Singole** → normalizzate e salvate in `singles_category_map` (parola → set categorie).  
- **Frasi Multi-parola** → caricate in un `KeywordProcessor` di FlashText per una ricerca veloce.  

### 2. Processamento dei Requisiti (`tokenize_and_match_with_spacy`)
Per ogni requisito:
1. **Ricerca Frasi Multi-parola** con FlashText (prioritaria).  
2. **Analisi POS con spaCy** per token rimanenti.  
3. **Matching Contestuale** con la mappa `POS_CATEGORY_MAPPING`.

#### Esempio
Requisito: `"The system must display a warning message."`  
Dizionari: `"display"` in `noun.txt` e `verb.txt`  
spaCy identifica `"display"` come VERB → lo script assegna categoria `verb`.

Questo approccio riduce drasticamente i falsi positivi grazie al contesto grammaticale.

---

##  Formato del File di Output (`Labeled_Dataset.csv`)

| Colonna | Descrizione | Esempio |
|----------|-------------|----------|
| **ID** | Identificatore univoco del requisito | R42 |
| **ID progetto** | ID del progetto dal file di input | 1 |
| **REQUISITO (testo)** | Testo completo del requisito | The application shall provide a search function |
| **Classe dei requisiti** | Classe estratta dal file di input | Functional_Requirement |
| **CATEGORIA** | Categoria derivata dal dizionario | noun |
| **PAROLA** | Parola/frase trovata nel requisito | application |

> Se un requisito contiene più corrispondenze, vengono create più righe.  
> Se nessuna parola/frase viene trovata, le colonne `CATEGORIA` e `PAROLA` contengono `NULL`.

---

##  Personalizzazione

- **Percorsi File** → modifica le costanti `DICTIONARIES_DIR`, `REQUIREMENTS_FILE`, `OUTPUT_FILE` in `tool.py`.  
- **Nuove Categorie** → aggiungi un file `.txt` in `NewDict/` e aggiorna `POS_CATEGORY_MAPPING` in base ai POS tag appropriati.  
- **Parsing dell’Input** → l’espressione regolare `REQUIREMENT_LINE_PARSE_RX` in `tool.py` definisce il formato di parsing delle righe di input.

---

##  Autore
Progetto sviluppato per attività di ricerca e analisi automatica dei **requisiti software** tramite NLP e dizionari semantici.
