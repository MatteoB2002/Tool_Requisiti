#  Requirement Labeling Tool

# Progetto di Annotazione Requisiti con Dizionari

## Panoramica del Progetto

Questo progetto Python è stato sviluppato per automatizzare il processo di pre-elaborazione e annotazione di requisiti testuali. Partendo da un dataset grezzo, il sistema è in grado di assegnare identificatori unici ai requisiti e successivamente di etichettarli con categorie pertinenti basate su un insieme di dizionari forniti. L'output finale è un dataset strutturato e annotato, pronto per ulteriori analisi o per l'addestramento di modelli di Machine Learning.

L'approccio modulare, diviso in due script principali (`AssociazioneID.py` e `tool.py`), garantisce flessibilità e manutenibilità.

## Funzionalità Principali

*   **Assegnazione ID Unici**: Genera identificatori progressivi (`R<numero>`) per ogni requisito, facilitando il tracciamento e la gestione.
*   **Pulizia Requisiti**: Filtra righe vuote e commenti dal dataset iniziale.
*   **Annotazione Basata su Dizionari**: Utilizza dizionari esterni (parole singole e frasi multi-parola) per identificare e associare categorie a specifici termini all'interno dei requisiti.
*   **Gestione Frasi Multi-parola Ottimizzata**: Implementa `Flashtext` per una ricerca efficiente e performante di frasi multi-parola, superando i limiti delle espressioni regolari tradizionali.
*   **Output Strutturato**: Genera un file CSV (`Labeled_Dataset.csv`) con i requisiti originali arricchiti da ID, categoria e parola/frase corrispondente.

## Struttura del Progetto


```
├── Dataset.arff
├── AssociazioneID.py
├── tool.py
├── NewDict/
│   ├── categoria1.txt
│   ├── categoria2.txt
│   └── ...
└── output/
    ├── Dataset_with_R_ID.txt
    └── Labeled_Dataset.csv
```

### File Principali

1.  **`AssociazioneID.py`**:
    *   Prende in ingresso il dataset grezzo (`Dataset.arff`).
    *   Rimuove eventuali intestazioni o metadati (come quelli dei file `.arff`).
    *   Assegna un ID univoco (`R<numero>`) a ciascun requisito.
    *   Salva i requisiti processati in `Dataset_With_R_ID.txt`.

2.  **`tool.py`**:
    *   Prende in ingresso i requisiti con ID da `Dataset_With_R_ID.txt`.
    *   Carica dizionari da una directory specificata (`NewDict/`).
    *   Utilizza `Flashtext` per l'estrazione efficiente di parole singole e frasi multi-parola.
    *   Confronta i termini estratti con i dizionari per assegnare categorie.
    *   Genera `Labeled_Dataset.csv`, contenente i requisiti originali, il loro ID, l'ID del progetto, la classe originale, la categoria assegnata e la parola/frase che ha generato il match.

### Directory e File Essenziali

*   **`Dataset.arff`**: Il file del dataset di requisiti di partenza (nome configurabile).
*   **`NewDict/`**: Una directory che deve contenere i file dei dizionari. Ogni file `.txt` all'interno di questa directory rappresenta una categoria, e il nome del file (senza estensione) sarà il nome della categoria.
    *   Esempio: `NewDict/Sicurezza.txt` conterrà termini relativi alla sicurezza; `NewDict/Performance.txt` conterrà termini relativi alle performance.
    *   Ogni riga in questi file può essere una parola singola o una frase multi-parola.

## Requisiti di Sistema

*   Python 3.6 o superiore

### Dipendenze Python

Per installare le dipendenze necessarie, esegui:

```bash
pip install flashtext


---

##  Flusso operativo

### Generazione ID dei requisiti

Esegui:

```bash
python AssociazioneID.py
```

- **Input:** `Dataset.arff`  
- **Output:** `Dataset_with_R_ID.txt`

Lo script:
- rimuove l’intestazione `.arff`;
- ignora righe vuote e commenti;
- assegna un ID progressivo nel formato `R<num>` a ciascun requisito;
- produce un file testuale contenente una riga per ogni requisito.


### Etichettatura semantica con dizionari

Esegui:

```bash
python tool.py
```

- **Input:**
  - `Dataset_with_R_ID.txt`
  - directory `NewDict/` (con file `.txt` di termini per categoria)
- **Output:** `Labeled_Dataset.csv`

Lo script:
- carica tutti i dizionari di categoria;
- riconosce **parole singole** e **frasi multi-parola** presenti nei requisiti;
- associa ogni occorrenza alla categoria di appartenenza;
- genera un file CSV con le seguenti colonne:

| ID | ID progetto | REQUISITO (testo) | Classe dei requisiti | CATEGORIA | PAROLA |
|----|--------------|------------------|----------------------|------------|---------|



##  Funzionamento tecnico

- Il modulo utilizza **FlashText** per il matching efficiente di parole e frasi multi-parola.  
- Il codice normalizza termini e frasi (minuscolo, rimozione di trattini/underscore).  
- Supporta encoding UTF-8.  
- Output in formato CSV delimitato da `;`.

---

##  File di output

### Dataset_with_R_ID.txt
Contiene i requisiti con ID numerico.

### Labeled_Dataset.csv
Dataset finale etichettato, adatto per analisi di classificazione O detection di *requirement smells*.

---


## Configurazione avanzata
- Entrambi gli script contengono variabili configurabili all'interno del blocco if __name__ == "__main__":.
- AssociazioneID.py
  - in_path: Percorso del file di input dei requisiti (default: Dataset.arff).
  - out_path: Percorso del file di output con gli ID (default: Dataset_With_R_ID.txt).
  - prefix: Prefisso per gli ID (default: "R").
  - start_from: Numero da cui iniziare l'incremento degli ID (default: 1).
  - keep_blank_lines: True per mantenere le righe vuote nell'output (default: False).
  - skip_if_already_tagged: True per saltare le righe che hanno già un ID valido (default: True).
- tool.py
  - DICTIONARIES_DIR: Percorso della directory contenente i file dei dizionari (default: NewDict).
  - REQUIREMENTS_FILE: Percorso del file dei requisiti con ID (default: Dataset_With_R_ID.txt).
  - OUTPUT_FILE: Percorso del file CSV di output annotato (default: Labeled_Dataset.csv).

