import re
from pathlib import Path
# RIMOSSO: import tokenize  <--- Questa riga causava il problema!
from typing import Dict, Set, List, Tuple
from flashtext import KeywordProcessor

# Espressione regolare per estrarre singole parole dal testo dei requisiti
WORD_RX = re.compile(r"\b\w+\b", flags=re.UNICODE)

# Regex per parsare la riga del requisito nel formato R<ID>: <ID_PROGETTO>,'<TESTO>',<CLASSE>
# Group 1: ID Requisito (es. R1)
# Group 2: ID Progetto (es. 1)
# Group 3: Testo del Requisito (es. 'The system shall...')
# Group 4: Classe dei requisiti (es. PE)
REQUIREMENT_LINE_PARSE_RX = re.compile(r"^(R\d+):\s*(\d+),\s*'(.*?)',\s*([A-Za-z0-9_]+)\s*$")

def norm_word(s: str) -> str:
    """Normalizza una singola parola (minuscolo, senza spazi)."""
    return s.casefold().strip()

def norm_phrase(s: str) -> str:
    """
    Normalizza una frase multi-parola:
    - Sostituisce underscore con spazi.
    - Sostituisce trattini con spazi (per trattare "all-out" come "all out").
    - Comprime spazi multipli.
    - Converte in minuscolo.
    """
    s = s.replace("_", " ").replace("-", " ")
    return " ".join(s.split()).casefold()

def load_all_dicts_optimized(dir_path: Path):
    """
    Carica tutti i dizionari da una directory in modo ottimizzato.
    Usa KeywordProcessor per le frasi multi-parola.

    Ritorna:
      singles_category_map: Dict[str, Set[str]] - Mappa parola normalizzata -> set di categorie
      multi_phrase_processor: KeywordProcessor - Processore per frasi multi-parola
      # original_phrase_map: Dict[str, str] - Mappa frase normalizzata -> frase originale (per output)
    
    """
    singles_category_map: Dict[str, Set[str]] = {}
    multi_phrase_processor = KeywordProcessor(case_sensitive=False)
    # original_phrase_map non viene più passata direttamente

    print(f"Caricamento dizionari ottimizzato dalla directory: {dir_path}")
    if not dir_path.is_dir():
        print(f"[ERRORE] La directory dei dizionari '{dir_path}' non esiste o non è una directory valida.")
        return singles_category_map, multi_phrase_processor, {} # Restituisci anche una mappa vuota

    dict_files_found = list(dir_path.glob("*.txt"))
    if not dict_files_found:
        print(f"[AVVISO] Nessun file .txt trovato nella directory dizionari: {dir_path}. Assicurati che i file abbiano estensione .txt")

    for path in sorted(dir_path.glob("*.txt")):
        categoria = path.stem
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
                w_norm = norm_word(s)
                singles_category_map.setdefault(w_norm, set()).add(categoria)
                words_added += 1
        print(f"    [DEBUG] Lette {lines_read} righe. Aggiunte {phrases_added} frasi e {words_added} parole singole per la categoria '{categoria}'.")
    
    print(f"  Caricate {len(singles_category_map)} parole singole e {len(multi_phrase_processor.get_all_keywords())} frasi multi-parola.")
    return singles_category_map, multi_phrase_processor, {} # original_phrase_map è stata rimossa dalla logica attiva

def get_words_from_text(text: str) -> Set[str]: # Rinomino la funzione per evitare futuri conflitti
    """Estrae e normalizza tutte le parole singole da un testo."""
    return {norm_word(w) for w in WORD_RX.findall(text)}

def tokenize_and_match(requirement_text: str,
                       singles_category_map: Dict[str, Set[str]],
                       multi_phrase_processor: KeywordProcessor) -> List[Tuple[str, str, str]]:
    """
    Trova tutte le corrispondenze (singole parole e frasi multi-parola) in un requisito.

    Ritorna:
      List[Tuple[str, str, str]] - Lista di tuple (parola/frase trovata_originale, categoria, testo_requisito_originale)
    """
    
    found_matches: List[Tuple[str, str, str]] = []
    
    # Ricerca di frasi multi-parola con Flashtext
    multi_keywords_with_spans = multi_phrase_processor.extract_keywords(requirement_text, span_info=True)
    
    for match_category, start_idx, end_idx in multi_keywords_with_spans:
        original_matched_text = requirement_text[start_idx:end_idx]
        found_matches.append((original_matched_text, match_category, requirement_text))

    # Ricerca di parole singole
    words_in_req = get_words_from_text(requirement_text) # Uso la funzione rinominata qui
    for w_norm in words_in_req:
        if w_norm in singles_category_map:
            for cat in singles_category_map[w_norm]:
                found_matches.append((w_norm, cat, requirement_text))
    
    return found_matches

# --- Main Logic ---
if __name__ == "__main__":
    DICTIONARIES_DIR = Path("NewDict") 
    REQUIREMENTS_FILE = "Dataset_With_R_ID.txt"  
    OUTPUT_FILE = "Labeled_Dataset.csv"    # L'output rimane CSV

    # 1. Carica i dizionari in modo ottimizzato
    # Non passiamo più original_phrase_map a load_all_dicts_optimized come terzo parametro
    # e non la usiamo più in tokenize_and_match.
    singles_category_map, multi_phrase_processor, _ = load_all_dicts_optimized(DICTIONARIES_DIR)
    
    total_single_words = len(singles_category_map)
    total_multi_phrases = len(multi_phrase_processor.get_all_keywords())

    if not (total_single_words or total_multi_phrases):
        print("Attenzione: Nessuna parola o frase è stata caricata dai dizionari. Controlla la directory e i file.")
        exit()
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
                
                # Modificata la chiamata a tokenize_and_match rimuovendo original_phrase_map
                matches_for_current_req = tokenize_and_match(req_text, singles_category_map, multi_phrase_processor)
                
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
                            matches_found_total += 1 # Aggiorna il contatore dei match trovati
                    
                    out_f.writelines(output_lines_for_this_req)
                
                processed_req_count += 1
                if processed_req_count % 100 == 0:
                    print(f"  [PROGRESSO] Processati {processed_req_count} requisiti...")

    except FileNotFoundError:
        print(f"Errore: Il file dei requisiti '{REQUIREMENTS_FILE}' non trovato.")
    except Exception as e:
        # Stampiamo l'errore completo per debugging
        import traceback
        print(f"Si è verificato un errore inaspettato durante l'elaborazione: {e}")
        traceback.print_exc() # Stampa il traceback completo
        
    print(f"\nElaborazione completata. I risultati sono stati scritti in '{OUTPUT_FILE}'.")
    print(f"Match totali trovati e scritti: {matches_found_total}")