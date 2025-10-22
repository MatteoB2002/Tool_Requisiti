import csv
from collections import defaultdict
from pathlib import Path

# --- Configurazione ---
INPUT_FILE = Path("Labeled_Dataset.csv")
OUTPUT_DIR = Path("Sorted_by_Categories")

def group_and_write_files_by_category():
    """
    Legge Labeled_Dataset.csv, raggruppa i requisiti per categoria
    e scrive un file CSV separato per ogni categoria in una nuova directory.
    """
    
    # defaultdict ci permette di raggruppare facilmente.
    # La struttura sarà: {'categoria1': [riga1, riga2], 'categoria2': [riga3]}
    # dove ogni 'riga' è una lista di stringhe (le colonne del CSV).
    grouped_data = defaultdict(list)
    header = []

    print(f"Inizio elaborazione: lettura del file '{INPUT_FILE}'...")

    # --- 1. Lettura e Raggruppamento dei Dati ---
    try:
        with open(INPUT_FILE, mode='r', encoding='utf-8', newline='') as infile:
            reader = csv.reader(infile, delimiter=';')
            
            # Leggiamo e salviamo l'intestazione, è cruciale per i file di output
            try:
                header = next(reader)
                category_col_index = header.index("CATEGORIA")
            except (StopIteration, ValueError) as e:
                print(f"Errore: Impossibile leggere l'intestazione o trovare la colonna 'CATEGORIA' in '{INPUT_FILE}'. ({e})")
                return

            # Iteriamo sulle righe di dati
            rows_processed = 0
            for row in reader:
                if not row or len(row) <= category_col_index:
                    continue
                
                category = row[category_col_index]
                
                # Aggiungiamo la riga al gruppo corretto, escludendo i 'NULL'
                if category != "NULL":
                    grouped_data[category].append(row)
                
                rows_processed += 1
            
            print(f"Lette {rows_processed} righe di dati. Trovate {len(grouped_data)} categorie valide.")

    except FileNotFoundError:
        print(f"ERRORE: File di input '{INPUT_FILE}' non trovato.")
        print("Assicurati che lo script 'tool.py' sia stato eseguito correttamente.")
        return
    except Exception as e:
        print(f"Si è verificato un errore inaspettato durante la lettura del file: {e}")
        return

    if not grouped_data:
        print("Nessun requisito con categorie valide trovato. Nessun file verrà creato.")
        return

    # --- 2. Creazione della Directory di Output ---
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Directory di output '{OUTPUT_DIR}' creata o già esistente.")
    except Exception as e:
        print(f"Errore critico: Impossibile creare la directory di output '{OUTPUT_DIR}'. Errore: {e}")
        return

    # --- 3. Scrittura dei File Separati per Categoria ---
    files_created_count = 0
    print("Inizio scrittura dei file separati per categoria...")

    # Iteriamo su ogni categoria e sulla sua lista di righe
    for category, rows_in_category in grouped_data.items():
        # Creiamo un nome di file sicuro per la categoria (es. 'functional_requirement.csv')
        # Sostituiamo spazi o caratteri non validi se necessario, anche se i nomi delle tue categorie sono semplici.
        safe_category_name = category.lower().replace(" ", "_")
        output_filename = f"{safe_category_name}_requirements.csv"
        output_filepath = OUTPUT_DIR / output_filename
        
        try:
            with open(output_filepath, mode='w', encoding='utf-8', newline='') as outfile:
                writer = csv.writer(outfile, delimiter=';')
                
                # Scriviamo l'intestazione in ogni file
                writer.writerow(header)
                
                # Scriviamo tutte le righe per questa specifica categoria
                writer.writerows(rows_in_category)
            
            print(f"  -> Creato file '{output_filepath}' con {len(rows_in_category)} requisiti.")
            files_created_count += 1
        except Exception as e:
            print(f"  -> ERRORE durante la scrittura del file per la categoria '{category}': {e}")

    print(f"\nElaborazione completata! Creati {files_created_count} file nella directory '{OUTPUT_DIR}'.")


# Esegui la funzione principale quando lo script viene lanciato
if __name__ == "__main__":
    group_and_write_files_by_category()