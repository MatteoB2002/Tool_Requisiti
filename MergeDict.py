import os

# Nomi dei file
file1_path = 'Vague_1.txt'
file2_path = 'Vagues_2.txt'
output_unione_path = 'vague.txt'
output_statistiche_path = 'statistiche_file_uniti.txt'

def leggi_parole_da_file(filepath):
    """
    Legge un file di testo e restituisce un set di parole uniche.
    Ogni parola viene "pulita" da spazi bianchi e resa minuscola.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # .strip() rimuove spazi e a capo all'inizio/fine di ogni riga
            # il costrutto { ... for ... } crea un set direttamente
            # if riga.strip() serve a ignorare le righe vuote
            parole = {riga.strip().lower() for riga in f if riga.strip()} #le inserisce in un set per evitare duplicati
        return parole
    except FileNotFoundError:
        print(f"ERRORE: Il file '{filepath}' non è stato trovato.")
        # Restituisce un set vuoto per evitare che lo script si blocchi
        return set()


# Legge le parole da ciascun file e le mette in un set
parole_set_1 = leggi_parole_da_file(file1_path)
parole_set_2 = leggi_parole_da_file(file2_path)

# Se uno dei file non è stato trovato, interrompe l'esecuzione
if not parole_set_1 and not parole_set_2:
    print("Entrambi i file di input sono vuoti o non trovati. Script terminato.")
else:
    #  Operazioni con i set per creare il file di output e le statistiche

    # Unione: tutte le parole di entrambi i file, senza duplicati
    parole_totali_uniche = parole_set_1.union(parole_set_2)

    # Intersezione: solo le parole presenti in entrambi i file
    parole_in_comune = parole_set_1.intersection(parole_set_2)

    # Differenza: parole presenti solo nel primo file (non nel secondo)
    parole_solo_in_file1 = parole_set_1.difference(parole_set_2)

    # Differenza: parole presenti solo nel secondo file (non nel primo)
    parole_solo_in_file2 = parole_set_2.difference(parole_set_1)

    # Calcola i numeri per le statistiche
    num_parole_comuni = len(parole_in_comune)
    num_parole_totali_uniche = len(parole_totali_uniche)
    num_parole_uniche_file1 = len(parole_solo_in_file1)
    num_parole_uniche_file2 = len(parole_solo_in_file2)

    # Calcola la percentuale (evitando la divisione per zero se non ci sono parole)
    percentuale_comuni = 0
    if num_parole_totali_uniche > 0:
        percentuale_comuni = (num_parole_comuni / num_parole_totali_uniche) * 100

    # Scrive il file con l'unione delle parole senza duplicati grazie all'uso del set
    # Ordina le parole alfabeticamente per un output più pulito
    parole_ordinate = sorted(list(parole_totali_uniche))

    with open(output_unione_path, 'w', encoding='utf-8') as f:
        for parola in parole_ordinate:
            f.write(f"{parola}\n")
    print(f"File '{output_unione_path}' creato con successo con {num_parole_totali_uniche} parole uniche.")

    #Crea il report delle statistiche
    if parole_in_comune:
        # Creiamo una lista di stringhe, dove ogni stringa è "- parola"
        lista_comuni_formattata = [f"- {p}" for p in sorted(list(parole_in_comune))]
        # Uniamo gli elementi della lista con il carattere "a capo" (\n)
        # Aggiungiamo un \n all'inizio per separare il titolo dalla lista
        elenco_comuni_stringa = "\n" + "\n".join(lista_comuni_formattata)
    else:
        elenco_comuni_stringa = " Nessuna" # Mettiamo uno spazio per allinearlo ai ":"

    # Crea il report delle statistiche
    report = (
        f"--- Statistiche di Confronto File ---\n\n"
        f"File 1: '{file1_path}'\n"
        f"File 2: '{file2_path}'\n"
        f"-------------------------------------\n\n"
        f"Numero di parole in comune: {num_parole_comuni}\n"
        f"Percentuale parole comuni sul totale delle parole uniche: {percentuale_comuni:.2f}%\n\n"
        f"Numero di parole presenti SOLO nel primo file: {num_parole_uniche_file1}\n"
        f"Numero di parole presenti SOLO nel secondo file: {num_parole_uniche_file2}\n\n"
        f"Elenco parole in comune:{elenco_comuni_stringa}\n" 
    )
    #Stampa il report a schermo
    print("\n--- STATISTICHE ---")
    print(report)

    #Scrive il report sul file delle statistiche
    with open(output_statistiche_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"File di statistiche '{output_statistiche_path}' creato con successo.")