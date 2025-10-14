import re
from pathlib import Path
from typing import Dict, Set, List, Tuple
from flashtext import KeywordProcessor
import spacy

# --- Configurazione e Modello spaCy ---
SPACY_MODEL_NAME = "en_core_web_sm"

try:
    nlp = spacy.load(SPACY_MODEL_NAME)
    print(f"[DEBUG] Modello spaCy '{SPACY_MODEL_NAME}' caricato con successo.")
except OSError:
    print(f"Errore: Modello spaCy '{SPACY_MODEL_NAME}' non trovato.")
    print(f"Assicurati di averlo installato eseguendo: python -m spacy download {SPACY_MODEL_NAME}")
    exit(1)

# --- Espressioni Regolari e Funzioni di Normalizzazione ---
WORD_RX = re.compile(r"\b\w+\b", flags=re.UNICODE)
REQUIREMENT_LINE_PARSE_RX = re.compile(r"^(R\d+):\s*(\d+),\s*'(.*?)',\s*([A-Za-z0-9_]+)\s*$")

def norm_word(s: str) -> str:
    """Normalizza una singola parola (minuscolo, senza spazi)."""
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
# Questa mappa ora converte il nome del tuo file di dizionario (la "categoria")
# nei POS tag di spaCy che ci aspetteremmo per quella categoria.
# Ho incluso i POS tag universali di spaCy. Potresti voler affinare con i TAG specifici
# se necessario (es. token.tag_ per 'NN', 'NNS', 'VBD', ecc.).
# Per ora, i POS universali sono un buon punto di partenza.
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
    # Importante: Se un tuo dizionario contiene parole che possono avere più POS tag validi
    # (es. "display" può essere NOUN o VERB), dovrai decidere come gestire questo.
    # Con questa mappa, se una parola è in "noun.txt" e anche in "verb.txt", e spaCy la vede come NOUN,
    # verrà etichettata come "noun". Se spaCy la vede come VERB, verrà etichettata come "verb".
    # L'ordine in cui i "potential_categories" vengono iterati può influenzare se una parola è in più dizionari.
}


# --- Funzioni di Caricamento Dizionari e Matching ---
def load_all_dicts_optimized(dir_path: Path):
    """
    Carica tutti i dizionari da una directory in modo ottimizzato.
    Usa KeywordProcessor per le frasi multi-parola.

    Ritorna:
      singles_category_map: Dict[str, Set[str]] - Mappa lemma normalizzato -> set di categorie
      multi_phrase_processor: KeywordProcessor - Processore per frasi multi-parola
    """
    singles_category_map: Dict[str, Set[str]] = {}
    multi_phrase_processor = KeywordProcessor(case_sensitive=False)

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

            if (" " in s) or ("_" in s) or ("-" in s):
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
    
    # Processa il testo con spaCy
    doc = nlp(requirement_text)

    # --- DEBUG: Stampa i POS tag per il requisito corrente (solo per R1, da rimuovere dopo debug) ---
    # Puoi adattare la condizione se vuoi vedere il debug solo per requisiti specifici
    # if "R1: 1" in requirement_text: # Condizione per filtrare il requisito R1
    #     print(f"\n--- DEBUG SPAy: Requisito '{requirement_text}' ---")
    #     for token in doc:
    #         print(f"Token: '{token.text}', Lemma: '{token.lemma_}', POS: '{token.pos_}', Tag: '{token.tag_}'")
    #     print("----------------------------------\n")
    # --- FINE DEBUG ---

    # 1. Ricerca di frasi multi-parola con Flashtext (prioritaria)
    multi_keywords_with_spans = multi_phrase_processor.extract_keywords(requirement_text, span_info=True)
    
    occupied_token_indices: Set[int] = set() 

    for match_category, start_char, end_char in multi_keywords_with_spans:
        original_matched_text = requirement_text[start_char:end_char]
        found_matches.append((original_matched_text, match_category, requirement_text))
        
        for token in doc:
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
            
            # Qui applichiamo la logica di spaCy e la mappa Categoria-POS
            matched_with_context = False
            
            # Prova a trovare una categoria che corrisponda al POS tag del token
            # Itera sulle categorie potenziali in ordine alfabetico per una certa consistenza
            # se una parola è in più dizionari con POS tag compatibili.
            for cat in sorted(list(potential_categories)):
                expected_pos_tags = POS_CATEGORY_MAPPING.get(cat)
                
                # --- DEBUG: per la parola "display" ---
                # if w_norm == "display" and "R1: 1" in requirement_text:
                #     print(f"[DEBUG - DISPLAY] Lemma 'display' trovato. POS tag spaCy: '{token.pos_}'")
                #     print(f"[DEBUG - DISPLAY] Categoria '{cat}': POS attesi nella mappa: {expected_pos_tags}. Il POS '{token.pos_}' è nel set: {token.pos_ in expected_pos_tags}")
                # --- FINE DEBUG ---

                if expected_pos_tags is not None and token.pos_ in expected_pos_tags:
                    found_matches.append((token.text, cat, requirement_text))
                    matched_with_context = True
                    break # Trovata la migliore corrispondenza contestuale, passa al prossimo token
            
            # Se la parola è presente nei dizionari ma non c'è una corrispondenza POS tag specifica
            # nella mappa, la ignoriamo per essere selettivi. Se vuoi un fallback, dovresti modificare qui.

    return found_matches

# --- Main Logic ---
if __name__ == "__main__":
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

    try:
        with open(REQUIREMENTS_FILE, 'r', encoding='utf-8') as req_f, \
             open(OUTPUT_FILE, 'w', encoding='utf-8', buffering=1000000) as out_f:
            
            out_f.write("ID;ID progetto;REQUISITO (testo);Classe dei requisiti;CATEGORIA;PAROLA\n")
            
            for line_num, line in enumerate(req_f, 1): 
                stripped_line = line.strip()
                
                if not stripped_line:
                    continue

                m = REQUIREMENT_LINE_PARSE_RX.match(stripped_line)
                if not m:
                    print(f"Avviso: Riga {line_num} non parsabile (ignorata): {stripped_line}")
                    continue

                req_id = m.group(1)
                proj_id = m.group(2)
                req_text = m.group(3)
                req_class = m.group(4)
                
                matches_for_current_req = tokenize_and_match_with_spacy(req_text, singles_category_map, multi_phrase_processor, nlp)
                
                unique_matches_for_this_req: Set[Tuple[str, str]] = set() 
                output_lines_for_this_req: List[str] = []

                base_output_parts = [req_id, proj_id, req_text, req_class]

                if not matches_for_current_req:
                    output_line = ";".join(base_output_parts + ["NULL", "NULL"]) + "\n"
                    out_f.write(output_line)
                else:
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