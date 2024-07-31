import csv
import pandas as pd

INJECTION_VOlume= 1
path = 'Z:/Chemspeed platform all versions/V8/Stock_and_Combination_workflow/Generated_MS_CSV/test.csv'

batch_space = [] #self.sample_space

for i in range(0,48):
    batch_space.append(f'sample{i+1}')

print(batch_space)
csv_dct = {
    'INDEX': [],
    'FILE_NAME': [],
    'FILE_TEXT': [],
    'MS_FILE': [],
    'MS_TUNE_FILE': [], 
    'INLET_FILE': [],
    'SAMPLE_LOCATION': [],
    'INJ_VOL': []
    }

for reaction_indx, reaction in enumerate(batch_space):
    csv_dct['INDEX'].append(reaction_indx + 1)
    csv_dct['FILE_NAME'].append(reaction) #reaction.unique_identifier
    csv_dct['FILE_TEXT'].append(reaction) #f'{self.batch_number}_{reaction.unique_identifier}'
    csv_dct['MS_FILE'].append('SupraChemCage')
    csv_dct['MS_TUNE_FILE'].append('SupraChemCage')
    csv_dct['INLET_FILE'].append('SupraChemCage')
    csv_dct['SAMPLE_LOCATION'].append(f'1:{reaction_indx+1}')
    csv_dct['INJ_VOL'].append(INJECTION_VOlume) #sc.USER_SELECTION.ms_injectoin_volume

df = pd.DataFrame.from_dict(csv_dct)
df.to_csv(path, index=False)

