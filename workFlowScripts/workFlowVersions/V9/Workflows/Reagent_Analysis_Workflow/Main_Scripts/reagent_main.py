"""
This script is responsible for analysis of just the reagents used in a workflow.

Structure of the programme:
- Subdivided into 2 main functions:
    1) calculate_required_masses()
    2) calculate_required_volumes()

The time line (psuedo logic) is the following:
 - Define the concentration of the different chemical subtypes
 - Calculate the concentrations of the reagents in the chemical vials (and hence in the analysis samples)
 - Calculate the masses to measure to hit that concentation for a volume that allows analysis on all machines
 - Generate a csv with the reagents and the masses need to measure.
 - Once the chemist has inputted the masses their measured, calculate the volume of CH2Cl2 and CH3CN to make up to the final concentration
 - Generate a csv for the chemspeed with the volumes required
 - Generate a json for the NMR analysis of the reagents (and send them via email)
 - Generate a csv for the MS analysis of the reagents (and send them via email)

"""

import pandas as pd
import os
import json
try:
    import win32com.client    #pip install pywin32   (does not work for mac, hence try and except)
except:
    pass
import sys 
sys.path.append('Python_Modules')
import script_classes as sc
import check_manager as cm

raw_path = os.getcwd()
PATH = ''.join([letter if letter != '\\' else '/' for letter in raw_path])
PATH = PATH + '/Reagent_Analysis_Workflow/'


#c1v1 = c2v2

V1 = sc.USER_SELECTION.reaction_vial_transfer_volume/1000000                                                                            #The volume of reagent added to a reaction vial (in litres)
V2 = sc.USER_SELECTION.reaction_volume/1000000                                                                                          #The final volume of the reaction vial (in litres)

REACTION_VIAL_TRANSFER_VOLUME = V1                                                                                                      #Defining global variables (concentrations of chemical subtypes)
METAL_CONCENTRATION = sc.USER_SELECTION.metal_concentration                                                                                                      
DIALDEHYDE_CONCENTRATION = sc.USER_SELECTION.dialdehyde_concentration
DIAMINE_CONCENTRATION = sc.USER_SELECTION.diamine_concentration
MONOALDEHYDE_CONCENTRATION = sc.USER_SELECTION.monoaldehdye_concentration

#Getting the concentrations in the reaction vials and hence in the NMR Samples

meatl_concentration_reaction_vial = METAL_CONCENTRATION/1000 * V1 / V2                                                                  #Concentration (M) of the metal in the reaction vial
dialdehyde_concentration_reaction_vial = DIALDEHYDE_CONCENTRATION/1000 * V1 / V2                                                        #Concentration (M) of the dialdhdye in the reaction vial
diamine_concentration_reaction_vial = DIAMINE_CONCENTRATION/1000 * V1 / V2                                                              #Concentration (M) of the dimaine in the reaction vial 
monoaldehdye_concentration_reaction_vial = MONOALDEHYDE_CONCENTRATION/1000 * V1 / V2                                                    #Concentration (M) of the monoamine in the reaction vial 

#the list of reagents in order (copy pasted from main workflow)

reagents = [
        sc.Metal(name='Iron(II) tetrafluoroborate hexahydrate', CAS='13877-16-2', molecular_weight=337.55, solubility=(0,1), price=6, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= METAL_CONCENTRATION, no_coordination_sites=(6)),
        sc.Metal(name='Zinc tetrafluoroborate', CAS='27860-83-9', molecular_weight=239, solubility=(0,1), price=1.348,  volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=METAL_CONCENTRATION, no_coordination_sites=(6)),
        sc.Metal(name='Yittrium(III) trifluoromethanesulfonate', CAS='52093-30-8', molecular_weight=536.11, solubility=(0,1), price=17.2,  volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=METAL_CONCENTRATION, no_coordination_sites=(6)), #yttrim has coordination numbers between 6-9 (in our experiment well just assume 6)
        sc.Metal(name='Tetrakis(acetonitrile)copper(I) tetrafluoroborate', CAS='15418-29-8', molecular_weight=314.56, solubility=(0,1), price=33,  volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=METAL_CONCENTRATION, no_coordination_sites=(4)), #copper has coordination number 4
        sc.Metal(name='Silver tetrafluoroborate', CAS='14104-20-2', molecular_weight=194.67, solubility=(0,1), price=28.3,  volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=METAL_CONCENTRATION, no_coordination_sites=(4,6)), #silver has coordiantion numebrs 4, 5, or 6 (in our experiment well just assume 4 and 5)
        sc.Dialdehyde(name='1,10-Phenanthroline-2,9-dicarbaldehyde', CAS='57709-62-3', molecular_weight=236.23, solubility=(0,1), price=165, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=DIALDEHYDE_CONCENTRATION, no_coordination_sites=2, no_imine_reaction_sites=2),
        sc.Dialdehyde(name='Pyridine-2,6-dicarbaldehyde', CAS='5431-44-7', molecular_weight=135.122, solubility=(0,1), price=59, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=DIALDEHYDE_CONCENTRATION, no_coordination_sites=2, no_imine_reaction_sites=2),
        sc.Diamine(name='2,2\'-(Ethane-1,2-diyl)dianiline', CAS='34124-14-6', molecular_weight=212.297, solubility=(0,1), price=16, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
        sc.Diamine(name='2,2\'-(Ethane-1,2-diylbis(oxy))diethanamine', CAS='929-59-9', molecular_weight=148.21, solubility=(3,1), price=0.64, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
        sc.Diamine(name= '2,2\'-Oxydiethanamine', CAS='2752-17-2', molecular_weight=104.15, solubility=(0,1), price=40, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
        #sc.Diamine(name='1,4-Phenylenedimethanamine', CAS='539-48-0', molecular_weight=136.194, solubility=(1,0), price=4, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2), to be replaced
        sc.Diamine(name='4,4\'-Methylenedianiline', CAS='101-77-9', molecular_weight=198.26, solubility=(0,1), price=0.506, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=DIAMINE_CONCENTRATION, no_coordination_sites=2, no_imine_reaction_sites=2),
        sc.Diamine(name='1,3-Benzenedimethanamine', CAS='1477-55-0', molecular_weight=136.19, solubility=(0,1), price=13, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
        sc.Diamine(name='Adamantane-1,3-diamine', CAS='10303-95-4', molecular_weight=166.27, solubility=(1,0), price=140, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
        sc.Diamine(name='4,4\'-(9H-Fluorene-9,9-diyl)dianiline', CAS='15499-84-0', molecular_weight=348.44, solubility=(0,1), price=10, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
        sc.Diamine(name='(S)-4,5,6,7-Tetrahydro-benzothiazole-2,6-diamine', CAS='106092-09-5', molecular_weight=169.25, solubility=(0,0), price=2.2, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2), #commented out because non existant in lab stock
        sc.Diamine(name='[2,2\'-Bipyridine]-4,4\'-diamine', CAS='18511-69-8', molecular_weight=186.22, solubility=(0,0), price=99, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2), #commented out because non existant in lab stock
        sc.Diamine(name='Naphthalene-1,8-diamine', CAS='479-27-6', molecular_weight=158.2, solubility=(0,1), price=10, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2), 
        sc.Diamine(name='4,4\'-Oxydianiline', CAS='101-80-4', molecular_weight=200.24, solubility=(0,1), price=0.742, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
        sc.Diamine(name='6-Methyl-1,3,5-triazine-2,4-diamine', CAS='542-02-9', molecular_weight=125.13, solubility=(0,0), price=0.1, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2), #commented out because non existant in lab stock
        sc.Diamine(name='(R)-(+)-1,1\'-Binaphthyl-2,2\'-diamine', CAS='18741-85-0', molecular_weight=284.35, solubility=(1,0), price=132, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
        sc.Monoaldehdye(name='6-Methylpyridine-2-carboxaldehyde', CAS='1122-72-1', molecular_weight=121.14, solubility=(0,1), price=4, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='6-Phenylpicolinaldehyde', CAS='157402-44-3', molecular_weight=183.21, solubility=(0,1), price=206, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='[2,2\'-Bipyridine]-6-carbaldehyde', CAS='134296-07-4', molecular_weight=184.19, solubility=(0,1), price=258, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='2-Quinolinecarboxaldehyde', CAS='5470-96-2', molecular_weight=157.17, solubility=(1,0), price=30.8, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='5-Methylpicolinaldehyde', CAS='4985-92-6', molecular_weight=121.14, solubility=(0,1), price=12, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='8-methoxyquinoline-2-carbaldehyde', CAS='103854-64-4', molecular_weight=187.19, solubility=(0,1), price=116, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='[1,8]Naphthyridine-2-carbaldehyde', CAS='64379-45-9', molecular_weight=158.16, solubility=(1,2), price=258, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='4-Formyl-2-methylthiazole', CAS='20949-84-2', molecular_weight=127.16, solubility=(0,1), price=28, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='6-Methoxypyridine-2-carbaldehyde', CAS='54221-96-4', molecular_weight=137.14, solubility=(0,1), price=10, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='1-Methyl-2-imidazolecarboxaldehyde', CAS='13750-81-7', molecular_weight=110.11, solubility=(0,1), price=16, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='1-Methyl-1H-benzimidazole-2-carbaldehyde', CAS='3012-80-4', molecular_weight=160.177, solubility=(0,1), price=54, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1),
        sc.Monoaldehdye(name='4-Methyl-1,3-thiazole-2-carbaldehyde', CAS='13750-68-0', molecular_weight=127.16, solubility=(0,1), price=51, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1)
]

#A dict to be converted to a data frame
reagent_space = {
    'Chemical_index': [],                                                                                                       #The numerical identy of the  reagent
    'Chemical': [],                                                                                                             #A list of the reaegent names
    'Mass to measure (in grams)': [],                                                                                            #A list of the required masses to reach the final concentratoin in the reaction vials (NMR tubes),
    'Actual mass measured': []                                                                                                  #A list of masses measured by the chemist
}                                                                                               

#Removing chemicals that are not part of the combination space (and hence we dont need to analyse)
chemicals_to_remove = [
        sc.Diamine(name='(S)-4,5,6,7-Tetrahydro-benzothiazole-2,6-diamine', CAS='106092-09-5', molecular_weight=169.25, solubility=(0,0), price=2.2, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
        sc.Diamine(name='[2,2\'-Bipyridine]-4,4\'-diamine', CAS='18511-69-8', molecular_weight=186.22, solubility=(0,0), price=99, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
        sc.Diamine(name='6-Methyl-1,3,5-triazine-2,4-diamine', CAS='542-02-9', molecular_weight=125.13, solubility=(0,0), price=0.1, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2),
]

def _calculate_masses_to_measure():
    """Calculates the required masses to hit the required concentrations for analysis"""
    for chemical_indx, chemical in enumerate(reagents):
        #concentration = moles / volume
        #moles = mass / molecular weight
        #concentration = (mass / molecular weight) / volume
        
        #getting final concentrations depending on the chemical subtype
        if  'Metal' == chemical.__class__.__name__:
            final_concentration = meatl_concentration_reaction_vial

        if 'Dialdehyde' == chemical.__class__.__name__:
            final_concentration = dialdehyde_concentration_reaction_vial

        if 'Diamine' == chemical.__class__.__name__:
            final_concentration = diamine_concentration_reaction_vial

        if 'Monoaldehdye'== chemical.__class__.__name__:
            final_concentration = monoaldehdye_concentration_reaction_vial

        #removing chemicals not part of the combination space
        for removal_chemical in chemicals_to_remove:
            if chemical.name == removal_chemical.name:
                final_concentration = 0


        mass = (final_concentration * V2) * chemical.molecular_weight                                                               #mass = (concentration * volume) * molecular weight         concentration has to be converted to M.         Volume has to be converted to litres.
        reagent_space['Mass to measure (in grams)'].append(mass)                                                                    #These are various columns in the generated csv
        reagent_space['Chemical'].append(chemical.name)
        reagent_space['Chemical_index'].append(chemical_indx+1)

    reagent_space['Actual mass measured'] = [None if mass != 0 else 0 for mass in reagent_space['Mass to measure (in grams)']]      #Adding an empty space if the reagent mass must be taken

    df = pd.DataFrame.from_dict(reagent_space).set_index('Chemical_index')                                                          #Reading the dictionary as a dataframe and saving it as a csv and pickle
    csv_path = PATH + 'Generated_CSVs/' + 'reagent_mass_to_measure.csv'
    df.to_csv(csv_path)

def _send_csv_via_email():
    """Sends the generated csv via email to then be printed"""
    csv_path = PATH + 'Generated_CSVs/' + 'reagent_mass_to_measure.csv'
    try:
            ol = win32com.client.Dispatch('Outlook.Application')                                                                    #sending stock space to print via outlook
            olmailitem=0x0
            newmail = ol.CreateItem(olmailitem)
            newmail.Subject = 'Mass of reagents to measure'
            newmail.To = 'printbw1@liverpool.ac.uk'
            newmail.Attachments.Add(csv_path)
            newmail.Display()
            newmail.Send()
            print('Reagent CSV successfully sent')

    except Exception as e:
        print(e)
        print('Email sending failed, manualy send stock space')
        pass


def calculate_required_masses():
    """Generates a csv with masses to measure and sends them to be printed off"""
    _calculate_masses_to_measure()
    _send_csv_via_email()
    
#Setting up the check manager
check_manager_2 = cm.Check_Manager()
check_manager_2.add_checks([
    cm.Visual_Bool_Check('Please add reagent vials in the right place and run get_batch_spaces_csvs() again.', 'Have the reagents vials been added in the right zone? (1=Yes, 0=No): ' ),
    cm.Visual_Bool_Check('Please top up CH2Cl2 vial and added it in the right place and run get_batch_spaces_csvs() again.', 'Has the CH2Cl2 vial been added and topped up? (1=Yes, 0=No): ' ),
    cm.Visual_Bool_Check('Please top up CHCN3 and run get_batch_spaces_csvs() again.', 'Is there enough CHCN3 left in the resevoir? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please empty special waste and run get_batch_spaces_csvs() again.', 'Is the special waste empty enough for one run? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please add NMR tubes and make sure they\'re in the right place and run get_batch_spaces_csvs() again.', 'Have all NMR tubes been added, and are the two green stickers aligned? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please add MS vials and run get_batch_spaces_csvs() again.', 'Have all the MS vials been added? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please add measured masses into the csv and run get_batch_spaces_csvs() again.', 'Have all the measured masses been added to the reagent_mass_to_measure csv? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please add the Mosquito rack and run get_batch_spaces_csvs() again.', 'Has the mosquito plate been added to the workflow? (1=Yes, 0=No): '),
])

def _generate_chemspeed_csv():
    """Generates the Chemspeed readable csv to make up stock solutions with the right concentrations for analysis"""

    flag =  check_manager_2.run_check_list()

    if flag == True:
        #laoding the user's measured masses
        csv_path = PATH + 'Generated_CSVs/' + 'reagent_mass_to_measure.csv'
        df = pd.read_csv(csv_path, index_col=0)
        CH3CN_volume_initial = []                                                                                                             #Volumes are divided into two different parts 1) Generation of the pseudo stock solution 2) Generation of the pseudo reactoin vial (see whole workflow for a better understanding)
        CH2Cl2_volume_initial = []
        CH3CN_volume_final = []
        for chemical_idx, chemical in enumerate(reagents):                                                                                    #Getting the concentration of the chemical subtypes
            if  'Metal' == chemical.__class__.__name__:
                final_concentration = meatl_concentration_reaction_vial

            if 'Dialdehyde' == chemical.__class__.__name__:
                final_concentration = dialdehyde_concentration_reaction_vial

            if 'Diamine' == chemical.__class__.__name__:
                final_concentration = diamine_concentration_reaction_vial

            if 'Monoaldehdye'== chemical.__class__.__name__:
                final_concentration = monoaldehdye_concentration_reaction_vial


            mass_measured = df.iloc[chemical_idx, 2]
            molecular_weight = chemical.molecular_weight
            
            if final_concentration != 0:                                                                                                      #Getting rid of the math x/0 error
                #volume = (mass / molecular weight) / concentration
                final_volume = (mass_measured / molecular_weight / final_concentration)                                                       #calculating the final volume required
                
                solubility_CCl2H2, solubility_CH3CN = chemical.solubility            
                if solubility_CCl2H2 == 0 and solubility_CH3CN == 0:                                                                          #Some chemicals my be insoluble in both solubility tuple = (0,0)     
                        CH2Cl2_volume_initial.append(0)
                        CH3CN_volume_initial.append(0)
                        CH3CN_volume_final.append(0) 

                else:
                    volume_CCl2H2_initial = (solubility_CCl2H2/(solubility_CCl2H2+solubility_CH3CN))*V1                                       #The final CH2Cl2 volume is dpendent on the solubility ratio of the chemical in CH3CN: CH2Cl2 in the transfer volume (in the main script, the chemical is first made into a stock solution and then topped up with CH3CN in the reaction vial)
                    volume_CH3CN_initial = (solubility_CH3CN/(solubility_CH3CN+solubility_CCl2H2))*V1                                         #This is the initial reagent conditions. In the main script this is equivalent to making up the stock solutions
                    volume_CH3CN_final = final_volume - (volume_CH3CN_initial + volume_CCl2H2_initial)                                        #Calculating the volume of acetonitrle in a pseuod reaction vial


                    CH2Cl2_volume_initial.append(volume_CCl2H2_initial*1000000)                                                               #Updating the various volumes / 1000000 to convert to microlitres
                    CH3CN_volume_initial.append(volume_CH3CN_initial*1000000)
                    CH3CN_volume_final.append(volume_CH3CN_final*1000000)

            else:                                                                                                                             #This is used to remove any potential math errors (x/0)
                CH2Cl2_volume_initial.append(0)
                CH3CN_volume_initial.append(0)
                CH3CN_volume_final.append(0)
        
        df['CH3CN_initial'] = CH3CN_volume_initial                                                                                            #Setting the calculated lists as df columns
        df['CCl2H2_initial'] = CH2Cl2_volume_initial
        df['CH3CN_final'] = CH3CN_volume_final

        df.to_csv(csv_path)                                                                                                                   #Saving the dataframe as a csv
        print('')
        print('REAGENT SPACE SUCCESFULY GENERATED')
        

def _generate_NMR_json():
    """Generates the json to be used by the NMR autosampler"""
    file_name = 'reagent_analysis.json'
    json_path = PATH + 'Generated_NMR_JSONs/' + file_name
    json_to_save = {}

    for reagent_idx, reagent in enumerate(reagents):                                                                                          #Iterating through the reagents and adding a new MNR sample for each  
        json_to_save[f'{reagent_idx+1}'] = {
        "sample_info": reagent.name,
        "solvent": sc.USER_SELECTION.solvent,                                                                                                 #Solvent is the major solvent in the experiment (see USERSELECTION class in script_classes.py)
        "nmr_experiments": [
                    {
                        "parameters": sc.USER_SELECTION.parameters,                                                                           #Different parameters that control how the NMR spectra is taken 
                        "num_scans": sc.USER_SELECTION.num_scans,
                        "pp_threshold": sc.USER_SELECTION.pp_thershold,
                        "field_presat": sc.USER_SELECTION.field_presat
                    }
                ]
        }
    
    with open(json_path, 'w', newline="\n") as json_output:                                                                                   #Saving the genrated NMR dictionary as a json to be sent and read by the NMR autosampler.  
        json.dump(json_to_save, json_output, indent=4)

def _generate_MS_csv():
    """Generates the csv to be used by the LCMS autosampler"""
    file_name = 'reagent_analysis.csv'
    csv_path = PATH + 'Generated_MS_CSV/' + file_name

    csv_dct = {                                                                                                                               #The dictionary to be saved as a csv                                                                               
            'INDEX': [],                                                                                                                      #An index for the autosampler is reqruired
            'FILE_NAME': [],                                                                                                                  #This is the file name for the samples UV and MS spectra
            'FILE_TEXT': [],                                                                                                                  #IDK what this does, I think it just makes the sample spectra more human interpretable
            'MS_FILE': [],                                                                                                                    #This is the name of the file used for MS protols (i.e. injection speeds, M/Z range)
            'MS_TUNE_FILE': [],                                                                                                               #Similar to the MS_file its a file name. The file is generated by the Water's LCMS machine when a user wants to run the same spectra over different samples
            'INLET_FILE': [],                                                                                                                 #Agian this is similar to the two previous.
            'SAMPLE_LOCATION': [],                                                                                                            #This is the location of the sample in the LCMS rack. In this case, the reaction order in the batch space is the same as the the sample location indx 
            'INJ_VOL': []                                                                                                                     #This is the injection volume for MS / UV-Vis 
            }

    for reagent_indx, reagent in enumerate(reagents):                                                                                         #Iterating through the reagents and adding a new table row for each
        text_var = 'reagent' + str(reagent_indx+1)
        csv_dct['INDEX'].append(reagent_indx + 1)
        csv_dct['FILE_NAME'].append(text_var)
        csv_dct['FILE_TEXT'].append(text_var)                                                                                                 #The file name is the reagent numerical id (the index of the reagent in the list)
        csv_dct['MS_FILE'].append('SupraChemCage')
        csv_dct['MS_TUNE_FILE'].append('SupraChemCage')
        csv_dct['INLET_FILE'].append('SupraChemCage')
        csv_dct['SAMPLE_LOCATION'].append(f'1:{reagent_indx+1}')
        csv_dct['INJ_VOL'].append(sc.USER_SELECTION.ms_injectoin_volume)
    
    df = pd.DataFrame.from_dict(csv_dct)                                                                                                      #Reading the dictionary as a dataframe to then save it as a csv
    df.to_csv(csv_path, index=False)
    

def _send_files_via_email(object_dirs:list):
    """Sends the object marked as a directly via email"""
    
    try:
            ol = win32com.client.Dispatch('Outlook.Application')                                                                    #sending objects pointed as directories via email
            olmailitem=0x0
            newmail = ol.CreateItem(olmailitem)
            newmail.Subject = 'NMR json and MS CVS'
            newmail.To = 'chemspeedgunther@gmail.com'
            for path in object_dirs:                                                                                                #Iterating through object directories and sending them as attachements
                newmail.Attachments.Add(path)
            newmail.Display()
            newmail.Send()
            print('Json and CSV successfully sent')

    except Exception as e:
        print(e)
        print('Email sending failed, manualy send stock space')
        pass
    

def calculate_required_volumes():
    _generate_chemspeed_csv()
    _generate_MS_csv()
    _generate_NMR_json()
    dirMScsv = PATH + 'Generated_MS_CSV/' + 'reagent_analysis.csv'
    dirNMRjson = PATH + 'Generated_NMR_JSONs/' + 'reagent_analysis.json'
    print(dirMScsv)
    _send_files_via_email([dirMScsv, dirNMRjson])


#To run the workflow run one function at a time. After the calculated_required_masses() is run measured masses must be inputted into the csv before the next function can be run.

#calculate_required_masses()
calculate_required_volumes()
