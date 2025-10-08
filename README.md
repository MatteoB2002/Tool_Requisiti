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
```


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
- Parsing dei requisiti (REQUIREMENT_LINE_PARSE_RX)

#### 1️ Espressione Regolare per la Cattura dei Gruppi
  ```bash
  REQUIREMENT_LINE_PARSE_RX = re.compile(r"^(R\d+):\s*(\d+),\s*'(.*?)',\s*([A-Za-z0-9_]+)\s*$")
  ```
Questa regex cattura i seguenti gruppi:

* **Gruppo 1 (`(R\d+)`)** → L'ID univoco del requisito (es. `R1`, `R123`).
* **Gruppo 2 (`(\d+)`)** → L'ID numerico del progetto.
* **Gruppo 3 (`(.*?)`)** → Il testo effettivo del requisito, racchiuso tra apici singoli.

  > Il `*?` è un quantificatore *non-greedy* per catturare il testo fino al prossimo apice singolo.
* **Gruppo 4 (`([A-Za-z0-9_]+)`)** → La classe del requisito (es. `PE`, `SE`, `US`).

---

#### 2️ Normalizzazione del Testo (`norm_word`, `norm_phrase`, `WORD_RX`)

Per garantire che la corrispondenza dei termini sia **insensibile alla capitalizzazione** e a leggere variazioni di formattazione, lo script impiega funzioni di normalizzazione:

* **`norm_word(s: str) -> str`**
  Converte una singola parola in minuscolo e rimuove spazi bianchi all’inizio/fine.

* **`norm_phrase(s: str) -> str`**
  Per le frasi multi-parola, oltre alla conversione in minuscolo, sostituisce underscore (`_`) e trattini (`-`) con spazi, quindi comprime spazi multipli in un singolo spazio.

  > Questo permette, ad esempio, a `"tempo_di_risposta"` o `"tempo-di-risposta"` di corrispondere a `"tempo di risposta"`.

* La funzione **`get_words_from_text`** estrae tutte le singole parole da un testo utilizzando l’espressione regolare

  ```python
  WORD_RX = re.compile(r"\b\w+\b", flags=re.UNICODE)
  ```

  che cattura sequenze di caratteri alfanumerici.
  Le parole estratte vengono poi normalizzate.

---

#### 3️ Caricamento Ottimizzato dei Dizionari (`load_all_dicts_optimized`)

Questa è una delle aree chiave di ottimizzazione.
Invece di caricare e confrontare ogni termine manualmente, lo script distingue tra **parole singole** e **frasi multi-parola**, per sfruttare al meglio le capacità di *FlashText*:

* **Parole singole** → caricate in un dizionario Python (`singles_category_map: Dict[str, Set[str]]`).

  * La chiave è la parola normalizzata.
  * Il valore è un set di categorie a cui appartiene.
  * L’uso di `set` evita duplicazioni per parole appartenenti a più categorie.

* **Frasi multi-parola** → aggiunte a un oggetto `KeywordProcessor` della libreria **FlashText**.
  FlashText è estremamente efficiente nella ricerca di molte parole chiave in un testo, molto più veloce delle espressioni regolari, specialmente con grandi dizionari.
  Ogni frase è associata alla sua categoria.

> Questa separazione e l’uso di FlashText garantiscono un caricamento veloce e una ricerca successiva altamente performante.

---

#### 4️ Tokenizzazione e Corrispondenza (`tokenize_and_match`)

La funzione `tokenize_and_match` è responsabile di trovare tutte le corrispondenze (match) in un dato testo di requisito:

* **Ricerca multi-parola (con FlashText)**
  Usa

  ```python
  multi_phrase_processor.extract_keywords(requirement_text, span_info=True)
  ```

  per trovare tutte le frasi multi-parola presenti nel requisito.
  L’opzione `span_info=True` restituisce non solo la categoria, ma anche gli indici di inizio e fine del match nel testo originale, consentendo di recuperare la frase esatta.

* **Ricerca parole singole**
  Vengono estratte tutte le parole singole dal requisito tramite `get_words_from_text`.
  Ogni parola normalizzata viene confrontata con `singles_category_map`; in caso di corrispondenza, viene aggiunta alla lista dei match.

Il risultato è una lista di tuple nel formato:
`(parola/frase_trovata_originale, categoria, testo_requisito_originale)`
La parola o frase viene mantenuta nella forma originale per una migliore leggibilità dell’output.

---

#### 5️ Generazione dell’Output (`Labeled_Dataset.csv`)

Lo script itera su ogni requisito, esegue `tokenize_and_match` e formatta i risultati in un file CSV finale.

* Scrive un’intestazione:

  ```
  ID;ID progetto;REQUISITO (testo);Classe dei requisiti;CATEGORIA;PAROLA
  ```
* Per ogni requisito:

  * Se **non vengono trovate corrispondenze**, scrive una riga con `CATEGORIA` e `PAROLA` come `NULL`.
  * Se **vengono trovate corrispondenze**, assicura che ogni coppia (termine, categoria) sia unica, evitando duplicati.

Ogni match genera una riga separata nel CSV, consentendo un’analisi dettagliata di **quali termini e categorie** sono stati identificati per ciascun requisito.

> L’uso di `buffering=1000000` nell’apertura del file di output migliora le performance di scrittura, riducendo le operazioni di I/O su disco — particolarmente utile con dataset di grandi dimensioni.

---
  
- genera un file CSV con le seguenti colonne delimitate da  `;` :

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

