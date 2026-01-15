import csv
import random
from pathlib import Path

# --- Configurazione ---
INPUT_DIR = Path("Sorted_by_Categories")
OUTPUT_FILE = "Requisiti_Selezionati_Percentuale.csv"

# Percentuale di righe da selezionare 
SAMPLE_PERCENTAGE = 0.20 

def create_final_sample_set():
    """
    Scansiona la directory di input, campiona una percentuale (20%) di requisiti
    da ogni file di categoria e li consolida in un unico file CSV di output.
    """
    print(f"--- Inizio Script di Campionamento Casuale ({int(SAMPLE_PERCENTAGE*100)}%) ---")

    # --- 1. Controlli Preliminari ---
    if not INPUT_DIR.is_dir():
        print(f"ERRORE: La directory di input '{INPUT_DIR}' non è stata trovata.")
        print("Assicurati di aver eseguito prima lo script che crea i file per categoria.")
        return

    # Trova tutti i file CSV nella directory di input
    category_files = sorted(list(INPUT_DIR.glob("*.csv")))
    if not category_files:
        print(f"ERRORE: Nessun file .csv trovato nella directory '{INPUT_DIR}'.")
        return

    print(f"Trovati {len(category_files)} file di categoria da processare.")

    # --- 2. Processo di Campionamento e Scrittura ---
    header_written = False
    total_selected_rows = 0

    try:
        # Apriamo il file di output in modalità scrittura
        with open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as outfile:
            csv_writer = csv.writer(outfile, delimiter=';')

            # Iteriamo su ogni file di categoria trovato
            for filepath in category_files:
                print(f"\nProcessando il file: '{filepath.name}'...")

                try:
                    with open(filepath, mode='r', encoding='utf-8', newline='') as infile:
                        csv_reader = csv.reader(infile, delimiter=';')
                        
                        # Leggiamo l'intestazione e i dati
                        header = next(csv_reader)
                        all_rows = list(csv_reader) # Leggiamo tutte le righe di dati in una lista
                        
                        # Scriviamo l'intestazione nel file di output, ma solo una volta
                        if not header_written:
                            csv_writer.writerow(header)
                            header_written = True
                        
                        if not all_rows:
                            print("  -> File vuoto (solo intestazione). Saltato.")
                            continue

                        # --- Logica di Campionamento Percentuale ---
                        num_rows_in_file = len(all_rows)
                        
                        # Calcolo quante righe prendere (arrotondamento all'intero più vicino)
                        rows_to_sample_count = int(round(num_rows_in_file * SAMPLE_PERCENTAGE))
                        
                        # Sicurezza: Se il file non è vuoto ma il 20% è < 1 (es. file da 2 righe),
                        # ne prendiamo comunque almeno 1 per rappresentanza.
                        if rows_to_sample_count < 1 and num_rows_in_file > 0:
                            rows_to_sample_count = 1

                        print(f"  -> Totale righe: {num_rows_in_file}. Seleziono {rows_to_sample_count} righe (circa {int(SAMPLE_PERCENTAGE*100)}%).")
                        
                        # Eseguiamo il campionamento
                        sampled_rows = random.sample(all_rows, rows_to_sample_count)

                        # Scriviamo le righe campionate nel file di output
                        csv_writer.writerows(sampled_rows)
                        total_selected_rows += len(sampled_rows)

                except StopIteration:
                     print(f"  -> AVVISO: Il file '{filepath.name}' sembra essere completamente vuoto. Saltato.")
                except Exception as e:
                     print(f"  -> ERRORE durante la lettura del file '{filepath.name}': {e}")

    except Exception as e:
        print(f"\nERRORE CRITICO durante la scrittura del file di output '{OUTPUT_FILE}': {e}")
        return

    print("\n--- Elaborazione Completata ---")
    print(f"Creato il file '{OUTPUT_FILE}' con un totale di {total_selected_rows} requisiti campionati.")



if __name__ == "__main__":
    create_final_sample_set()