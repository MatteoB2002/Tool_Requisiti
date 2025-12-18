#  Automated Requirements Labeling Tool

Questo progetto fornisce una pipeline di scripting in **Python** per **pre‑elaborare**, **etichettare** e **selezionare** automaticamente requisiti in linguaggio naturale a partire da un dataset testuale e da dizionari di categorie.  
La pipeline produce dapprima un dataset etichettato (CSV) e quindi, tramite passi post‑processing, **suddivide per categoria** e **seleziona un sottoinsieme di requisiti** per le analisi successive.

---

##  Features

- **Pre‑elaborazione automatica** del dataset `.arff` (pulizia intestazioni/commenti).  
- **ID univoci** dei requisiti (`R1`, `R2`, …) per tracciabilità.  
- **Etichettatura basata su dizionari** (`NewDict/*.txt`, una categoria per file).  
- **Matching contestuale (spaCy)** con POS tagging per disambiguare termini polisemici.  
- **Supporto frasi multi‑parola (FlashText)** ad alte prestazioni.  
- **Post‑processing completo** dopo l’etichettatura:
  - **Splitter**: crea 19 file (uno per categoria) con i requisiti etichettati.
  - **Selecter**: seleziona **N requisiti casuali** per categoria (default 27) e li consolida in un unico CSV finale.
- **Utility per dizionari**:
  - **MergeDict**: unisce due file di termini “vaghi” e genera statistiche di overlap.

---

##  Struttura del Progetto

```bash
/progetto/
│
├── NewDict/                     # dizionari (una categoria per file .txt)
│   ├── noun.txt
│   ├── verb.txt
│   ├── adj.txt
│   └── vague.txt                 # (generato da MergeDict)
│   └── ...                       # altre categorie
│
├── Dataset.arff                 # dataset iniziale dei requisiti
├── AssociazioneID.py            # step 1: assegna ID e normalizza
├── tool.py                      # step 2: etichetta usando NewDict + spaCy + FlashText
├── Splitter.py                  # step 3: split per categoria (post-tool.py)
├── Selecter.py                  # step 4: selezione casuale per categoria (post-split)
├── MergeDict.py                 # utility: merge di due dizionari “vaghi”
│
├── Dataset_With_R_ID.txt        # (generato)
├── Labeled_Dataset.csv          # (generato)
├── Sorted_by_Categories/        # (generato da Splitter.py)
│   ├── <categoria>_requirements.csv
│   └── ...
│── Vague_1.txt
│── Vagues_2.txt
│
└── README.md
```

---

##  Requisiti e Installazione

- **Python** 3.7+
- Dipendenze:
```bash
pip install spacy flashtext
python -m spacy download en_core_web_sm
```

---

##  Workflow End‑to‑End

Di seguito il flusso operativo **completo**, con i passi “post‑tool.py” **integrati** perché necessari alla fase di **selezione** dei requisiti per l’analisi.

### 1) Pre‑elaborazione & ID — `AssociazioneID.py`
Legge `Dataset.arff`, rimuove intestazioni/commenti e assegna un ID univoco a ogni requisito.

```bash
python AssociazioneID.py
```
**Output**: `Dataset_With_R_ID.txt`  
Esempio riga:
```
R1: 1,'The system shall refresh the display every 60 seconds.',PE
```

### 2) Etichettatura — `tool.py`
Analizza ed etichetta ogni requisito utilizzando i dizionari in `NewDict/`, spaCy (POS) e FlashText (frasi).

```bash
python tool.py
```
**Output**: `Labeled_Dataset.csv` (delimitatore `;`)  
Colonne: `ID;ID progetto;REQUISITO (testo);Classe dei requisiti;CATEGORIA;PAROLA`

> Se un requisito ha più match, genera più righe. Se non ha match, `CATEGORIA` e `PAROLA` sono `NULL`.

### 3) Split per categoria — `Splitter.py` ️  (POST‑tool.py)
Legge `Labeled_Dataset.csv` e crea **19 file CSV**, uno per ciascuna categoria del dizionario, dentro `Sorted_by_Categories/`.

```bash
python Splitter.py
```
**Output**: `Sorted_by_Categories/<categoria>_requirements.csv` (con intestazione).  
Ogni file contiene **tutti i requisiti** etichettati con quella categoria.

### 4) Selezione campione — `Selecter.py` ️  (POST‑split)
Per ogni file in `Sorted_by_Categories/`, seleziona **N requisiti casuali** (default **27**, modificabile nello script).  
Se il file contiene meno di N requisiti, li include **tutti**. Infine consolida tutto in un unico CSV.

```bash
python Selecter.py
```
**Output**: `Requisiti_Selezionati.csv`  
**Randomicità**: la selezione è **casuale** → **non è garantito** ottenere lo stesso output finale a esecuzioni differenti.  
Per riproducibilità, imposta un seed all’inizio dello script (es. `random.seed(42)`).

---

##  Logica di Etichettatura (`tool.py`)

### Caricamento dizionari (`load_all_dicts_optimized`)
- **Parole singole** → normalizzate e mappate in `singles_category_map` (parola → set categorie).  
- **Frasi multi‑parola** → caricate in `KeywordProcessor` (FlashText) per matching veloce e scalabile.

### Tokenizzazione & Matching (`tokenize_and_match_with_spacy`)
1. **Frasi multi‑parola**: prioritarie (FlashText, con `span_info=True` per recupero esatto).  
2. **Token singoli**: analizzati con **spaCy** (lemma, POS).  
3. **Disambiguazione**: il lemma del token viene confrontato con `singles_category_map` e validato tramite `POS_CATEGORY_MAPPING` (es. `noun` → {`NOUN`,`PROPN`}).

**Esempio**  
Testo: “The system must display a warning message.”  
Se `display` è in `noun.txt` e `verb.txt`, spaCy lo marca **VERB** → categoria finale `verb` (riduzione falsi positivi).

---

##  Utility Dizionari — `MergeDict.py` (opzionale ma utile)

**Scopo**: unire due elenchi di termini “vaghi” in un unico file senza duplicati e generare statistiche di overlap. Utile per **curare/aggiornare** i dizionari prima di lanciare la pipeline.

**Input**: `Vague_1.txt`, `Vagues_2.txt`  
**Output**:
- `vague.txt` — unione **ordinata** di tutte le parole uniche dei due file.  
- `statistiche_file_uniti.txt` — contiene:
  - conteggio parole **solo** nel primo file;
  - conteggio parole **solo** nel secondo;
  - conteggio ed **elenco** parole **comuni**;
  - percentuali riepilogative.

**Esecuzione**:
```bash
python MergeDict.py
```

---

## 🛠️ Personalizzazione Rapida

- **Percorsi file**: modifica `DICTIONARIES_DIR`, `REQUIREMENTS_FILE`, `OUTPUT_FILE` in `tool.py`.  
- **Nuove categorie**: aggiungi un file `.txt` in `NewDict/` e aggiorna `POS_CATEGORY_MAPPING` (mappa categoria → POS spaCy).  
- **Parsing input**: la regex `REQUIREMENT_LINE_PARSE_RX` in `tool.py` definisce il formato di parsing delle righe di `Dataset_With_R_ID.txt`.  
- **Campione Selecter**: in `Selecter.py` cambia il numero N di requisiti da selezionare (default 30). Per risultati ripetibili, imposta un seed casuale.

---

##  Quick Start (tutto in fila)

```bash
# 1) Pre-elaborazione & ID
python AssociazioneID.py

# 2) Etichettatura
python tool.py

# 3) Split per categoria
python Splitter.py

# 4) Selezione campione (random)
python Selecter.py
```

Output principali:
- `Labeled_Dataset.csv` → dataset etichettato completo  
- `Sorted_by_Categories/` → 19 file, uno per categoria  
- `Requisiti_Selezionati.csv` → campione finale per l’analisi

---

## Autore

Progetto per la **qualità e l’analisi dei requisiti** tramite NLP, dizionari semantici e pipeline di post‑processing (split & selezione).



