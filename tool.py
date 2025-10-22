import re 
from pathlib import Path 
from typing import Dict, Set, List, Tuple 
from flashtext import KeywordProcessor 
import spacy 
import csv
import traceback 

#Configurazione e Modello spaCy
SPACY_MODEL_NAME = "en_core_web_sm"

try:
    nlp = spacy.load(SPACY_MODEL_NAME)
    print(f"[DEBUG] Modello spaCy '{SPACY_MODEL_NAME}' caricato con successo.")
except OSError:
    print(f"Errore: Modello spaCy '{SPACY_MODEL_NAME}' non trovato.")
    print(f"Assicurati di averlo installato eseguendo: python -m spacy download {SPACY_MODEL_NAME}")
    exit(1)

WORD_RX = re.compile(r"\b\w+\b", flags=re.UNICODE) 
REQUIREMENT_LINE_PARSE_RX = re.compile(r"^(R\d+):\s*(\d+),\s*'(.*?)',\s*([A-Za-z0-9_]+)\s*$")

def norm_word(s: str) -> str:
    return s.casefold().strip()

def norm_phrase(s: str) -> str:
    s = s.replace("_", " ").replace("-", " ")
    return " ".join(s.split()).casefold()

# --- Mappatura Categorie-POS Tag SPECIFICA PER I  FILE DI DIZIONARIO ---
POS_CATEGORY_MAPPING = {
    "adj": {"pos": {"ADJ"}},
    "adv": {"pos": {"ADV"}},
    "conjunction": {"pos": {"CCONJ", "SCONJ"}},
    "det": {"pos": {"DET", "PRON"}},
    "noun": {"pos": {"NOUN", "PROPN"}},
    "preposition": {"pos": {"ADP"}},
    "pronoun": {"pos": {"PRON"}},
    "plurals": {"pos": {"NOUN"}},
    "continuance": {"pos": {"ADV","ADJ" "SCONJ", "CCONJ"}},
    "incompletes": {"pos": {"ADJ", "NOUN", "ADV"}},
    "vague": {"pos": {"ADJ", "DET", "ADV"}},
    "mv": {"tag": {"MD"}},
    "pv": {"tag": {"VB", "VBP", "VBZ"}},
    "vpastp": {"tag": {"VBN"}},
    "vpastt": {"tag": {"VBD"}},
    "vpresentp": {"tag": {"VBG"}},
    "directive": {"tag": {"MD", "VB"}},
    # --- MODIFICA CHIAVE: La regola per "optional" è ora molto più completa ---
    "optional": {"pos": {"ADV", "CCONJ", "SCONJ"}, "tag": {"MD"}},
    "verb": {"tag": {"VB", "VBP", "VBZ", "VBD", "VBN", "VBG"}}
}

# --- Lista di Priorità delle Categorie ---
CATEGORY_PRIORITY = [
    "vpastp", "vpastt", "vpresentp",
    "pv", "mv",
    "plurals", "continuance", "directive", "incompletes", "optional", "vague",
    "verb", "noun", "adj", "adv", "pronoun", "det", "preposition", "conjunction"
]

# Funzioni di Caricamento Dizionari e Matching 
def load_all_dicts_optimized(dir_path: Path):
    singles_category_map: Dict[str, Set[str]] = {}
    multi_phrase_processor = KeywordProcessor(case_sensitive=False)

    print(f"Caricamento dizionari ottimizzato dalla directory: {dir_path}")
    if not dir_path.is_dir():
        print(f"[ERRORE] La directory dei dizionari '{dir_path}' non esiste o non è una directory valida.")
        return singles_category_map, multi_phrase_processor

    dict_files_found = list(dir_path.glob("*.txt"))
    if not dict_files_found:
        print(f"[AVVISO] Nessun file .txt trovato nella directory dizionari: {dir_path}.")

    for path in sorted(dict_files_found):
        categoria = path.stem.lower()
        print(f"  Caricamento categoria: '{categoria}' da '{path.name}'")

        if not path.is_file():
            print(f"    [ERRORE] Il file '{path.name}' non è un file valido.")
            continue
        
        lines_read, phrases_added, words_added = 0, 0, 0
        for line in path.read_text(encoding="utf-8").splitlines():
            lines_read += 1
            s = line.strip()
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
    return singles_category_map, multi_phrase_processor



def tokenize_and_match_with_spacy(requirement_text: str,
                                   singles_category_map: Dict[str, Set[str]],
                                   multi_phrase_processor: KeywordProcessor,
                                   nlp) -> List[Tuple[str, str, str]]:
    found_matches: List[Tuple[str, str, str]] = []
    doc = nlp(requirement_text)
    occupied_token_indices: Set[int] = set()

    # 1. Ricerca di frasi multi-parola (prioritaria)
    multi_keywords_with_spans = multi_phrase_processor.extract_keywords(requirement_text, span_info=True)
    for match_category, start_char, end_char in multi_keywords_with_spans:
        original_matched_text = requirement_text[start_char:end_char]
        found_matches.append((original_matched_text, match_category, requirement_text))
        
        for token in doc:
            if (token.idx < end_char and token.idx + len(token.text) > start_char):
                occupied_token_indices.add(token.i)

    # 2. Ricerca di parole singole con NUOVA STRATEGIA A DUE PASSATE
    for token in doc:
        if token.i in occupied_token_indices:
            continue

        # --- FASE 1: Ricerca della PAROLA ORIGINALE (token.text) ---
        # Questa ha la priorità perché è più specifica (es. cerca "allowed")
        w_original = norm_word(token.text)
        potential_categories = singles_category_map.get(w_original, set())
        
        # --- FASE 2: Ricerca del LEMMA (token.lemma_) ---
        # Se non troviamo la parola originale, o per coprire varianti (es. plurale), cerchiamo il lemma.
        w_lemma = norm_word(token.lemma_)
        if w_original != w_lemma:
            potential_categories.update(singles_category_map.get(w_lemma, set()))

        # Se abbiamo trovato delle categorie candidate (o dalla parola originale o dal lemma)
        if potential_categories:
            
            def get_priority(category):
                try:
                    return CATEGORY_PRIORITY.index(category.lower())
                except ValueError:
                    return len(CATEGORY_PRIORITY)

            sorted_categories = sorted(list(potential_categories), key=get_priority)

            for cat in sorted_categories:
                rule = POS_CATEGORY_MAPPING.get(cat.lower())

                if rule is None:
                    continue

                match_found = False
                if "pos" in rule and token.pos_ in rule["pos"]:
                    match_found = True
                elif "tag" in rule and token.tag_ in rule["tag"]:
                    match_found = True
                
                if match_found:
                    found_matches.append((token.text, cat, requirement_text))
                    break # Trovata la migliore corrispondenza, esci

    return found_matches

# --- Main Logic ---
if __name__ == "__main__":
    DICTIONARIES_DIR = Path("NewDict") 
    REQUIREMENTS_FILE = "Dataset_With_R_ID.txt"  
    OUTPUT_FILE = "Labeled_Dataset.csv" 

    singles_category_map, multi_phrase_processor = load_all_dicts_optimized(DICTIONARIES_DIR)
    
    if not (singles_category_map or multi_phrase_processor.get_all_keywords()):
        print("Attenzione: Nessuna parola o frase è stata caricata dai dizionari.")
        exit(0)

    print(f"\nProcessamento requisiti dal file: {REQUIREMENTS_FILE}")
    processed_req_count = 0
    matches_found_total = 0

    try:
        with open(REQUIREMENTS_FILE, 'r', encoding='utf-8') as req_f, \
             open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as out_f:
            
            csv_writer = csv.writer(out_f, delimiter=';')
            header = ["ID", "ID progetto", "REQUISITO (testo)", "Classe dei requisiti", "CATEGORIA", "PAROLA"]
            csv_writer.writerow(header)
            
            for line_num, line in enumerate(req_f, 1): 
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                m = REQUIREMENT_LINE_PARSE_RX.match(stripped_line)
                if not m:
                    print(f"Avviso: Riga {line_num} non parsabile (ignorata): {stripped_line}")
                    continue

                req_id, proj_id, req_text, req_class = m.groups()
                
                matches_for_current_req = tokenize_and_match_with_spacy(req_text, singles_category_map, multi_phrase_processor, nlp)
                
                base_output_parts = [req_id, proj_id, req_text, req_class]

                if not matches_for_current_req:
                    csv_writer.writerow(base_output_parts + ["NULL", "NULL"])
                else:
                    unique_matches_for_this_req: Set[Tuple[str, str]] = set() 
                    for original_word_phrase, category, _ in matches_for_current_req:
                        if (category, original_word_phrase) not in unique_matches_for_this_req:
                            csv_writer.writerow(base_output_parts + [category, original_word_phrase])
                            unique_matches_for_this_req.add((category, original_word_phrase))
                            matches_found_total += 1
                
                processed_req_count += 1
                if processed_req_count % 100 == 0:
                    print(f"  [PROGRESSO] Processati {processed_req_count} requisiti...")

    except FileNotFoundError:
        print(f"Errore: Il file dei requisiti '{REQUIREMENTS_FILE}' non trovato.")
        exit(1)
    except Exception as e:
        print(f"Si è verificato un errore inaspettato durante l'elaborazione: {e}")
        traceback.print_exc()
        exit(1)
        
    print(f"\nElaborazione completata. I risultati sono stati scritti in '{OUTPUT_FILE}'.")
    print(f"Match totali univoci trovati e scritti: {matches_found_total}")