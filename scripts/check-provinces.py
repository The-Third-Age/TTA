import os
import re
import sys
import unicodedata
from collections import defaultdict

from PIL import Image

definition_file = "map/definition.csv"
provinces_bmp_file = "map/provinces.bmp"
history_folder = "history/provinces/middle earth"
map_loc_file = "localisation/map.csv"
region_file = "map/region.txt"
region_sea_file = "map/region_sea.txt"
default_map_file = "map/default.map"
positions_file = "map/positions.txt"
continent_file = "map/continent.txt"

# Real land regions are named "<COUNTRYCODE>_<seed province id>", e.g. "GON_4 = { 4 2 3 7 }".
# region.txt also contains a large number of unrelated blocks reused for the dynamic
# localisation system (add_claim_*, remove_claim_*, claim_status_*, dynamic_loc_slot*,
# *_trading_realm_count_loc, etc.) which must be ignored.
region_name_re = re.compile(r'^([A-Za-z]{2,4}_\d+)\s*=\s*\{([^}]*)\}')


def fold_name(name):
    stripped = name.strip()
    return ''.join(c for c in unicodedata.normalize('NFKD', stripped) if not unicodedata.combining(c))


def is_river(name):
    lowered = name.strip().lower()
    return 'river' in lowered or lowered.startswith('mouth of')


"""
Parse map/definition.csv into {id: {'color': (r,g,b), 'name': name}}, and report any
duplicate province ids or duplicate colors found within the file itself.
"""
def parse_definition_csv():
    provinces = {}
    duplicate_ids = set()
    with open(definition_file, 'r', encoding='windows-1252') as f:
        lines = f.readlines()
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.rstrip('\n').split(';')
        if len(parts) < 5:
            continue
        pid = int(parts[0])
        color = (int(parts[1]), int(parts[2]), int(parts[3]))
        name = parts[4].strip()
        if pid in provinces:
            duplicate_ids.add(pid)
        provinces[pid] = {'color': color, 'name': name}

    color_ids = defaultdict(set)
    for pid, data in provinces.items():
        color_ids[data['color']].add(pid)
    duplicate_colors = {color: ids for color, ids in color_ids.items() if len(ids) > 1}

    return provinces, duplicate_ids, duplicate_colors


"""
Get every unique RGB colour used in map/provinces.bmp
"""
def get_bmp_colors():
    img = Image.open(provinces_bmp_file).convert('RGB')
    colors = img.getcolors(maxcolors=img.width * img.height)
    return set(color for _, color in colors)


"""
Parse history/provinces/middle earth into {id: name}, based on filenames of the form
"<id> - <name>.txt"
"""
def parse_history_files():
    provinces = {}
    unparseable = []
    for fn in os.listdir(history_folder):
        if not fn.endswith('.txt'):
            continue
        m = re.match(r'^(\d+) - (.+)\.txt$', fn)
        if not m:
            unparseable.append(fn)
            continue
        provinces[int(m.group(1))] = m.group(2)
    return provinces, unparseable


"""
Parse localisation/map.csv into {id: name}, based on keys of the form "PROV<id>"
"""
def parse_map_loc_csv():
    provinces = {}
    with open(map_loc_file, 'r', encoding='windows-1252') as f:
        for line in f:
            if not line.startswith('PROV'):
                continue
            parts = line.rstrip('\n').split(';')
            m = re.match(r'^PROV(\d+)$', parts[0])
            if not m:
                continue
            provinces[int(m.group(1))] = parts[1].strip() if len(parts) > 1 else ''
    return provinces


"""
Get every province id with a "<id> = { ... }" block in map/positions.txt
"""
def parse_positions_txt():
    with open(positions_file, 'r', encoding='windows-1252') as f:
        content = f.read()
    return set(int(m.group(1)) for m in re.finditer(r'(?m)^(\d+)\s*=\s*\{', content))


"""
Get every province id listed inside a "provinces = { ... }" block in map/continent.txt
"""
def parse_continent_txt():
    with open(continent_file, 'r', encoding='windows-1252') as f:
        content = f.read()
    ids = set()
    for block in re.findall(r'provinces\s*=\s*\{([^}]*)\}', content, re.S):
        ids.update(int(x) for x in re.findall(r'\d+', block))
    return ids


"""
Get every province id listed inside a genuine land region block in map/region.txt
"""
def parse_region_txt():
    ids = set()
    with open(region_file, 'r', encoding='windows-1252') as f:
        for line in f:
            m = region_name_re.match(line.strip())
            if not m:
                continue
            ids.update(int(x) for x in re.findall(r'\d+', m.group(2)))
    return ids


"""
Get every province id listed inside the all_sea_provinces block in map/region_sea.txt
"""
def parse_region_sea_txt():
    with open(region_sea_file, 'r', encoding='windows-1252') as f:
        content = f.read()
    m = re.search(r'all_sea_provinces\s*=\s*\{([^}]*)\}', content, re.S)
    if not m:
        return set()
    return set(int(x) for x in re.findall(r'\d+', m.group(1)))


"""
Get every province id listed in the sea_starts block in map/default.map, plus any duplicates
"""
def parse_sea_starts():
    with open(default_map_file, 'r', encoding='windows-1252') as f:
        content = f.read()
    m = re.search(r'sea_starts\s*=\s*\{([^}]*)\}', content, re.S)
    ids = [int(x) for x in re.findall(r'\d+', m.group(1))] if m else []
    duplicates = set(pid for pid in ids if ids.count(pid) > 1)
    return set(ids), duplicates


def report(title, items):
    if not items:
        return False
    print(f'\n{title} ({len(items)}):')
    for item in sorted(items, key=lambda x: (x,) if isinstance(x, int) else x):
        print(f'  {item}')
    return True


def main():
    definition, duplicate_ids, duplicate_colors = parse_definition_csv()
    bmp_colors = get_bmp_colors()

    color_to_id = {}
    for pid, data in definition.items():
        color_to_id.setdefault(data['color'], pid)
    def_colors = set(color_to_id.keys())

    problems = False

    problems |= report('Duplicate province ids in definition.csv', duplicate_ids)
    problems |= report('Duplicate colors in definition.csv (color -> ids)',
                        [f'{color} -> {sorted(ids)}' for color, ids in duplicate_colors.items()])
    problems |= report('Colors used in provinces.bmp with no entry in definition.csv',
                        bmp_colors - def_colors)
    problems |= report('Entries in definition.csv whose color is not used in provinces.bmp (leftover)',
                        [f'{pid} ({definition[pid]["name"]})' for pid in definition
                         if definition[pid]['color'] not in bmp_colors])

    # The set of provinces actually backed by both a definition.csv entry and a bmp color.
    master_ids = set(pid for pid, data in definition.items() if data['color'] in bmp_colors)

    sea_ids_raw, sea_duplicates = parse_sea_starts()
    problems |= report('Duplicate ids in sea_starts (default.map)', sea_duplicates)
    problems |= report('Ids in sea_starts (default.map) that are not valid provinces',
                        sea_ids_raw - master_ids)

    sea_ids = sea_ids_raw & master_ids
    land_ids = master_ids - sea_ids

    # History files (land provinces only)
    history_provinces, unparseable_history = parse_history_files()
    history_ids = set(history_provinces.keys())
    problems |= report('Files in history/provinces/middle earth with an unparseable name',
                        unparseable_history)
    problems |= report('Land provinces missing a history file', land_ids - history_ids)
    problems |= report('History files not matching a land province (leftover, or wrongly present for a sea province)',
                        history_ids - land_ids)
    name_mismatches = []
    for pid in land_ids & history_ids:
        if fold_name(definition[pid]['name']) != fold_name(history_provinces[pid]):
            name_mismatches.append(f'{pid}: definition.csv="{definition[pid]["name"]}" file="{history_provinces[pid]}"')
    problems |= report('History file names not matching definition.csv name', name_mismatches)

    # localisation/map.csv (all provinces, land and sea)
    loc_map = parse_map_loc_csv()
    loc_ids = set(loc_map.keys())
    problems |= report('Provinces missing an entry in localisation/map.csv', master_ids - loc_ids)
    problems |= report('Entries in localisation/map.csv not matching a valid province (leftover)',
                        loc_ids - master_ids)
    loc_name_mismatches = []
    for pid in master_ids & loc_ids:
        if definition[pid]['name'].strip() != loc_map[pid].strip():
            loc_name_mismatches.append(f'{pid}: definition.csv="{definition[pid]["name"]}" map.csv="{loc_map[pid]}"')
    problems |= report('localisation/map.csv names not matching definition.csv name', loc_name_mismatches)

    # map/positions.txt (all provinces, land and sea)
    positions_ids = parse_positions_txt()
    problems |= report('Provinces missing an entry in map/positions.txt', master_ids - positions_ids)
    problems |= report('Entries in map/positions.txt not matching a valid province (leftover)',
                        positions_ids - master_ids)

    # map/continent.txt (land provinces only)
    continent_ids = parse_continent_txt()
    problems |= report('Land provinces missing from map/continent.txt', land_ids - continent_ids)
    problems |= report('Entries in map/continent.txt not matching a land province (leftover, or wrongly present for a sea province)',
                        continent_ids - land_ids)

    # map/region.txt (land provinces only)
    region_ids = parse_region_txt()
    problems |= report('Land provinces not part of any region in map/region.txt', land_ids - region_ids)
    problems |= report('Provinces in a map/region.txt region that are not a land province (leftover, or wrongly present for a sea province)',
                        region_ids - land_ids)

    # map/region_sea.txt (sea provinces only, river/river-mouth provinces are exempt)
    region_sea_ids = parse_region_sea_txt()
    river_ids = set(pid for pid in sea_ids if is_river(definition[pid]['name']))
    required_sea_ids = sea_ids - river_ids
    problems |= report('Sea provinces missing from all_sea_provinces in map/region_sea.txt (rivers exempt)',
                        required_sea_ids - region_sea_ids)
    problems |= report('Entries in map/region_sea.txt not matching a sea province (leftover)',
                        region_sea_ids - sea_ids)

    print()
    if problems:
        print('Province validation FAILED')
    else:
        print(f'All {len(master_ids)} provinces ({len(land_ids)} land, {len(sea_ids)} sea) validated successfully')

    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
