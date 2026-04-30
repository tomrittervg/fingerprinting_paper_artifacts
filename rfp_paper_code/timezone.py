#!/usr/bin/env python3
import argparse

from webgl_constants import tz_abbr_to_utc_offset, NON_BACKWARD_TIMEZONE_MAPPINGS

def process_link_mode(filename):
    result = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith("Link"):
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        key = parts[2]
                        value = parts[1]
                        result[key] = value
        print(result)
    except FileNotFoundError:
        print(f"File not found: {filename}")
    except Exception as e:
        print(f"Error reading file: {e}")

def process_zone_mode(filename):
    zones = {}
    rules = {}
    state = "NewCommand"
    current_zone = None

    def get_mapping(zone_line):
        mapping = None
        parts = zone_line.split()
        offset = 2 if zone_line.startswith("Zone") else 0

        # The "Until" section starts at the 5th column (index 4)
        until = parts[offset + 3:] if len(parts) > offset + 3 else []

        #print(parts)
        if not until:
            if len(parts) < offset + 3:
                #print(line)
                raise Exception(f"Invalid zone line format: {line}, segmented to {parts}")

            mapping = parts[offset + 2]
            if "%s" in mapping:
                rule_key = parts[offset + 1]
                if rule_key in rules:
                    mapping = mapping.replace("%s", rules[rule_key])
                else:
                    mapping = mapping.replace("%s", "")

            if mapping == "%z":
                mapping = parts[offset + 0].replace(":", "")
            return False, mapping
        return True, mapping

    try:
        with open(filename, 'r') as f:
            for line in f:
                original_line = line
                hash_index = line.find("#")
                if hash_index != -1:
                    line = line[:hash_index]
                line = line.strip()
                if not line:
                    continue


                if state == "NewCommand":
                    assert current_zone is None, "Current zone should be None at the start of a new command"
                    if line.startswith("Rule"):
                        parts = line.split()
                        if len(parts) >= 9:
                            rule_name = parts[1]
                            value = parts[-1]
                            rules[rule_name] = value
                    if line.startswith("Zone"):
                        #print("N", line)
                        state = "Zone"
                        parts = line.split()
                        if len(parts) >= 2:
                            current_zone = parts[1]

                            keep_going, mapping = get_mapping(line)
                            if mapping:
                                zones[current_zone] = mapping
                                #print(f"Assigning {current_zone} to {mapping}")
                            if not keep_going:
                                current_zone = None
                                state = "NewCommand"

                elif state == "Zone":
                    #print("z", line)
                    if line and not original_line[0].isspace():
                        state = "NewCommand"
                        if line.startswith("Zone"):
                            state = "Zone"
                            parts = line.split()
                            if len(parts) >= 2:
                                current_zone = parts[1]

                                keep_going, mapping = get_mapping(line)
                                if mapping:
                                    zones[current_zone] = mapping
                                    #print(f"Assigning {current_zone} to {mapping}")
                                if not keep_going:
                                    current_zone = None
                                    state = "NewCommand"
                    else:
                        if current_zone is None:
                            raise Exception("No zone defined for this line")

                        if not line:
                            continue

                        keep_going, mapping = get_mapping(line)
                        #print(keep_going, mapping)
                        if mapping:
                            zones[current_zone] = mapping
                            #print(f"Assigning {current_zone} to {mapping}")
                        if not keep_going:
                            current_zone = None
                            state = "NewCommand"

    except FileNotFoundError:
        print(f"File not found: {filename}")
    print()
    print(zones)


def process_mapping_mode():
    print("Checking TIMEZONE_MAPPINGS for numeric offsets or valid abbreviation conversions...")
    for mapping_dict in NON_BACKWARD_TIMEZONE_MAPPINGS:
        for key, value in mapping_dict.items():
            # Check if value is numeric (allow negative, allow colon for HH:MM)
            is_numeric = False
            try:
                # Accept strings like "120", "-300", "5:30"
                if isinstance(value, str):
                    v = value.replace(":", "")
                    if v.lstrip("+-").isdigit():
                        is_numeric = True
            except Exception:
                pass
            if not is_numeric:
                offset = tz_abbr_to_utc_offset(value)
                if offset is None:
                    raise Exception(f"Could not convert abbreviation '{value}' from key '{key}'")
                print(f"{key}: {value} -> {offset}")
            else:
                print(f"{key}: {value} (numeric)")

def main():
    parser = argparse.ArgumentParser(description="Process a file in different modes.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--file', help='File to read')
    group.add_argument('--all', action='store_true', help='Process all timezone files')
    parser.add_argument('-m', '--mode', required=True, choices=['link', 'zone', 'mapping'], help='Mode of operation')
    args = parser.parse_args()

    tzdata_dir = "tzdata"
    timezone_files = [
        f"{tzdata_dir}/africa",
        f"{tzdata_dir}/antarctica",
        f"{tzdata_dir}/asia",
        f"{tzdata_dir}/australasia",
        f"{tzdata_dir}/backzone",
        f"{tzdata_dir}/europe",
        f"{tzdata_dir}/northamerica",
        f"{tzdata_dir}/southamerica"
    ]

    if args.mode == 'mapping':
        process_mapping_mode()
        return

    if args.all:
        for fname in timezone_files:
            #print(f"\nProcessing {fname} in {args.mode} mode:")
            if args.mode == 'link':
                process_link_mode(fname)
            elif args.mode == 'zone':
                process_zone_mode(fname)
    else:
        if args.mode == 'link':
            process_link_mode(args.file)
        elif args.mode == 'zone':
            process_zone_mode(args.file)

if __name__ == "__main__":
    main()