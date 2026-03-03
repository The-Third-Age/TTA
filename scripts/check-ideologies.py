import os
import sys
import re

ideologies_file = 'common/ideologies.txt'
countries_folder = 'common/countries'
localisation_file = 'localisation/politics.csv'
national_focus_file = 'common/national_focus.txt'

#TODO: Add checks for ideologies in pops, flags, elections, national focus files
pops_folder = 'poptypes'
flags_localisation_file = 'localisation/modifiers and flags.csv'
election_event_file = 'events/Election.txt'

disenfranchised_ideologies = {
    'slave_ideology', 'tribal_ideology'
}

unpromotable_ideologies = {
    'slave_ideology', 'tribal_ideology', 'servants'
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
    
def main():
    ideologies_file_groups, ideologies_file_ideologies = get_ideologies_from_ideologies_file()
    countries_ideologies = get_ideologies_from_countries()
    localisation_ideologies, localisation_ideologies_uh = get_ideologies_from_localisation()
    localisation_ideologies = localisation_ideologies - ideologies_file_groups
    promote_ideologies, demote_ideologies = get_ideologies_from_national_focuses()

    all_ideologies = ideologies_file_ideologies | countries_ideologies | localisation_ideologies | localisation_ideologies_uh

    missing_in_ideologies_file = all_ideologies - ideologies_file_ideologies
    missing_in_countries = all_ideologies - countries_ideologies - disenfranchised_ideologies # We don't expect disenfranchised ideologies to be in the countries files as they are not used for political parties
    missing_in_localisation = all_ideologies - localisation_ideologies
    missing_in_localisation_uh = all_ideologies - localisation_ideologies_uh
    missing_in_promote_ideologies = all_ideologies - promote_ideologies - unpromotable_ideologies # We don't expect unpromotable ideologies in national focuses
    missing_in_demote_ideologies = all_ideologies - demote_ideologies - unpromotable_ideologies # We don't expect unpromotable ideologies in national focuses

    problems = False
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

    sys.exit(1 if problems else 0)

if __name__ == '__main__':
    main()
