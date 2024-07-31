"""
Structure of the programme:
- Subdivided into 3 main compnents:
    1) Generation of Reaction space (and pickle file)
    2) Generation of batch reaction space (pickle + csv file)
    3) Generation of stock solution space (pickle + csv file)

The time line (pseudo logic is as follows)
 - Addition of chemicals Gunther is able to explore into a chemical space
 - Removal of unintersting chemicals into a subset chemical space
 - Generation of the reaction space
 - Sorting of reaction space
 - Saving of reacation space
 - saving a logged  space
 - Taking a batch space
 - Calculating the mass of reagents needed
 - Generation of stock and batch chemspeed scripts

 


Inoder to do so the following classes will be created:
- Various chemical classes: these store information of the chemical and will help with price ranking, calaculating mass, concentrations, generation of reaction spaces, e.t.c.
- Chemical space: stores inforamtion of the possible chemical space Gunther can search.
- focused chemical space: stores information of the chemical space (a subset of the chemical space whos combinations we are interested in).
- Reaction class: these store information on the reagents, volumes of each chemical in the reaction space. These will then generate a chemspeed readbale csv.
- Batch space: the space of reactions for a specific batch
- Logged space: the space of reactions taken

- USER_SELECTION:
    - Any sort of information that users can change (i.e. batch number, transfer volume)

- Chemical:
    - Attributes:
        - Name
        - CAS number
        - molecular_weight
        - solubility (in DCM and CH3CN)
        - price
        - stochiometric amount / volume to transfer to reaction vials  in reaction mixture (it is also representative of stoichiometric amounts, inaddition to the concenatrions in stock solutions)
        - Concentraion in stock vials (microlitre) (for metals with different numbers, assume concentraion to be the amount for its octhedral geometry, the script will atomaticly calcualte the concentraion for the other coordiation numbers). Having the concentration as a chemical attribute in theory, allows for the most felxibility.

- Metal (chemical):
    - Attributes:
        - Coordination number
    
    - Methods:
        - select coordination number (allows the user to select the assumed coordiantion number of the metal in a reaction)

- Dialdehyde (chemical):
    - Attributes:
        - Number of coordination sites
        - Number of imine reaction sites

- Diamine (chemical):
    - Attributes:
        - Number of coordination sites
        - Number of imine reaction sites

- Monoamine (chemical):
    - Attributes:
        - Number of coordination sites
        - Number of imine reaction sites

- Monoaldehdye (chemical):
    - Attributes:
        - Number of coordination sites
        - Number of imine reaction sites    

- Whole_chemical_space:
    - Attributes:
        - list of all chemical class
    
    - Methods:
        - save to pickle file

- Subset_chemical_space ():
    - Attributes:
        - list of all chemical classes taken from parent class
        - dct of unique chemical subtypes (i.e. aldehyde, ketone) in the subset chemcial space and all their corresponding chemicals
    - Methods:
        - Remove chemicals (takes in a list of chemicals which are not of interst and removes them from the space)
        - Divide space (fills the dictionary in the attributes section)#

- Chemical_reaction():
    - Attributes:
        - Final volume of the reaction mixtres in microlitre (top up with CH3CN)
        - Regents in reaction (list of chemical objects)
        - Volume of reagents in reactions (to calc CH3CN volumes)
        - Volume of reagents required (vector with chemical space basis + CH3CN)

    - Methods:
        - find reagent volumes 

- Reaction_space
    - Attributes:
        - Subset chemical space (takes in as argument)
        - Rection space (list of all reactions to take in the form of reaction objects)
        - Reagent space (a list of all reactions to take in the form of reagent list: must be converted to reaction space)
    
    - Methods:
        - calc combinations (based on the number of each chemcial subtype wanted)
        - calc possible imines (calcs all possible imines in reaction subspace)
        - add standard reactions (this is the same reaction run as sample 1, to help check chemical and robotic systems are operating as intended)
        - sort chemical space (sorts the reactions form most pricy to least pricy)
        - Save to pickle (save reaction space as a pickle file)
        - show reaction space size
        - show reaction space
        - save to csv (more easy to asses what the programme is doing)

Logged space:
    - Attributes:
        - list of logged experiments

    - Methods:
        - added bath space to logged space (add reactions done to the logged space)
        - get batches done (returns the number of experiment batches already carried out)

TODO    
- Batch_space:
    - Attributes
        - All chemical space ()
        - reaction space (as an argument)
        - logged space (as an arguemt)
        - batch_space_size (the number of reactions in a batch)
        - batch_number_taken
        - CH3CN volumes need for stock (vector with chemicals in chemical space as basis)
        - CCl2H2 volumes need for stock (vector with chemicals in chemical space as basis)

    - Methods:
        - take new batch (changes batch space based on logged experiments)
        - generate reaction csv (generates a chemspeed readable csv)
        - calcualted reagent mass need (generates a csv with the mass of reagents required)
        - generate stock csv
        - update logs

""" 
import pickle
import sys
sys.path.append('Python_Modules')
import check_manager as cm
import script_classes as sc


def instantiate_spaces():
    """generates the first instance of the different spaces"""

    METAL_CONCENTRATION = sc.USER_SELECTION.metal_concentration                                                              #concentrations of various chemicals in a reaction (you could individualy change them in the attributes of a chemical)
    DIALDEHYDE_CONCENTRATION = sc.USER_SELECTION.dialdehyde_concentration
    DIAMINE_CONCENTRATION = sc.USER_SELECTION.diamine_concentration
    MONOALDEHYDE_CONCENTRATION = sc.USER_SELECTION.monoaldehdye_concentration

    REACTION_VIAL_TRANSFER_VOLUME = sc.USER_SELECTION.reaction_vial_transfer_volume


    #creating the whole chemical space 
    whole_space = sc.Whole_chemical_space(
        sc.Metal(name='Iron(II) tetrafluoroborate hexahydrate', CAS='13877-16-2', molecular_weight=337.55, solubility=(0,1), price=6, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= METAL_CONCENTRATION, no_coordination_sites=(6), new_chemical=True),
        sc.Metal(name='Zinc tetrafluoroborate', CAS='27860-83-9', molecular_weight=239, solubility=(0,1), price=1.348,  volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=METAL_CONCENTRATION, no_coordination_sites=(6), new_chemical=True),
        sc.Metal(name='Yittrium(III) trifluoromethanesulfonate', CAS='52093-30-8', molecular_weight=536.11, solubility=(0,1), price=17.2,  volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=METAL_CONCENTRATION, no_coordination_sites=(6), new_chemical=True), #yttrim has coordination numbers between 6-9 (in our experiment well just assume 6)
        sc.Metal(name='Tetrakis(acetonitrile)copper(I) tetrafluoroborate', CAS='15418-29-8', molecular_weight=314.56, solubility=(0,1), price=33,  volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=METAL_CONCENTRATION, no_coordination_sites=(4), new_chemical=True), #copper has coordination number 4
        sc.Metal(name='Silver tetrafluoroborate', CAS='14104-20-2', molecular_weight=194.67, solubility=(0,1), price=28.3,  volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=METAL_CONCENTRATION, no_coordination_sites=(4,6), new_chemical=True), #silver has coordiantion numebrs 4, 5, or 6 (in our experiment well just assume 4 and 5)
        sc.Dialdehyde(name='1,10-Phenanthroline-2,9-dicarbaldehyde', CAS='57709-62-3', molecular_weight=236.23, solubility=(0,1), price=165, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=DIALDEHYDE_CONCENTRATION, no_coordination_sites=2, no_imine_reaction_sites=2, new_chemical=True),
        sc.Dialdehyde(name='Pyridine-2,6-dicarbaldehyde', CAS='5431-44-7', molecular_weight=135.122, solubility=(0,1), price=59, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=DIALDEHYDE_CONCENTRATION, no_coordination_sites=2, no_imine_reaction_sites=2, new_chemical=True),
        sc.Diamine(name='2,2\'-(Ethane-1,2-diyl)dianiline', CAS='34124-14-6', molecular_weight=212.297, solubility=(0,1), price=16, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True),
        sc.Diamine(name='2,2\'-(Ethane-1,2-diylbis(oxy))diethanamine', CAS='929-59-9', molecular_weight=148.21, solubility=(3,1), price=0.64, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True),
        sc.Diamine(name= '2,2\'-Oxydiethanamine', CAS='2752-17-2', molecular_weight=104.15, solubility=(0,1), price=40, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True),
        #sc.Diamine(name='1,4-Phenylenedimethanamine', CAS='539-48-0', molecular_weight=136.194, solubility=(1,0), price=4, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True), to be replaced
        sc.Diamine(name='4,4\'-Methylenedianiline', CAS='101-77-9', molecular_weight=198.26, solubility=(0,1), price=0.506, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=DIAMINE_CONCENTRATION, no_coordination_sites=2, no_imine_reaction_sites=2, new_chemical=True),
        sc.Diamine(name='1,3-Benzenedimethanamine', CAS='1477-55-0', molecular_weight=136.19, solubility=(0,1), price=13, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True),
        sc.Diamine(name='Adamantane-1,3-diamine', CAS='10303-95-4', molecular_weight=166.27, solubility=(1,0), price=140, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True),
        sc.Diamine(name='4,4\'-(9H-Fluorene-9,9-diyl)dianiline', CAS='15499-84-0', molecular_weight=348.44, solubility=(0,1), price=10, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True),
        sc.Diamine(name='(S)-4,5,6,7-Tetrahydro-benzothiazole-2,6-diamine', CAS='106092-09-5', molecular_weight=169.25, solubility=(0,0), price=2.2, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True), #commented out because non existant in lab stock
        sc.Diamine(name='[2,2\'-Bipyridine]-4,4\'-diamine', CAS='18511-69-8', molecular_weight=186.22, solubility=(0,0), price=99, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True), #commented out because non existant in lab stock
        sc.Diamine(name='Naphthalene-1,8-diamine', CAS='479-27-6', molecular_weight=158.2, solubility=(0,1), price=10, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True), 
        sc.Diamine(name='4,4\'-Oxydianiline', CAS='101-80-4', molecular_weight=200.24, solubility=(0,1), price=0.742, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True),
        sc.Diamine(name='6-Methyl-1,3,5-triazine-2,4-diamine', CAS='542-02-9', molecular_weight=125.13, solubility=(0,0), price=0.1, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True), #commented out because non existant in lab stock
        sc.Diamine(name='(R)-(+)-1,1\'-Binaphthyl-2,2\'-diamine', CAS='18741-85-0', molecular_weight=284.35, solubility=(1,0), price=132, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=True),
        sc.Monoaldehdye(name='6-Methylpyridine-2-carboxaldehyde', CAS='1122-72-1', molecular_weight=121.14, solubility=(0,1), price=4, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True),
        sc.Monoaldehdye(name='6-Phenylpicolinaldehyde', CAS='157402-44-3', molecular_weight=183.21, solubility=(0,1), price=206, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True),
        sc.Monoaldehdye(name='[2,2\'-Bipyridine]-6-carbaldehyde', CAS='134296-07-4', molecular_weight=184.19, solubility=(0,1), price=258, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True),
        sc.Monoaldehdye(name='2-Quinolinecarboxaldehyde', CAS='5470-96-2', molecular_weight=157.17, solubility=(1,0), price=30.8, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True),
        sc.Monoaldehdye(name='5-Methylpicolinaldehyde', CAS='4985-92-6', molecular_weight=121.14, solubility=(0,1), price=12, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True),
        sc.Monoaldehdye(name='8-methoxyquinoline-2-carbaldehyde', CAS='103854-64-4', molecular_weight=187.19, solubility=(0,1), price=116, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True),
        sc.Monoaldehdye(name='[1,8]Naphthyridine-2-carbaldehyde', CAS='64379-45-9', molecular_weight=158.16, solubility=(1,2), price=258, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True),
        sc.Monoaldehdye(name='4-Formyl-2-methylthiazole', CAS='20949-84-2', molecular_weight=127.16, solubility=(0,1), price=28, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True),
        sc.Monoaldehdye(name='6-Methoxypyridine-2-carbaldehyde', CAS='54221-96-4', molecular_weight=137.14, solubility=(0,1), price=10, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1,new_chemical=True),
        sc.Monoaldehdye(name='1-Methyl-2-imidazolecarboxaldehyde', CAS='13750-81-7', molecular_weight=110.11, solubility=(0,1), price=16, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True),
        sc.Monoaldehdye(name='1-Methyl-1H-benzimidazole-2-carbaldehyde', CAS='3012-80-4', molecular_weight=160.177, solubility=(0,1), price=54, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True),
        sc.Monoaldehdye(name='4-Methyl-1,3-thiazole-2-carbaldehyde', CAS='13750-68-0', molecular_weight=127.16, solubility=(0,1), price=51, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial=MONOALDEHYDE_CONCENTRATION, no_coordination_sites=1, no_imine_reaction_sites=1, new_chemical=True)
        )

    #saving the whole space to a pickle file 
    whole_space.save_to_pickle()

    #taking a subset of the whole chemical space
    intrest_space = sc.Subset_chemical_space(whole_chemical_space=whole_space)

    #these chemicals are removed as they are insoluble in both CH3CN and CCl2H2
    intrest_space.remove_chemicals_from_space(
        sc.Diamine(name='(S)-4,5,6,7-Tetrahydro-benzothiazole-2,6-diamine', CAS='106092-09-5', molecular_weight=169.25, solubility=(0,0), price=2.2, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=False),
        sc.Diamine(name='[2,2\'-Bipyridine]-4,4\'-diamine', CAS='18511-69-8', molecular_weight=186.22, solubility=(0,0), price=99, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=False),
        sc.Diamine(name='6-Methyl-1,3,5-triazine-2,4-diamine', CAS='542-02-9', molecular_weight=125.13, solubility=(0,0), price=0.1, volume_in_reaction_vial=REACTION_VIAL_TRANSFER_VOLUME, concentration_in_stock_vial= DIAMINE_CONCENTRATION, no_coordination_sites= 2, no_imine_reaction_sites=2, new_chemical=False),
        )
    
    intrest_space.divide_space_by_subtype()

    #calculating combinations
    subtype_in_reaction_tuple = sc.USER_SELECTION.subtype_in_reaction_tuple
    reaction_space = sc.Reaction_space(subset_space=intrest_space, whole_space=whole_space)
    reaction_space.calc_subtype_combinations(no_subtype_in_reaction=subtype_in_reaction_tuple)
    #reaction_space.calc_imine_combinations()
    reaction_space.order_chemical_prices()
    reaction_space.order_reaction_prices()
    reaction_space.generate_reaction_space()
    reaction_space.add_standard_reaction(reaction_idx=sc.USER_SELECTION.standard_reaction_idx)
    print(f'The size of the chemical space is {len(reaction_space.reaction_space)} reactions')

    #saving reaction space to a human readable csv
    reaction_space.save_to_csv()

    #saving reaction space as a pickle
    reaction_space.save_to_pickle()

    #creating an empty log (saves an empty log for the batch space to read)
    new_log = sc.Logged_space()

    #creating the batch_space
    batch_space = sc.Batch_space(batch_size=sc.USER_SELECTION.batch_size)
    batch_space.import_logged_reaction_space()
    batch_space.import_reaction_space()
    batch_space.import_whole_chemical_space()
    batch_space.save_to_pickle()
    print('')
    print('SPACES HAVE BEEN INSTANTIATED')                             #Makes it more clear to the user when the instantiate_spaces function has been called

def take_new_batch():
    """Takes a new batch space, and generates masses to measure"""

    #loading the batch pickle
    path = sc.USER_SELECTION.generated_pickle_path + 'batch_space.pickle'                  #reading the batch space for each batch 
    file = open(path, 'rb')
    batch_space = pickle.load(file)
    file.close() 

    #instantiation of spaces in batch space
    batch_space.import_reaction_space()
    batch_space.import_logged_reaction_space()
    batch_space.import_whole_chemical_space()

    #getting the sample space
    batch_space.get_sample_space()

    #generating masses to measure
    batch_space.calc_stock_masses()
    batch_space.save_calc_stock_masses_to_csv()
    batch_space.send_stock_space_to_email()    
    batch_space.save_to_pickle()
    print('')
    print('STOCK SPACE CSV GENERATED')                                      #Makes it more clear to the user when the take_new_batch function has been called


check_manager_1 = cm.Check_Manager()
check_manager_1.add_checks([
    cm.Visual_Bool_Check('Please top up CH2Cl2 vial and added it in the right place and run get_batch_spaces_csvs() again.', 'Has the CH2Cl2 vial been added and topped up? (1=Yes, 0=No): ' ),
    cm.Visual_Bool_Check('Please top up CHCN3 and run get_batch_spaces_csvs() again.', 'Is there enough CHCN3 left in the resevoir? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please empty special waste and run get_batch_spaces_csvs() again.', 'Is the special waste empty enough for one run? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please add reaction vials and make sure they\'re in the right place and run get_batch_spaces_csvs() again.', 'Have all 48 reaction vials been added in the right places? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please add NMR tubes and make sure they\'re in the right place and run get_batch_spaces_csvs() again.', 'Have all NMR tubes been added, and are the two green stickers aligned? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please add MS vials and run get_batch_spaces_csvs() again.', 'Have all the MS vials been added? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please add measured masses into the csv and run get_batch_spaces_csvs() again.', 'Have all the measured masses been added to the stock_space csv? (1=Yes, 0=No): '),
    cm.Visual_Bool_Check('Please add stock vials in the right locations and run get_batch_spaces_csvs() again.', 'Have the stock vials been added in the right locations? (1=Yes, 0=No): '),
    cm.CSV_Mass_Check('Please check your input masses are in the appropiate range OR check there are no empty values and run get_batch_spaces_csvs() again.', 1.5, 0.5, sc.USER_SELECTION.generated_csv_path + 'stock_space.csv')
])

def get_batch_spaces_csvs():
    """Saves the sample space and stock spaces as gunther readable csvs"""
    
    flag = check_manager_1.run_check_list()                                                       #going through the check list to see that everything is ok

    if flag == True:                                                            
        #loading the batch pickle
        path = sc.USER_SELECTION.generated_pickle_path + 'batch_space.pickle'                  #reading the batch space for each batch 
        file = open(path, 'rb')
        batch_space = pickle.load(file)
        file.close() 

        #instantiation of spaces in batch space
        batch_space.import_reaction_space()
        batch_space.import_logged_reaction_space()
        batch_space.import_whole_chemical_space()

        #reading the masses measured and calculating the stock volumes needed
        batch_space.get_mass_measured()                                         
        batch_space.get_stock_space()

        #saving the batch (stock and sample) spaces to csv
        batch_space.save_stock_space_to_csv()                                   
        batch_space.save_sample_space_to_csv()

        #Generating and saving the NMR json
        batch_space.save_NMR_JSON()

        #Generating and saving the MS CSV
        batch_space.save_MS_csv()

        #Sending the generated NMR JSON and MS CSV via email
        batch_space.send_NMR_json_and_MS_csv_to_email()

        #updating logs and saving batch space
        batch_space.update_batch_logs()
        batch_space.save_to_pickle()
        
        print('')
        print('BATCH SPACE CSVS GENERATED')                                     #Makes it more clear to the user when the get_batch_spaces_csvs function has been called



instantiate_spaces()
#take_new_batch()
#get_batch_spaces_csvs()

#conda env location = C:\Users\SCRC112\AppData\Local\miniconda3\envs\chemspeed_env\python.exe