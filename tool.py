import re 
from pathlib import Path 
from typing import Dict, Set, List, Tuple 
from flashtext import KeywordProcessor 
import spacy 
import csv
import traceback 

# Configurazione e Modello spaCy
SPACY_MODEL_NAME = "en_core_web_sm"

try:
    nlp = spacy.load(SPACY_MODEL_NAME)
    print(f"[DEBUG] Modello spaCy '{SPACY_MODEL_NAME}' caricato con successo.")
except OSError:
    print(f"Errore: Modello spaCy '{SPACY_MODEL_NAME}' non trovato.")
    print(f"Assicurati di averlo installato eseguendo: python -m spacy download {SPACY_MODEL_NAME}")
    exit(1)

REQUIREMENT_LINE_PARSE_RX = re.compile(r"^(R\d+):\s*(\d+),\s*'(.*?)',\s*([A-Za-z0-9_]+)\s*$")

def norm_word(s: str) -> str:
    return s.casefold().strip()

def norm_phrase(s: str) -> str:
    # Normalizza spazi e trattini
    s = s.replace("_", " ").replace("-", " ")
    return " ".join(s.split()).casefold()

# --- Lista di Priorità delle Categorie (determina quale vince se una parola è in più file) ---
CATEGORY_PRIORITY = [
    "vpastp", "vpastt", "vpresentp",
    "pv", "mv", "weak",
    "plurals", "continuance", "directive", "incompletes", "optional", "vague",
    "coordinator", "qualifier",
    "verb", "noun", "adj", "adv", "pronoun", "det", "preposition", "conjunction"
]

def get_priority_index(category: str) -> int:
    """Restituisce l'indice di priorità (più basso = più importante)"""
    cat_lower = category.lower()
    try:
        return CATEGORY_PRIORITY.index(cat_lower)
    except ValueError:
        return 999  # Priorità bassa se non in lista

# Funzioni di Caricamento Dizionari
def load_all_dicts_optimized(dir_path: Path):
    """
    Carica i dizionari.
    - Se una stringa ha spazi O punteggiatura (es. 'i.e.'), va in FlashText (multi_phrase_processor).
    - Se è una parola alfanumerica pulita, va nella mappa per lemmatizzazione (singles_category_map).
    """
    singles_category_map: Dict[str, Set[str]] = {}
    multi_phrase_processor = KeywordProcessor(case_sensitive=False)

    print(f"Caricamento dizionari ottimizzato dalla directory: {dir_path}")
    if not dir_path.is_dir():
        print(f"[ERRORE] La directory '{dir_path}' non esiste.")
        return singles_category_map, multi_phrase_processor

    dict_files_found = list(dir_path.glob("*.txt"))
    
    for path in sorted(dict_files_found):
        categoria = path.stem.lower()
        
        if not path.is_file():
            continue
        
        phrases_added, words_added = 0, 0
        try:
            content = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            # Fallback per encoding diversi
            content = path.read_text(encoding="latin-1").splitlines()

        for line in content:
            s = line.strip()
            if not s or s.startswith("---"): # Salta intestazioni o righe vuote
                continue

            # Logica migliorata:
            # Se contiene spazi O caratteri non alfanumerici (es. punti in 'i.e.'), usa FlashText
            # FlashText gestisce meglio la punteggiatura rispetto al tokenizer di singole parole.
            if " " in s or "_" in s or "-" in s or "." in s or "/" in s:
                p_norm = norm_phrase(s)
                # FlashText non permette di assegnare liste, quindi se c'è duplicato sovrascrive.
                # Per gestire priorità in FlashText, dovremmo aggiungere keywords multiple, 
                # ma qui semplifichiamo assegnando la categoria corrente.
                # (FlashText preferisce la stringa più lunga, quindi 'as well as' vince su 'as')
                multi_phrase_processor.add_keyword(p_norm, categoria)
                phrases_added += 1
            else:
                # Parole singole alfanumeriche (es. 'table', 'test')
                w_norm = norm_word(s)
                singles_category_map.setdefault(w_norm, set()).add(categoria)
                words_added += 1
                
        print(f"    Cat '{categoria}': {phrases_added} frasi/speciali, {words_added} parole semplici.")
    
    return singles_category_map, multi_phrase_processor


def tokenize_and_match_robust(requirement_text: str,
                              singles_category_map: Dict[str, Set[str]],
                              multi_phrase_processor: KeywordProcessor,
                              nlp) -> List[Tuple[str, str, str]]:
    
    found_matches: List[Tuple[str, str, str]] = []
    
    # 1. FlashText: Trova frasi multi-parola E parole speciali con punteggiatura (es. "i.e.")
    # span_info=True ci dà (start, end)
    multi_keywords_with_spans = multi_phrase_processor.extract_keywords(requirement_text, span_info=True)
    
    # Set per tracciare le posizioni dei caratteri già occupati da FlashText
    occupied_char_indices = set()
    
    for match_category, start_char, end_char in multi_keywords_with_spans:
        original_matched_text = requirement_text[start_char:end_char]
        found_matches.append((original_matched_text, match_category, requirement_text))
        
        # Marcare gli indici come occupati per non sovrapporre con spaCy
        for i in range(start_char, end_char):
            occupied_char_indices.add(i)

    # 2. spaCy: Trova parole singole e lemmi (es. "tables" -> match con "table")
    doc = nlp(requirement_text)
    
    for token in doc:
        # Se il token cade in un'area già trovata da FlashText (es. parte di "i.e." o "as well as"), saltalo
        if token.idx in occupied_char_indices:
            continue
        
        # Candidati per il match
        potential_categories = set()
        
        # A) Match esatto parola (priority alta)
        w_original = norm_word(token.text)
        if w_original in singles_category_map:
            potential_categories.update(singles_category_map[w_original])
            
        # B) Match lemma (es. "running" -> "run", "tables" -> "table")
        w_lemma = norm_word(token.lemma_)
        if w_lemma in singles_category_map:
            potential_categories.update(singles_category_map[w_lemma])

        if potential_categories:
            # Abbiamo trovato la parola nei dizionari.
            # ORA NON FILTRIAMO PIÙ PER POS TAG.
            # Selezioniamo solo la categoria con la priorità più alta.
            
            best_category = sorted(list(potential_categories), key=get_priority_index)[0]
            found_matches.append((token.text, best_category, requirement_text))

    return found_matches

# --- Main Logic ---
if __name__ == "__main__":
    DICTIONARIES_DIR = Path("NewDict") 
    REQUIREMENTS_FILE = "Dataset_With_R_ID.txt"  
    OUTPUT_FILE = "Labeled_Dataset.csv" 

    singles_category_map, multi_phrase_processor = load_all_dicts_optimized(DICTIONARIES_DIR)
    
    if not (singles_category_map or multi_phrase_processor.get_all_keywords()):
        print("Attenzione: Nessuna parola caricata. Controlla il percorso 'NewDict'.")
        exit(0)

    print(f"\nProcessamento requisiti dal file: {REQUIREMENTS_FILE}")
    
    matches_found_total = 0

    try:
        with open(REQUIREMENTS_FILE, 'r', encoding='utf-8') as req_f, \
             open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as out_f:
            
            csv_writer = csv.writer(out_f, delimiter=';')
            header = ["ID", "ID progetto", "REQUISITO (testo)", "Classe dei requisiti", "CATEGORIA", "PAROLA"]
            csv_writer.writerow(header)
            
            for line in req_f: 
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                m = REQUIREMENT_LINE_PARSE_RX.match(stripped_line)
                if not m:
                    # Gestione righe che non matchano la regex (opzionale)
                    continue

                req_id, proj_id, req_text, req_class = m.groups()
                
                matches = tokenize_and_match_robust(req_text, singles_category_map, multi_phrase_processor, nlp)
                
                base_row = [req_id, proj_id, req_text, req_class]

                if not matches:
                    csv_writer.writerow(base_row + ["NULL", "NULL"])
                else:
                    # Usiamo un set per evitare duplicati identici nella stessa riga (es. due volte la stessa parola)
                    # O rimuovere il set se vuoi una riga per ogni singola occorrenza anche se ripetuta
                    unique_matches = set()
                    for word_found, category, _ in matches:
                        # Chiave univoca: Categoria + Parola Trovata
                        if (category, word_found) not in unique_matches:
                            csv_writer.writerow(base_row + [category, word_found])
                            unique_matches.add((category, word_found))
                            matches_found_total += 1
                
    except FileNotFoundError:
        print(f"Errore: File '{REQUIREMENTS_FILE}' non trovato.")
    except Exception as e:
        traceback.print_exc()

    print(f"\nFinito. Match totali scritti: {matches_found_total}")