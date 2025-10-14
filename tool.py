import re #libreria standard per le espressioni regolari (pattern di testo usati per parsing e normalizzazione )
from pathlib import Path # libreria standard per gestire i percorsi dei file 
from typing import Dict, Set, List, Tuple #servono per favorire analisi statica (consentono di tipare variabili e funzioni)
from flashtext import KeywordProcessor # libreria specializzata nel trovare e sostituire un gran numero di parole chiave all'interno di un testo 
import spacy #libreria NLP avanzata per l'analisi del linguaggio naturale

#Configurazione e Modello spaCy
SPACY_MODEL_NAME = "en_core_web_sm" # Modello spaCy da usare (inglese piccolo, leggero e veloce)
#per maggiore accuratezza, considerare modelli più grandi come "en_core_web_md" o "en_core_web_lg"

try:
    nlp = spacy.load(SPACY_MODEL_NAME) #carica il modello spaCy specificato
    print(f"[DEBUG] Modello spaCy '{SPACY_MODEL_NAME}' caricato con successo.")
except OSError:
    print(f"Errore: Modello spaCy '{SPACY_MODEL_NAME}' non trovato.")
    print(f"Assicurati di averlo installato eseguendo: python -m spacy download {SPACY_MODEL_NAME}")
    exit(1)

WORD_RX = re.compile(r"\b\w+\b", flags=re.UNICODE) #regex per identificare le parole singole all'interno di un testo 
#\b = confine di parola, \w+ = uno o più caratteri di parola (lettere A- Z, numeri  e underscore)
# re.UNICODE = flag che assicura che l'espressione regolare riconosca caratteri Unicode 

REQUIREMENT_LINE_PARSE_RX = re.compile(r"^(R\d+):\s*(\d+),\s*'(.*?)',\s*([A-Za-z0-9_]+)\s*$")
#regex per per leggere e interpretare ogni riga del file dei requisiti 
# ^ = inizio della riga, (R\d+) = cattura ID requisito (es. R1, R2), :\s* = due punti seguiti da spazi,
# (\d+) = cattura ID progetto (numerico), (.*?) = cattura testo requisito (qualsiasi carattere, non greedy),
# ([A-Za-z0-9_]+) = cattura classe requisito (caratteri alfanumerici e underscore), \s*$ = spazi finali e fine riga

def norm_word(s: str) -> str:
    # Normalizza una singola parola (minuscolo, senza spazi).
    return s.casefold().strip()

def norm_phrase(s: str) -> str:
    """
    Normalizza una frase multi-parola:
    - Sostituisce underscore con spazi.
    - Sostituisce trattini con spazi.
    - Comprime spazi multipli.
    - Converte in minuscolo.
    """
    s = s.replace("_", " ").replace("-", " ")
    return " ".join(s.split()).casefold()

# --- Mappatura Categorie-POS Tag SPECIFICA PER I  FILE DI DIZIONARIO ---
# Questa mappa converte il nome del file di dizionario nei POS tag di spaCy per quella categoria.
#  per avere la certezza che una parola venga etichettata correttamente in base al suo contesto grammaticale.
# sono inclusi i POS tag universali di spaCy che servono 

POS_CATEGORY_MAPPING = {
    "adj": {"ADJ"},                      # Aggettivi
    "adv": {"ADV"},                      # Avverbi
    "conjunction": {"CCONJ", "SCONJ"},   # Congiunzioni (coordinanti e subordinanti)
    "det": {"DET", "PRON"},              # Determinanti (articoli, dimostrativi) e alcuni pronomi
    "mv": {"AUX", "VERB"},               # Verbi Modali/Ausiliari (se il tuo mv.txt li contiene)
    "noun": {"NOUN", "PROPN"},           # Nomi (comuni e propri)
    "preposition": {"ADP"},              # Preposizioni
    "pronoun": {"PRON"},                 # Pronomi
    "pv": {"VERB", "AUX"},               # Verbi (se il tuo pv.txt contiene verbi principali)
    "verb": {"VERB", "AUX"},             # Verbi (verbi principali e ausiliari)
    "vpastp": {"VERB", "AUX"},           # Verbi Passato Participe (se i tuoi files li dividono per forma)
    "vpastt": {"VERB", "AUX"},           # Verbi Passato (idem)
    "vpresentp": {"VERB", "AUX"},        # Verbi Presente Participe (idem)
   
}


# Funzioni di Caricamento Dizionari e Matching 
def load_all_dicts_optimized(dir_path: Path):
    """
    Carica tutti i dizionari da una directory.
    Usa KeywordProcessor per le frasi multi-parola.
    Ritorna:
      singles_category_map: Dict[str, Set[str]] - Mappa lemma normalizzato -> set di categorie
      multi_phrase_processor: KeywordProcessor - Processore per frasi multi-parola
    """
    singles_category_map: Dict[str, Set[str]] = {} # mappa la parola normalizzata al suo set di categorie a cui appartiene
    multi_phrase_processor = KeywordProcessor(case_sensitive=False) #inizializza un oggetto KeywordProcessor e dice a flasntext di ignorare le la differenza tra maiusc e minusc

    print(f"Caricamento dizionari ottimizzato dalla directory: {dir_path}")
    if not dir_path.is_dir():
        print(f"[ERRORE] La directory dei dizionari '{dir_path}' non esiste o non è una directory valida.")
        return singles_category_map, multi_phrase_processor

    dict_files_found = list(dir_path.glob("*.txt"))
    if not dict_files_found:
        print(f"[AVVISO] Nessun file .txt trovato nella directory dizionari: {dir_path}. Assicurati che i file abbiano estensione .txt")

    for path in sorted(dict_files_found):
        categoria = path.stem # Il nome del file senza estensione diventa la categoria
        print(f"  Caricamento categoria: '{categoria}' da '{path.name}'")

        if not path.is_file():
            print(f"    [ERRORE] Il file '{path.name}' non è un file valido o non è accessibile.")
            continue
        
        lines_read = 0
        phrases_added = 0
        words_added = 0

        for line_num_in_file, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            lines_read += 1
            s = raw_line.strip()
            if not s:
                continue

            if (" " in s) or ("_" in s) or ("-" in s): # controllo se è una frase o una parola singola
                p_norm = norm_phrase(s)
                multi_phrase_processor.add_keyword(p_norm, categoria)
                phrases_added += 1
            else:
                w_norm = norm_word(s) # Usa il lemma normalizzato in fase di matching
                singles_category_map.setdefault(w_norm, set()).add(categoria)
                words_added += 1
        print(f"    [DEBUG] Lette {lines_read} righe. Aggiunte {phrases_added} frasi e {words_added} parole singole per la categoria '{categoria}'.")
    
    print(f"  Caricate {len(singles_category_map)} parole singole e {len(multi_phrase_processor.get_all_keywords())} frasi multi-parola.")
    return singles_category_map, multi_phrase_processor

def tokenize_and_match_with_spacy(requirement_text: str,
                                   singles_category_map: Dict[str, Set[str]],
                                   multi_phrase_processor: KeywordProcessor,
                                   nlp) -> List[Tuple[str, str, str]]:
    """
    Trova tutte le corrispondenze (singole parole e frasi multi-parola) in un requisito,
    usando spaCy per il contesto grammaticale.

    Ritorna:
      List[Tuple[str, str, str]] - Lista di tuple (parola/frase trovata_originale, categoria, testo_requisito_originale)
    """
    
    found_matches: List[Tuple[str, str, str]] = []
    
    # Processa il testo con spaCy per ottenere token, lemmi e POS tag
    doc = nlp(requirement_text)


    # per il debug 
    # if "R1: 1" in requirement_text: # Condizione per filtrare il requisito R1
    #     print(f"\n--- DEBUG SPAy: Requisito '{requirement_text}' ---")
    #     for token in doc:
    #         print(f"Token: '{token.text}', Lemma: '{token.lemma_}', POS: '{token.pos_}', Tag: '{token.tag_}'")
    #     print("----------------------------------\n")
    # FINE

    # 1. Ricerca di frasi multi-parola con Flashtext (prioritaria)

    multi_keywords_with_spans = multi_phrase_processor.extract_keywords(requirement_text, span_info=True) #ceerca  nei requirement text tutte le keyword che erano stte caricate nel keyword processor
    # span_info=True fa in modo che ritorni anche gli indici di inizio e fine della keyword trovata

    occupied_token_indices: Set[int] = set() #set per tenere traccia degli indici dei token che fanno gia parte di una frase. 

#itero su ogni frase trovata da flashtext 
    for match_category, start_char, end_char in multi_keywords_with_spans:
        original_matched_text = requirement_text[start_char:end_char]
        found_matches.append((original_matched_text, match_category, requirement_text))
        #estraggo la porzione di testo origninale che corrisponde alla frase trovata 
        # e viene aggiunta alla lista dei risultati la tupla (testo originale, categoria, testo requisito)

        for token in doc: #iterazione su token spaCy 
            if (token.idx >= start_char and token.idx < end_char) or \
               ((token.idx + len(token.text)) > start_char and (token.idx + len(token.text)) <= end_char) or \
               (token.idx <= start_char and (token.idx + len(token.text)) >= end_char):
                occupied_token_indices.add(token.i)

    # 2. Ricerca di parole singole usando spaCy per il contesto
    for token in doc:
        if token.i in occupied_token_indices:
            continue

        w_norm = norm_word(token.lemma_) 
        
        if w_norm in singles_category_map:
            potential_categories = singles_category_map[w_norm]
            
            # Qui uso la logica di spaCy e la mappa Categoria-POS
            matched_with_context = False
            
            # Prova a trovare una categoria che corrisponda al POS tag del token
            # Itera sulle categorie potenziali in ordine alfabetico 
            # se una parola è in più dizionari con POS tag compatibili.
            for cat in sorted(list(potential_categories)):
                expected_pos_tags = POS_CATEGORY_MAPPING.get(cat)


                if expected_pos_tags is not None and token.pos_ in expected_pos_tags:
                    found_matches.append((token.text, cat, requirement_text))
                    matched_with_context = True
                    break # Trovata la migliore corrispondenza contestuale, passa al prossimo token
            
            # Se la parola è presente nei dizionari ma non c'è una corrispondenza POS tag specifica
            # nella mappa, la ignoriamo.

    return found_matches

#  Main Logic
if __name__ == "__main__":
    # Configurazione dei percorsi dei file
    DICTIONARIES_DIR = Path("NewDict") 
    REQUIREMENTS_FILE = "Dataset_With_R_ID.txt"  
    OUTPUT_FILE = "Labeled_Dataset.csv" 

    # 1. Carica i dizionari in modo ottimizzato
    singles_category_map, multi_phrase_processor = load_all_dicts_optimized(DICTIONARIES_DIR)
    
    total_single_words = len(singles_category_map)
    total_multi_phrases = len(multi_phrase_processor.get_all_keywords())

    if not (total_single_words or total_multi_phrases):
        print("Attenzione: Nessuna parola o frase è stata caricata dai dizionari. Controlla la directory e i file.")
        exit(0)
    else:
        print(f"[DEBUG] Dizionari caricati con successo: {total_single_words} parole singole e {total_multi_phrases} frasi multi-parola.")

    # 2. Processa il dataset di requisiti
    print(f"\nProcessamento requisiti dal file: {REQUIREMENTS_FILE}")
    
    processed_req_count = 0
    matches_found_total = 0
#blocco di lettura e scrittura dei file con gestione delle eccezioni
    try:
        with open(REQUIREMENTS_FILE, 'r', encoding='utf-8') as req_f, \
             open(OUTPUT_FILE, 'w', encoding='utf-8', buffering=1000000) as out_f:
            
            out_f.write("ID;ID progetto;REQUISITO (testo);Classe dei requisiti;CATEGORIA;PAROLA\n")
            
            for line_num, line in enumerate(req_f, 1): 
                stripped_line = line.strip()
                
                if not stripped_line:
                    continue

                m = REQUIREMENT_LINE_PARSE_RX.match(stripped_line) #faccio il match della riga con la regex
                if not m:
                    print(f"Avviso: Riga {line_num} non parsabile (ignorata): {stripped_line}")
                    continue
                # estraggo le porzioni di testo catturate tra parentesi dalla regex 
                req_id = m.group(1)
                proj_id = m.group(2)
                req_text = m.group(3)
                req_class = m.group(4)
                
                matches_for_current_req = tokenize_and_match_with_spacy(req_text, singles_category_map, multi_phrase_processor, nlp)
                
                unique_matches_for_this_req: Set[Tuple[str, str]] = set() # per tenere traccia delle coppie (categoria, parola/frase) già scritte per questo requisito
                output_lines_for_this_req: List[str] = [] # per accumulare le righe di output per questo requisito

                base_output_parts = [req_id, proj_id, req_text, req_class] # parti comuni della riga di output

                if not matches_for_current_req:#se non ci sono match scrivo NULL nella categoria e nella parola
                    output_line = ";".join(base_output_parts + ["NULL", "NULL"]) + "\n"
                    out_f.write(output_line)
                else: #se ci sono match, scrivo una riga per ogni match unico
                    for original_word_phrase, category, _ in matches_for_current_req:
                        if (category, original_word_phrase) not in unique_matches_for_this_req:
                            output_line = ";".join(base_output_parts + [category, original_word_phrase]) + "\n"
                            output_lines_for_this_req.append(output_line)
                            unique_matches_for_this_req.add((category, original_word_phrase))
                            matches_found_total += 1
                    
                    out_f.writelines(output_lines_for_this_req)
                
                processed_req_count += 1
                if processed_req_count % 100 == 0:
                    print(f"  [PROGRESSO] Processati {processed_req_count} requisiti...")

    except FileNotFoundError:
        print(f"Errore: Il file dei requisiti '{REQUIREMENTS_FILE}' non trovato nella directory corrente.")
        exit(1)
    except Exception as e:
        import traceback
        print(f"Si è verificato un errore inaspettato durante l'elaborazione: {e}")
        traceback.print_exc()
        exit(1)
        
    print(f"\nElaborazione completata. I risultati sono stati scritti in '{OUTPUT_FILE}'.")
    print(f"Match totali univoci trovati e scritti: {matches_found_total}")