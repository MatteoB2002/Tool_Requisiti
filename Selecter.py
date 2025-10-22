import csv
import random
from pathlib import Path

# --- Configurazione ---
INPUT_DIR = Path("Sorted_by_Categories")
OUTPUT_FILE = "Requisiti_Selezionati.csv"
SAMPLE_SIZE = 27

def create_final_sample_set():
    """
    Scansiona la directory di input, campiona casualmente un numero fisso di requisiti
    da ogni file di categoria e li consolida in un unico file CSV di output.
    """
    print("--- Inizio Script di Campionamento Casuale ---")

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

                        # --- Logica di Campionamento ---
                        num_rows_in_file = len(all_rows)
                        
                        if num_rows_in_file <= SAMPLE_SIZE:
                            # Se ci sono 27 o meno requisiti, li prendiamo tutti
                            print(f"  -> Trovati {num_rows_in_file} requisiti (meno di {SAMPLE_SIZE}). Selezionati tutti.")
                            sampled_rows = all_rows
                        else:
                            # Se ce ne sono più di 27, ne selezioniamo 27 a caso
                            print(f"  -> Trovati {num_rows_in_file} requisiti. Selezionando {SAMPLE_SIZE} a caso.")
                            sampled_rows = random.sample(all_rows, SAMPLE_SIZE)

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
    print(f"Il file contiene un campione di (fino a) {SAMPLE_SIZE} requisiti da ognuna delle {len(category_files)} categorie.")


# Esegui la funzione principale quando lo script viene lanciato
if __name__ == "__main__":
    create_final_sample_set()