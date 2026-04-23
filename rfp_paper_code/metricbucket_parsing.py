#!/usr/bin/env python3.14t
import csv
import glob
import os
import sys

def main(input_dir: str, output_file: str):
    # Find all CSV files in the directory
    pattern = os.path.join(input_dir, '*.csv')
    csv_paths = sorted(glob.glob(pattern))
    if not csv_paths:
        print(f"No CSV files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    # Read each file: skip header, collect rows and header-from-row2-col1
    all_data = []
    headers = []
    for path in csv_paths:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                file_header = next(reader)  # skip the first (header) row
            except StopIteration:
                print(f"{path} is empty", file=sys.stderr)
                sys.exit(1)

            rows = list(reader)
            if len(rows) < 1:
                print(f"{path} has no data rows", file=sys.stderr)
                sys.exit(1)

            # header for this column is value in row 2, column 1 (first data row, first column)
            headers.append(rows[0][0])

            # extract column 5 (index 4) for every data row
            try:
                col5 = [row[4] for row in rows]
            except IndexError:
                print(f"{path} has fewer than 5 columns", file=sys.stderr)
                sys.exit(1)

            all_data.append(col5)

    # Confirm all files have the same number of data rows
    lengths = [len(col) for col in all_data]
    if len(set(lengths)) != 1:
        print("CSV files have differing numbers of data rows:", lengths, file=sys.stderr)
        sys.exit(1)
    num_rows = lengths[0]

    # Write the merged CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as out_f:
        writer = csv.writer(out_f)
        # first row: the headers collected from each file
        writer.writerow(headers)
        # subsequent rows: one row per original data row index
        for i in range(num_rows):
            row = [all_data[j][i] for j in range(len(all_data))]
            writer.writerow(row)

    print(f"Merged {len(csv_paths)} files ({num_rows} rows each) into {output_file}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_directory> <output_csv>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
