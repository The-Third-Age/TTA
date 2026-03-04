import os
import sys
import re

ideologies_file = 'common/ideologies.txt'
countries_folder = 'common/countries'
localisation_file = 'localisation/politics.csv'
national_focus_file = 'common/national_focus.txt'
election_event_file = 'events/Election.txt'
flags_localisation_file = 'localisation/modifiers and flags.csv'
pops_folder = 'poptypes'

default_ideologies = {
    'nobility', 'tribal_ideology', 'burgher', 'slave_ideology', 'servants', 'loremaster'
}
disenfranchised_ideologies = {
    'slave_ideology', 'tribal_ideology'
}
unpromotable_ideologies = {
    'slave_ideology', 'tribal_ideology', 'servants'
}
poptypes_to_ignore = {
    'slaves', 'tribals', 'bankers'
}

"""
Get all ideologies that are found in the ideologies file
Ideologies are defined within ideological groups
ideology_group = {
    ideology = {
        ...
    }
}
"""
def get_ideologies_from_ideologies_file():
    groups = set()
    ideologies = set()
    depth = 0
    with open(ideologies_file, 'r', encoding='windows-1252') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            match = re.match(r'^([A-Za-z0-9_]+)\s*=\s*{', line)
            if match:
                name = match.group(1)
                if depth == 0:
                    groups.add(name)
                elif depth == 1:
                    ideologies.add(name)
            depth += line.count("{")
            depth -= line.count("}")
    return groups, ideologies

"""
Get all ideologies that are found in the political parties of the countries files
Look for any lines that match the pattern "ideology = <ideology_name>"
"""
def get_ideologies_from_countries():
    ideologies = set()
    for filename in os.listdir(countries_folder):
        if filename.endswith('.txt'):
            with open(os.path.join(countries_folder, filename), 'r', encoding='windows-1252') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    match = re.match(r'^ideology\s*=\s*([A-Za-z0-9_]+)', line)
                    if match:
                        ideology = match.group(1)
                        ideologies.add(ideology)
    return ideologies

'''
Get all ideologies that are found in the localisation file
'''
def get_ideologies_from_localisation():
    ideologies = set()
    ideologies_uh = set()
    found_start_line = False
    found_end_line = False
    with open(localisation_file, 'r', encoding='windows-1252') as f:
        for line in f:
            line = line.strip()
            if found_end_line:
                break
            # Ignore all lines up till we find the localisation bit
            if not found_start_line and '### Ideologies ####' not in line:
                continue
            if not found_start_line:
                found_start_line = True
                continue
            if '### COUNCIL OF THE REALM TEXT ###' in line and found_start_line:
                found_end_line = True
            if line.startswith('#') or not line:
                continue
            parts = line.split(';')
            ideology = parts[0].strip()
            # Ignore _uh which refers to upper house localisation
            if ideology.endswith('_uh'):
                ideologies_uh.add(ideology[:-3])
            else:
                ideologies.add(ideology)
    return ideologies, ideologies_uh

def get_ideologies_from_national_focuses():
    promote_ideologies = set()
    demote_ideologies = set()
    found_start_line = False
    with open(national_focus_file, 'r', encoding='windows-1252') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if 'promotion_ideologies' in line:
                found_start_line = True
                continue
            if 'promote_' in line and found_start_line:
                national_focus_label = line.split(' ')[0].strip() # promote_[ideology]
                ideology = national_focus_label.split('_', 1)[1]
                promote_ideologies.add(ideology)
            elif 'demote_' in line and found_start_line:
                national_focus_label = line.split(' ')[0].strip() # demote_[ideology]
                ideology = national_focus_label.split('_', 1)[1]
                demote_ideologies.add(ideology)
    return promote_ideologies, demote_ideologies

'''
Get all ideologies that are found in events 14006 and 14007 
'''
def get_ideologies_from_election_event():
    ideologies_14006 = set()
    ideologies_14007 = set()
    in_14006 = False
    in_14007 = False
    with open(election_event_file, 'r', encoding='windows-1252') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if 'id = 14006' in line:
                in_14006, in_14007 = True, False
                continue
            if 'id = 14007' in line:
                in_14006, in_14007 = False, True
                continue
            if 'id = 14008' in line:
                break
            if 'ruling_party_ideology = ' in line:
                # The line looks like 'limit = { owner = { ruling_party_ideology = [ideology] } }'
                ideology = line.split('ruling_party_ideology = ')[1].strip(' }')
                if in_14006:
                    ideologies_14006.add(ideology)
                elif in_14007:
                    ideologies_14007.add(ideology)
    return ideologies_14006, ideologies_14007

def get_ideologies_from_flag_localisation():
    ideologies = set()
    with open(flags_localisation_file, 'r', encoding='windows-1252') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            parts = line.split(';')
            key = parts[0].strip()
            if key.startswith('ideologies_') and key.endswith('_active'):
                ideology = key.split('ideologies_')[1].split('_active')[0]
                ideologies.add(ideology)
    return ideologies

'''
Check that every ideology appears in every applicable pop file
'''
def check_ideologies_appear_in_all_pop_files(ideologies):
    problems = False
    for filename in os.listdir(pops_folder):
        if filename.endswith('.txt'):
            raw_filename = filename.rsplit('.', 1)[0]
            if raw_filename in poptypes_to_ignore:
                continue
            # Just check if the ideology is mentioned in the pop file, we don't care about the context
            with open(os.path.join(pops_folder, filename), 'r', encoding='windows-1252') as f:
                file_contents = f.read()
                for ideology in ideologies:
                    if ideology in file_contents:
                        continue
                    print(f'Ideology {ideology} is missing in pop file {filename}')
                    problems = True
    return problems

def main():
    ideologies_file_groups, ideologies_file_ideologies = get_ideologies_from_ideologies_file()
    countries_ideologies = get_ideologies_from_countries()
    localisation_ideologies, localisation_ideologies_uh = get_ideologies_from_localisation()
    localisation_ideologies = localisation_ideologies - ideologies_file_groups
    promote_ideologies, demote_ideologies = get_ideologies_from_national_focuses()
    ideologies_14006, ideologies_14007 = get_ideologies_from_election_event()
    flag_localisation_ideologies = get_ideologies_from_flag_localisation()

    all_ideologies = ideologies_file_ideologies | countries_ideologies | localisation_ideologies | localisation_ideologies_uh | flag_localisation_ideologies | promote_ideologies | demote_ideologies | ideologies_14006 | ideologies_14007

    missing_in_ideologies_file = all_ideologies - ideologies_file_ideologies
    missing_in_countries = all_ideologies - countries_ideologies - disenfranchised_ideologies # We don't expect disenfranchised ideologies to be in the countries files as they are not used for political parties
    missing_in_localisation = all_ideologies - localisation_ideologies
    missing_in_localisation_uh = all_ideologies - localisation_ideologies_uh
    missing_in_promote_ideologies = all_ideologies - promote_ideologies - unpromotable_ideologies # We don't expect unpromotable ideologies in national focuses
    missing_in_demote_ideologies = all_ideologies - demote_ideologies - unpromotable_ideologies # We don't expect unpromotable ideologies in national focuses
    missing_in_14006 = all_ideologies - ideologies_14006 - disenfranchised_ideologies # We don't expect disenfranchised ideologies in election events
    missing_in_14007 = all_ideologies - ideologies_14007 - disenfranchised_ideologies # We don't expect disenfranchised ideologies in election events
    missing_in_flag_localisation = all_ideologies - flag_localisation_ideologies - default_ideologies # We don't expect default ideologies in flag localisation

    problems = check_ideologies_appear_in_all_pop_files(all_ideologies - disenfranchised_ideologies)
    if missing_in_ideologies_file:
        problems = True
        print(f'\nIdeologies missing in ideologies file: {missing_in_ideologies_file}')
    if missing_in_countries:
        problems = True
        print(f'\nIdeologies missing in countries files: {missing_in_countries}')
    if missing_in_localisation:
        problems = True
        print(f'\nIdeologies missing in localisation file: {missing_in_localisation}')
    if missing_in_localisation_uh:
        problems = True
        print(f'\nIdeologies missing upper house localisation: {missing_in_localisation_uh}')
    if missing_in_promote_ideologies:
        problems = True
        print(f'\nIdeologies missing in promote_ideologies: {missing_in_promote_ideologies}')
    if missing_in_demote_ideologies:
        problems = True
        print(f'\nIdeologies missing in demote_ideologies: {missing_in_demote_ideologies}')
    if missing_in_14006:
        problems = True
        print(f'\nIdeologies missing in event 14006: {missing_in_14006}')
    if missing_in_14007:
        problems = True
        print(f'\nIdeologies missing in event 14007: {missing_in_14007}')
    if missing_in_flag_localisation:
        problems = True
        print(f'\nIdeologies missing in flag localisation: {missing_in_flag_localisation}')

    sys.exit(1 if problems else 0)

if __name__ == '__main__':
    main()
