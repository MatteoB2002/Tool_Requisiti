#!/usr/bin/env python3
import re
from pathlib import Path

ID_REGEX = re.compile(r"^(R\d+)\s*:\s*(.*)$", flags=re.IGNORECASE)

def add_ids_to_requirements(
    in_path: Path,
    out_path: Path,
    prefix: str = "R",
    start_from: int = 1,
    keep_blank_lines: bool = False,
    skip_if_already_tagged: bool = True,
):
    """
    Legge requisiti (uno per riga) da in_path, aggiunge ID progressivi e scrive su out_path.
    """
    counter = start_from
    written = 0

    with in_path.open("r", encoding="utf-8") as f, \
         out_path.open("w", encoding="utf-8") as fout:
        
        for raw in f:
            line = raw.strip()

            # righe vuote
            if not line:
                if keep_blank_lines:
                    fout.write("\n")  # preserva riga vuota
                continue

            # salta commenti che iniziano con % o @
            if line.startswith(("%", "@")):
                #fout.write(f"{line}\n")
                continue

            # già taggato?
            m = ID_REGEX.match(line)
            if m:
                if skip_if_already_tagged:
                    existing_id, rest = m.group(1).upper(), m.group(2).strip()
                    fout.write(f"{existing_id}: {rest}\n")
                    written += 1
                    continue
                else:
                    line = m.group(2).strip()

            # assegna nuovo ID
            fout.write(f"{prefix}{counter}: {line}\n")
            counter += 1
            written += 1

    return written


if __name__ == "__main__":
    in_path  = Path("Dataset.arff")
    out_path = Path("Dataset_With_R_ID.txt")

    n = add_ids_to_requirements(
        in_path=in_path,
        out_path=out_path,
        prefix="R",
        start_from=1,
        keep_blank_lines=False,
        skip_if_already_tagged=True,
    )

    print(f"Fatto! Requisiti scritti: {n}")
    print(f"Output: {out_path}")
