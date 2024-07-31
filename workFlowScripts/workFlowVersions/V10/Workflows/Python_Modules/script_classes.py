import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
import math
import json
import copy
try:
    import win32com.client    #pip install pywin32   (does not work for mac, hence try and except)
except:
    pass

class USER_SELECTION():
    """A class to help keep user changeable variables in one location"""
    raw_cwd = os.getcwd()
    str_cwd = ''.join([letter if letter != '\\' else '/' for letter in raw_cwd])
    generated_csv_path =  str_cwd + '/Reaction_Combinations_workflow/Generated_CSVs/'
    generated_pickle_path = str_cwd + '/Reaction_Combinations_workflow/Generated_pickles/'
    generated_json_path = str_cwd + '/Reaction_Combinations_workflow/Generated_NMR_JSONs/'
    generated_MS_csv_path = str_cwd + '/Reaction_Combinations_workflow/Generated_MS_CSV/'
    
    metal_concentration = 20 * 1.5                                                                                #The concentration (mM) of the metal in the stock vials, as if it had a coordination number of 6 (this attribute can be easily implimented as a class attribute in the metal, but I thought doing this allows for more flexibility)
    dialdehyde_concentration = 0 * 1.5
    diamine_concentration = 30 * 1.5
    monoaldehdye_concentration = 60 * 1.5

    min_transfer_volume = 900                                                                                                     #This is the volume, in microlitre, in the stock vials that Gunther can not physicaly aspirate.
    buffer_volume = 500                                                                                                           #This is the buffer volume, as Gunther does not perfectly aspirate X microlitres of sample
    mosquito_sample_volume = 0                                                                                                  #This is the volume, in microlitres, of a reaction sample in a mosquito rack well (for later use in the cystalography workflow).
    nmr_sample_volume = 600                                                                                                       #This is the volume, in microlitres, of a reaction sample in a NMR tube.
    ms_sample_volume = 50                                                                                                         #This is the volume, in microlitres, of a reaction sample in a MS vial.                                                                    
    reaction_volume = min_transfer_volume + buffer_volume + mosquito_sample_volume + nmr_sample_volume + ms_sample_volume         #this is the volume, in microlitres, a reaction sample must have for all the needed analysis

    reaction_volume_transfer_volume_ratio = 1500/200                                                              #this is a ratio between the transfer volume of a reagent and the total volume in a reaction. Implies -> change in final volume = change in transfer volume (this ratio can be changed, but currently using one that gave the best NMR results). 
    reaction_vial_transfer_volume = reaction_volume / reaction_volume_transfer_volume_ratio                       #The volume in microlitres to transfer from stock vials to sample vials (again, this could be added as an attribute to the chemical class, but it does give up flexibility)
    
    subtype_in_reaction_tuple = (1,0,1,1)                                                                         #This is a vector showing the number of chemical subtypes to include in a reaction. The length of the vector changes depending on the number of chemical subtypes in the whole chemical space. In this case its (Metal=1, Dialdehdye=0, Diamine=1, Monoaldehdye=1). There is a method that allows you to show the index and the chemical subtype (see Reaction_space.show_subtypes_index() )
    batch_size = 48
    standard_reaction_idx = 23                                                                                    #This is the index of where the standard reaction is found in the reaction space (Reaction_space.add_standard_reaction() method is called)
    
    parameters = 'MULTISUPPDC_f'                                                                                  #This is the type of NMR experiment to be run
    num_scans = 64                                                                                                #This is the number of scans the NMR experiment should carry out
    pp_thershold = 0.008                                                                                          #This is a setting for the MULTISUPPDC_f program
    field_presat = 10                                                                                             #This is a setting for the MULTISUPPDC_f program
    solvent = 'CH3CN'                                                                                             #Solvent used for NMR smaple
    ms_injectoin_volume = 1                                                                                       #This is the injection volume (microlitre) for the UV-Vis / MS machine 

class Chemical():
    chemical_ID = 1

    """Parent chemical class with data relaventy to all chemicals"""
    def __init__(self, name: str, CAS:str, molecular_weight:int, solubility:tuple, price:float, volume_in_reaction_vial:float, concentration_in_stock_vial:float, new_chemical:bool) -> None:
        self.name = name                                                                     #name 
        self.CAS = CAS                                                                       #CAS number as shown in the reagent vial 
        self.molecular_weight = molecular_weight                                             #molecular weight in grams per mole
        self.solubility = solubility                                                         #solubility in CCl2H2:CH3CN (as a ratio in a tuple)
        self.price = price                                                                   #this is the price of the chemical per gram
        self.volume_in_reaction_vial = volume_in_reaction_vial                               #(this is volume in microlitre that Gunther dispenses into the reaction vials, along side concentration, it is representative of the stoichiometries) i.e. allows you to put reagents in excess
        self.concentration_in_stock_vial = concentration_in_stock_vial                       #this the concentration in mM of the chemical in the stock solution. For metals with multiple coordiantion numbers, this is the concentration for the metal at a theoreitcal coordination number of 6
        self.ID = Chemical.chemical_ID                                                       #this is the ID of the chemical
        if new_chemical:
            Chemical.chemical_ID += 1                                                            #updating the chemical id after a new chemical has been instantiated.

    def __repr__(self) -> str:
        return self.name

class Metal(Chemical):
    """These are all chemicals which are metals"""
    def __init__(self, name: str, CAS: str, molecular_weight: int, solubility: tuple, price: float, volume_in_reaction_vial: float, concentration_in_stock_vial: float, new_chemical:bool, no_coordination_sites: tuple, selected_coordinaiton_num:int = None) -> None:
        super().__init__(name, CAS, molecular_weight, solubility, price, volume_in_reaction_vial, concentration_in_stock_vial, new_chemical)
        
        self.no_coordination_sites = no_coordination_sites                                    #this is a tuple with the number of coordination site a metal has (may have) (i.e. silver = 8,7,6)
        self.selected_coordination_num = selected_coordinaiton_num                            #this is the coordination number of the metal assumed in a specific reaction.
        if self.selected_coordination_num != None:
            self.volume_in_reaction_vial = self.volume_in_reaction_vial*(6/self.selected_coordination_num)          #[previous metal volume] * (6/ New coor num) :this is the ratio required to for a metal to react with the same (constant) volume of iminie reagent (with a change in coordination number)
        
    def select_coor_num(self, coor_num:int):
        """Changing the coordination number of the metal in an experiment"""
        self.selected_coordination_num = coor_num


class Dialdehyde(Chemical):
    """These are all chemicals which are dialdehydes"""
    def __init__(self, name: str, CAS: str, molecular_weight: int, solubility: tuple, price: float, volume_in_reaction_vial: float, concentration_in_stock_vial: float, new_chemical:bool, no_coordination_sites:int, no_imine_reaction_sites: int) -> None:
        super().__init__(name, CAS, molecular_weight, solubility, price, volume_in_reaction_vial, concentration_in_stock_vial, new_chemical)
        
        self.no_coordination_sites = no_coordination_sites                                     #the number of chelating agents in the molecule
        self.no_imine_reaction_sites = no_imine_reaction_sites                                 #the number of site that react to form an imine
    
class Diamine(Chemical):
    """These are all chemicals which are diamines"""
    def __init__(self, name: str, CAS: str, molecular_weight: int, solubility: tuple, price: float, volume_in_reaction_vial: float, concentration_in_stock_vial: float, new_chemical:bool, no_coordination_sites:int, no_imine_reaction_sites: int) -> None:
        super().__init__(name, CAS, molecular_weight, solubility, price, volume_in_reaction_vial, concentration_in_stock_vial, new_chemical)
    
        self.no_coordination_sites = no_coordination_sites                                     #the number of chelating agents in the molecule
        self.no_imine_reaction_sites = no_imine_reaction_sites                                 #the number of site that react to form an imine
    
class Monoamine(Chemical):
    """These are all chemicals which are monoamines"""
    def __init__(self, name: str, CAS: str, molecular_weight: int, solubility: tuple, price: float, volume_in_reaction_vial: float, concentration_in_stock_vial: float, new_chemical, no_coordination_sites:int, no_imine_reaction_sites: int) -> None:
        super().__init__(name, CAS, molecular_weight, solubility, price, volume_in_reaction_vial, concentration_in_stock_vial, new_chemical)
    
        self.no_coordination_sites = no_coordination_sites                                     #the number of chelating agents in the molecule
        self.no_imine_reaction_sites = no_imine_reaction_sites                                 #the number of site that react to form an imine
    
class Monoaldehdye(Chemical):
    """These are all chemicals which are monoaldehydes"""
    def __init__(self, name: str, CAS: str, molecular_weight: int, solubility: tuple, price: float, volume_in_reaction_vial: float, concentration_in_stock_vial: float, new_chemical:bool, no_coordination_sites:int, no_imine_reaction_sites: int) -> None:
        super().__init__(name, CAS, molecular_weight, solubility, price, volume_in_reaction_vial, concentration_in_stock_vial, new_chemical)
    
        self.no_coordination_sites = no_coordination_sites                                     #the number of chelating agents in the molecule
        self.no_imine_reaction_sites = no_imine_reaction_sites                                 #the number of site that react to form an imine
    
class Whole_chemical_space():
    """A theoretical space with all the chemicals Gunther can run"""
    def __init__(self, *chemical_objects:Chemical) -> None:
        self.space = list(chemical_objects)                                                     #a list of chemicals (as chemical objects) that gunther is able to manipulate (this is limited by the chemspeed script)
    
    def show_chemical_space(self):
        """prints out the list of chemicals in the space"""
        print(self.space)
    
    def show_chemical_space_size(self):
        """prints out the size of """
        print(len(self.space))

    def save_to_pickle(self):
        """saves the whole chemical space to a pickle file"""
        path = USER_SELECTION.generated_pickle_path+'whole_chemical_space.pickle'
        file = open(path, 'wb')
        pickle.dump(self, file)
        file.close()

class Subset_chemical_space():
    """A the chemical space which we wish the ML to study"""
    def __init__(self, whole_chemical_space:Whole_chemical_space) -> None:
        self.space = whole_chemical_space.space.copy()                                                  #a list of the chemical space (as above). Chemicals in the whole space will be removed to create the subspace.
        self.divided_space = {}                                                                  #this is a dictionary with the chemical subtype as a key and the list of chemicals of this subtype as the value
    
    def remove_chemicals_from_space(self, *chemicals:Chemical):
        """removes any unwanted chemicals from the whole chemicals space, tranforming it to the subsetspace"""
        for chemical_to_remove in chemicals:
            for whole_chemical in self.space:
                if chemical_to_remove.name == whole_chemical.name:
                    self.space.remove(whole_chemical)
    
    def show_chemical_space(self):
        """prints out the list of chemicals in the space"""
        print(self.space)
    
    def show_chemical_space_size(self):
        """prints out the size of the space """
        print(len(self.space))
    
    def divide_space_by_subtype(self):
        """divides the chemical space into the different chemical subtype into a dictionary"""
        for chemical in self.space:
            chemical_subtype = chemical.__class__.__name__ 
            if chemical_subtype not in self.divided_space.keys() and chemical_subtype != 'Metal':            #adds the initial instance of a chemical subtype to a key (if its not a metal)
                self.divided_space[f'{chemical_subtype}'] = [chemical]
            
            elif chemical_subtype in self.divided_space.keys() and chemical_subtype != 'Metal':              #if subtype key already exists add chemical to this subset
                self.divided_space[f'{chemical_subtype}'].append(chemical)

            if chemical_subtype not in self.divided_space.keys() and chemical_subtype == 'Metal':            #as before, however with metals, each different coordination number is seen as a 'unique metal' (this will make combination calculations for reactions with same metal but different CN more easy)
                self.divided_space[f'{chemical_subtype}'] = []
                if type(chemical.no_coordination_sites) == int:                                              #checking that if the tuple is interpreted as an integer or tuple by python
                    coordination_number =chemical.no_coordination_sites                                             
                    new_chemical = Metal(name=chemical.name, CAS=chemical.CAS, molecular_weight=chemical.molecular_weight, solubility=chemical.solubility, price=chemical.price, volume_in_reaction_vial=chemical.volume_in_reaction_vial, concentration_in_stock_vial= chemical.concentration_in_stock_vial, no_coordination_sites=chemical.no_coordination_sites, selected_coordinaiton_num=coordination_number, new_chemical=False)
                    new_chemical.ID = chemical.ID                                                            #Making sure that the same checmical have the same chemical.ID
                    self.divided_space[f'{chemical_subtype}'].append(new_chemical)
                
                elif type(chemical.no_coordination_sites) == tuple:
                    for coordination_number in chemical.no_coordination_sites:
                        new_chemical = Metal(name=chemical.name, CAS=chemical.CAS, molecular_weight=chemical.molecular_weight, solubility=chemical.solubility, price=chemical.price, volume_in_reaction_vial=chemical.volume_in_reaction_vial, concentration_in_stock_vial= chemical.concentration_in_stock_vial, no_coordination_sites=chemical.no_coordination_sites, selected_coordinaiton_num=coordination_number, new_chemical=False)
                        new_chemical.ID = chemical.ID                                                       #Making sure that the same checmical have the same chemical.ID
                        self.divided_space[f'{chemical_subtype}'].append(new_chemical)
                
                else:
                    print(f'Check {chemical.name}\'s coordination number tuple')
                    break

            elif chemical_subtype in self.divided_space.keys() and chemical_subtype == 'Metal':              #if subtype key already exists add chemical to this subset
                if type(chemical.no_coordination_sites) == int:                                              #checking that if the tuple is interpreted as an integer or tuple by python
                    coordination_number =chemical.no_coordination_sites                                             
                    new_chemical = Metal(name=chemical.name, CAS=chemical.CAS, molecular_weight=chemical.molecular_weight, solubility=chemical.solubility, price=chemical.price, volume_in_reaction_vial=chemical.volume_in_reaction_vial, concentration_in_stock_vial= chemical.concentration_in_stock_vial, no_coordination_sites=chemical.no_coordination_sites, selected_coordinaiton_num=coordination_number, new_chemical=False)
                    new_chemical.ID = chemical.ID                                                            #Making sure that the same checmical have the same chemical.ID
                    self.divided_space[f'{chemical_subtype}'].append(new_chemical)
                
                elif type(chemical.no_coordination_sites) == tuple:
                    for coordination_number in chemical.no_coordination_sites:
                        new_chemical = Metal(name=chemical.name, CAS=chemical.CAS, molecular_weight=chemical.molecular_weight, solubility=chemical.solubility, price=chemical.price, volume_in_reaction_vial=chemical.volume_in_reaction_vial, concentration_in_stock_vial= chemical.concentration_in_stock_vial, no_coordination_sites=chemical.no_coordination_sites, selected_coordinaiton_num=coordination_number, new_chemical=False)
                        new_chemical.ID = chemical.ID                                                        #Making sure that the same checmical have the same chemical.ID
                        self.divided_space[f'{chemical_subtype}'].append(new_chemical)
                
                else:
                    print(f'Check {chemical.name}\'s coordination number tuple')
                    break
            
class Reaction():
    """Stores information of individual reactions"""
    reaction_generated = 1                                                                      #keeps track of the number of chemical reactions generated

    def __init__(self, final_reaction_volume:float, reagents:list, whole_space:Whole_chemical_space=None) -> None:
        if whole_space != None:
            self.chemical_vector = whole_space.space
        else:
            self.chemical_vector = None
        
        self.final_reaction_volume = final_reaction_volume                                       #the volume of the reaction sample in the reagent vial (the vial will be topped up with CH3CN)
        self.reagents = reagents                                                                 #a list of the reagents in the reaction (does not include solvents)
        self.volume_of_reagents_required = []                                                    #a list of all chemicals in the subset chemical space and their volumes required to make this reaction mixture.
        self.reagents_volume = 0
        self.unique_identifier = self.reaction_generated                                         #The uniqe identifier of the reaction is just its generated sequencial number 
        Reaction.reaction_generated += 1                                                             #updating the reaction count

    def get_volumes_vector(self):
        """gets a vector of the volumes of the reagents with chemicals in the whole chemicals space as basis"""
        for basis_vector in self.chemical_vector:                                                #iterating through the various basis vectors and reagents in the reaction
            basis_vector_found = False
            for reagent in self.reagents:
                if basis_vector.name == reagent.name and reagent.concentration_in_stock_vial != 0:
                    self.volume_of_reagents_required.append(reagent.volume_in_reaction_vial)     #adding the transfer volume to the volume of reagents required
                    self.reagents_volume += reagent.volume_in_reaction_vial                      #adding the found volume to the total reagent volume
                    basis_vector_found = True
            if basis_vector_found == False:
                self.volume_of_reagents_required.append(0)
            else:
                basis_vector_found = False
        
        self.volume_of_reagents_required.append(self.final_reaction_volume-self.reagents_volume)  #the volume of CH3CN need to top up to the final volume   

    def __repr__(self) -> str:
        return str(self.reagents)

class Reaction_space():
    """A space whos vectors represent a reaction with basis vectors in the subset chemical space"""
    def __init__(self, subset_space:Subset_chemical_space, whole_space:Whole_chemical_space) -> None:
        self.subset_space = subset_space                                                         #this is the subset chemical space. The divided space will be usefull in the combination calc
        self.whole_space = whole_space                                                           #this is the whole space, it is used for calcualting reagent volumes
        self.reaction_space = []                                                                 #a list that stores different chemical reactions as reaction objects
        self.reagent_space = []                                                                  #a list that stores different chemcial reactions as their regent list

    def show_subtypes_index(self):
        """shows the chemical subtype and the index for calculating combinations"""
        for idx, subtype in enumerate(self.subset_space.divided_space):
            print(idx, subtype)
    
    def calc_subtype_combinations(self, no_subtype_in_reaction:tuple):
        """gets the combination of reagents depending on the amount per chemical subtype in a reaction (based on the inputed tuple) returns a list (with reagent in reaction)"""
        combination_list = []
        combination_space = []

        for key_index, chemical_subtype in enumerate(self.subset_space.divided_space):                      #iterating through the chemical subtypes        
            for i in range(0, no_subtype_in_reaction[key_index]):                                           #iterating through the number of times a subtype appears in a reaction (as selected by the tuple argument)
                combination_list.append(self.subset_space.divided_space[f'{chemical_subtype}'])
        
        for subtype_lst in combination_list:                                                                #iterating through chemical subtypes and merging their combinations each time
            combination_space = self.add_combination(combination_space, subtype_lst)

        self.reagent_space += combination_space                                                             #adding the computed combination space to the reaction space

    def calc_imine_combinations(self):
        """Calculates the possible combination of imines and """
        amine_list = []                                                                                     #current limitation of this imine combination is that more complex imines (i.e. Adamantane-1,3-diamine + 5-Methylpicolinaldehyde + 2-Quinolinecarboxaldehyde) are not possible
        aldehyde_list = []
        combination_list = [amine_list, aldehyde_list]
        imine_space = []
        for key_index, chemical_subtype in enumerate(self.subset_space.divided_space):
            if chemical_subtype == 'Diamine' or chemical_subtype == 'Monoamine':
                amine_list += self.subset_space.divided_space[f'{chemical_subtype}']
            
            elif chemical_subtype == 'Dialdehyde' or chemical_subtype == 'Monoaldehdye':
                aldehyde_list += self.subset_space.divided_space[f'{chemical_subtype}']
        
        for subtype_lst in combination_list:                                                                #iterating through amine and aldehdye chemicals and merging their combinations each time
            imine_space = self.add_combination(imine_space, subtype_lst)
        
        self.reagent_space += imine_space                                                                   #adding the calcualted imine combinations into the reaction space 
    
    def order_chemical_prices(self):
          """orders the chemicals in the nested lists based on their price (more cheapest to most expensive)"""
          reaction_list = self.reagent_space
          numeration = len(reaction_list)
          for i in range(numeration):
               reaction_list[i] = Reaction_space.order_chemicals(reaction_list[i])
    
    def order_reaction_prices(self):
          """orders the reactions based on their prices (form cheapest to most expensive)"""
          lst_to_sort = self.reagent_space
          self.reagent_space = Reaction_space.multi_list_sort(lst_to_sort)

    def generate_reaction_space(self):
        """Fills in the empty reaction space with reaction objects"""
        for reagent_combo in self.reagent_space:
            reaction = Reaction(final_reaction_volume=USER_SELECTION.reaction_volume, reagents=reagent_combo, whole_space=self.whole_space)
            reaction.get_volumes_vector()
            self.reaction_space.append(reaction)

    def add_standard_reaction(self, reaction_idx):
        """Adds a standard reaction to smaple 1 of each batch."""
        
        batch_size = USER_SELECTION.batch_size
        reaction_space = self.reaction_space
        
        standard_reaction = reaction_space[reaction_idx]
        standard_reaction_final_volume = standard_reaction.final_reaction_volume
        standard_reaction_reagents = standard_reaction.reagents
        standard_reaction_chemical_vector = standard_reaction.chemical_vector
        standard_reaction_reagents_volume = standard_reaction.reagents_volume
        standard_reaction_volume_of_reagents_required = standard_reaction.volume_of_reagents_required

        #getting the attributes of the standard reaction.
        multiple_int = 0                                                                                    #iterating via integer batch steps to find the index of where to append the repeated standard reaction
        multiple = 0
        while multiple+batch_size<len(reaction_space):
            multiple = multiple_int*(batch_size)

            #Creating a new reaction with the same attributes as the standard reaction
            reaction = Reaction(final_reaction_volume=standard_reaction_final_volume, reagents=standard_reaction_reagents)
            reaction.chemical_vector = standard_reaction_chemical_vector
            reaction.final_reaction_volume = standard_reaction_final_volume
            reaction.reagents = standard_reaction_reagents
            reaction.volume_of_reagents_required = standard_reaction_volume_of_reagents_required
            reaction.reagents_volume = standard_reaction_reagents_volume
            reaction.unique_identifier = '1'+'batch'+str(multiple_int)
            
            reaction_space.insert(multiple, reaction)
            multiple_int = multiple_int + 1
   
    def show_chemical_space(self):
        """prints out the list of chemicals in the space"""
        print(self.reagent_space)
    
    def get_space_size(self):
        """returns the size of the reaction space"""
        return(len(self.reaction_space))

    def show_chemical_space_size(self):
        """prints out the size of the space"""
        print(len(self.reagent_space))

    def save_to_pickle(self):
        """save the reaction space oject as a pickle"""
        path = USER_SELECTION.generated_pickle_path+'reaction_space.pickle'
        file = open(path, 'wb')
        pickle.dump(self, file)
        file.close()
    
    def save_to_csv(self):
        """save the reaction space to a csv, including unique identifiers"""
        dct_to_convert = {}
        columns_names = ['Unique Identifier']+['Reaction'] + [reagent.name for reagent in self.whole_space.space] + ['CH3CN']                   #columns are: reaction name + reagents + solvents (order is of utmost importance)
        path = USER_SELECTION.generated_csv_path + 'reaction_space.csv'
        for reaction_idx, reaction in enumerate(self.reaction_space):
            dct_to_convert[f'{reaction_idx}'] = [reaction.unique_identifier]+[str(reaction.reagents)]+reaction.volume_of_reagents_required
        df = pd.DataFrame.from_dict(dct_to_convert, orient='index', columns=columns_names)
        df.to_csv(path, index=False)

    @staticmethod
    def add_combination(list_1:list, list_2:list):
        """takes in two reagent lists and returns all their possible combinations"""
        combination_list = []
        
        if len(list_1) == 0 or len(list_2) == 0:                                                          #if either list is empty the combination list is just the filled list 
                combination_list = list_1 + list_2
        else:
            for chemical_2 in list_2:                                                                     #enumerating through all list items
                for chemical_1 in list_1:
                    if type(chemical_1) == list and type(chemical_2) == list:                             #a conditional so that the appended items will allways result in the form [reagent_1, reagent_2]. Prevents post cleanup
                        combination_list.append(chemical_1 + chemical_2)
                    
                    elif type(chemical_1) == list and type(chemical_2) != list:
                        combination_list.append(chemical_1 + [chemical_2])
                    
                    elif type(chemical_1) != list and type(chemical_2) == list:
                        combination_list.append([chemical_1] + chemical_2)
                        
                    else:
                        combination_list.append([chemical_1,chemical_2])
        
        return combination_list
        
    def order_chemicals(reaction):
          """orders chemicals from the most expensive to the least expensive"""
          #bubble sort algorithm taken from https://www.geeksforgeeks.org/bubble-sort/
          
          list_to_return = reaction.copy()
          n = len(list_to_return)
          
          # Traverse through all array elements
          for i in range(n):
               swapped = False
               
               # Last i elements are already in place
               for j in range(0, n-i-1):
                    # Traverse the array from 0 to n-i-1
                    # Swap if the element found is greater
                    # than the next element
                    if list_to_return[j].price < list_to_return[j+1].price:
                         list_to_return[j], list_to_return[j+1] = list_to_return[j+1], list_to_return[j]
                         swapped = True
               
               if (swapped == False):
                    break
          return list_to_return
    
    def multi_list_sort(list_name):
        """sorts a list based on the chemical prices inside the nested list"""
        sorted_list = []
        for reaction in list_name:
            largest_found = 0
            for sorted_reaction_idx, sorted_reaction in enumerate(sorted_list):
                if len(sorted_list) == 0:
                        sorted_list.append(reaction)
                #getting the similarities between the two reactions
                price_idx = 0
                while reaction[price_idx].price*reaction[price_idx].volume_in_reaction_vial == sorted_reaction[price_idx].price*sorted_reaction[price_idx].volume_in_reaction_vial and min(len(reaction), len(sorted_reaction))-1 > price_idx:
                    price_idx +=1
                
                #conditions and consequences to take once difference is found
                
                #if reactions are the exact same 
                if reaction == sorted_reaction:
                    largest_found += 1
                
                #if reactions are the same but one has additional chemicals
                elif len(reaction) > len(sorted_reaction) and reaction[price_idx].price*reaction[price_idx].volume_in_reaction_vial == sorted_reaction[price_idx].price*sorted_reaction[price_idx].volume_in_reaction_vial:
                    largest_found += 1
                
                # if the reactions are not the same and have the same string length
                elif len(reaction) == len(sorted_reaction) and reaction[price_idx].price*reaction[price_idx].volume_in_reaction_vial > sorted_reaction[price_idx].price*sorted_reaction[price_idx].volume_in_reaction_vial:
                    largest_found += 1
                
                #if reactions are not the same and have different string lengths
                elif len(reaction) > len(sorted_reaction) and reaction[price_idx].price*reaction[price_idx].volume_in_reaction_vial > sorted_reaction[price_idx].price*sorted_reaction[price_idx].volume_in_reaction_vial:
                    largest_found += 1
                
                #if reactions are not the same and have different string lengths
                elif len(reaction) < len(sorted_reaction) and reaction[price_idx].price*reaction[price_idx].volume_in_reaction_vial > sorted_reaction[price_idx].price*sorted_reaction[price_idx].volume_in_reaction_vial:
                        largest_found += 1
            
            sorted_list.insert(largest_found, reaction)
            largest_found = 0
        return sorted_list
    
class Logged_space():
    """A theorical space with a list of completed reactions"""
    def __init__(self) -> None:
        #upon instantiation, create an empty log
        self.logged_space = []
        path = USER_SELECTION.generated_pickle_path+'logged_space.pickle'
        file = open(path, 'wb')
        pickle.dump(self, file)
        file.close()
    
    def update_logs(self, batch_list:list):
        """adds the batch of chemicals in the log"""
        self.logged_space += batch_list

    def retrieve_batchs_done(self, batch_size:int):
        """returns the number of batch experiments carried out so far"""
        return int(len(self.logged_space)/batch_size)

class Batch_space():
    """A theoretical space with the reaction to carry out"""
    def __init__(self, batch_size:int) -> None:
        self.batch_size = batch_size
        self.whole_chemical_space = None
        self.reaction_space = None
        self.logged_space = None
        self.batch_number = None
        self.stock_space = None                                                                                #this is the 
        self.sample_space = None                                                                               #A list with all the reaction present (as reaction objects) in the batch 
        self.stock_mass_vector = []                                                                            #This is a list contaning the mass of each chemical needed in the stock solutions
        self.CH3CN_volume_vector = []                                                                          #The volume (in microlitres) of CH3CN required for each chemical in the whole chemical space (chemicals not in the batch space are get an addition of 0)
        self.CCl2H2_volume_vector = []                                                                         #The volume (in microlitres) of CH2Cl2 required for each chemical in the whole chemical space (chemicals not in the batch space are get an addition of 0)
        
    def import_reaction_space(self):
        """Imports the reaction space after initiation, again."""
        path = USER_SELECTION.generated_pickle_path+'reaction_space.pickle'
        file = open(path, 'rb')
        self.reaction_space = pickle.load(file)
        file.close()
        
    def import_logged_reaction_space(self):
        """Imports the logged space after initiation, again."""
        path = USER_SELECTION.generated_pickle_path+'logged_space.pickle'
        file = open(path, 'rb')
        self.logged_space = pickle.load(file)
        file.close()

    def import_whole_chemical_space(self):
        """Imports the whole chemical space after initiation, again."""
        path = USER_SELECTION.generated_pickle_path+'whole_chemical_space.pickle'
        file = open(path, 'rb')
        self.whole_chemical_space = pickle.load(file)
        file.close()

    def get_sample_space(self):
        """Gets the reactions which should happen in the sample vials"""
        batchs_done = self.logged_space.retrieve_batchs_done(self.batch_size)                                           #gets the batch done (current batch number -1)]
        print(f'The current batch number gunther is running is {batchs_done}. (Batches numbers start from 0). The last batch number is {math.ceil(len(self.reaction_space.reaction_space)/USER_SELECTION.batch_size)-1}')
        self.batch_number = batchs_done
        reaction_space_size = self.reaction_space.get_space_size()                                                      #gets the size of the reaction space
        if len(self.logged_space.logged_space)>=len(self.reaction_space.reaction_space):                                #checks if all the reactions have been completed
            self.sample_space = []
            print('ALL REACTIONS DONE, EXPERIMENT FINISHED')        
        else:
            current_batch_number = batchs_done
            number_will_be_done_reactions = (current_batch_number+1)*self.batch_size
            if number_will_be_done_reactions > reaction_space_size:                                                     #checks that the upcoming batch does not go over the reaction space size
                self.sample_space = self.reaction_space.reaction_space[current_batch_number*self.batch_size:]

            else:
                self.sample_space = self.reaction_space.reaction_space[current_batch_number*self.batch_size:(current_batch_number+1)*self.batch_size]

    def save_to_pickle(self):
        """Save the batch space to a pickle file"""
        path = USER_SELECTION.generated_pickle_path+'batch_space.pickle'
        file = open(path, 'wb')
        pickle.dump(self, file)
        file.close()

    def save_to_stock_csv(self):
        """Save the stock_space to a Gunther readable csv"""
        pass

    def save_sample_space_to_csv(self):
        """saves the smaple space to a Gunther readable csv"""
        dct_to_convert = {} 
        columns_names = ['Unique Identifier']+['Reaction']+[reagent.name for reagent in self.whole_chemical_space.space] + ['CH3CN']                      #columns are: reaction name + reagents + solvents (order is of utmost importance)
        path = USER_SELECTION.generated_csv_path + 'sample_space.csv'  
        for reaction_idx, reaction in enumerate(self.sample_space):
            dct_to_convert[f'{reaction_idx}'] = [reaction.unique_identifier] + [str(reaction.reagents)] + reaction.volume_of_reagents_required
        df = pd.DataFrame.from_dict(dct_to_convert, columns=columns_names, orient='index')
        df.to_csv(path, index=False)

    def calc_stock_masses(self):
        """calculates the masses of the requied chemicals and appends them to the stock mass vector"""
        self.stock_mass_vector.clear()
        for chemical in self.whole_chemical_space.space:                                                                           #iterating through the chemical bassis vector present int the batch space and checking their presence in each reation
            chemical_volume = 0
            for reaction in self.sample_space:                                                                                     #getting the total volume of a chemical in the sample space
                for reagent in reaction.reagents:
                    if chemical.name == reagent.name:
                        chemical_volume += reagent.volume_in_reaction_vial
            
            if chemical_volume == 0:
                self.stock_mass_vector.append(0)
            
            else:
                min_transfer_volume = USER_SELECTION.min_transfer_volume                                                                                                   #minimum transfer volume for blue caps (800≈900 microlires) at calibration (0,0,0) for shaker and (0,0,-59) for shaker insert, minimum transfer for white caps (770≈900 microlires) at calibration (0,0,0) for shaker and (0,0, -59) for shaker insert 
                buffer_volume = (chemical.volume_in_reaction_vial)*2 
                total_volume = chemical_volume + buffer_volume + min_transfer_volume                                                        #this is the tat0l stock volume required for a specific chemical basis vector 
                chemical_Mw = chemical.molecular_weight
                chemical_concentration = chemical.concentration_in_stock_vial
                chemical_mass_required = (chemical_concentration/1000)*(total_volume/1000000)*chemical_Mw                           #concentration = moles/volume = mass/Mw/volume (mass = concentration*volume*Mw)
                self.stock_mass_vector.append(chemical_mass_required)
                chemical_volume = 0                                                                                                 #at the end of the chemical iteration, add the calculated mass reqruied to the mass vector, reset the chemical_volume

    def save_calc_stock_masses_to_csv(self):
        """Saves the reqiured masses to measure to a human readable csv"""
        mass_dct = {}                                                                                                               #An empty dictionary to populate and then read as a pandas dataframe
        path = USER_SELECTION.generated_csv_path + 'stock_space.csv'

        mass_dct['Chemical_index'] = [i+1 for i in range(len(self.whole_chemical_space.space))]
        mass_dct['Chemical'] = self.whole_chemical_space.space
        mass_dct['Mass to measure (in grams)'] = self.stock_mass_vector
        mass_dct['Actual mass measured'] = [None if mass !=0 else 0 for mass in self.stock_mass_vector]                             #to make it more userfriendly, reagents not present in the batch space are automaticaly assigned 0

        df = pd.DataFrame.from_dict(mass_dct, orient='columns')                                                                     #making a pandas dataframe as its more simple to create + save object as a csv
        df.to_csv(path, index=False)
    
    def send_stock_space_to_email(self):
        """sends the generated csv to email to then print"""
        df_path = USER_SELECTION.generated_csv_path + 'stock_space.csv'
        df = pd.read_csv(df_path)

        pdf_path = USER_SELECTION.generated_csv_path + 'stock_space.pdf'
        
        fig, ax =plt.subplots(figsize=(12,4))                                      #saving the df as a matplot table, to then save as pdf (code taken from https://stackoverflow.com/questions/33155776/export-pandas-dataframe-into-a-pdf-file-using-python)
        ax.axis('tight')
        ax.axis('off')
        the_table = ax.table(cellText=df.values,colLabels=df.columns,loc='center')

        pp = PdfPages(pdf_path)
        pp.savefig(fig, bbox_inches='tight')
        pp.close()


        try:
            ol = win32com.client.Dispatch('Outlook.Application')                        #sending stock space to print via outlook
            olmailitem=0x0
            newmail = ol.CreateItem(olmailitem)
            newmail.Subject = 'Print CSV'
            newmail.To = 'printbw1@liverpool.ac.uk'
            newmail.Attachments.Add(pdf_path)
            newmail.Display()
            newmail.Send()
            print('Stock space successfully sent')
        
        except:
            print('Email sending failed, manualy send stock space')
            pass


    def get_mass_measured(self):
        """Gets the actual mass measured and adds them into a vector"""
        path = USER_SELECTION.generated_csv_path + 'stock_space.csv'                                                                   
        df = pd.read_csv(path, index_col=None)
        self.stock_mass_vector = df['Actual mass measured'].tolist()
        original_mass = df['Mass to measure (in grams)'].tolist()
     
    def get_stock_space(self):
        """Calculates the volumes of CH3CN and CH2Cl2 for the chemicals basis in the batch space"""
        
        self.CCl2H2_volume_vector = []                                                                                             #Ensures that the vectors are completly empty
        self.CH3CN_volume_vector = []

        for chemical_index, chemical in enumerate(self.whole_chemical_space.space):                                                 #iterating through the chemicals
            chemical_mass = self.stock_mass_vector[chemical_index]
            chemical_Mw = chemical.molecular_weight
            chemical_concentration = chemical.concentration_in_stock_vial/1000                                                      #divide by 1000 to get concentration in M
            if chemical_concentration != 0:                                                                                         #some chemicals have a may have a concentration of 0 (division by 0 = error)
                final_stock_volume = chemical_mass/chemical_Mw/chemical_concentration                                               #volume = mass/MW/concentration
                solubility_CCl2H2, solubility_CH3CN = chemical.solubility
                if solubility_CCl2H2 == 0 and solubility_CH3CN == 0:                                                                #Some chemicals my be insoluble in both solubility tuple = (0,0)     
                    self.CCl2H2_volume_vector.append(0)
                    self.CH3CN_volume_vector.append(0) 

                else:
                    volume_CCl2H2 = (solubility_CCl2H2/(solubility_CCl2H2+solubility_CH3CN))*final_stock_volume*1000000              #subdividing the stock volume based on the chemicals solubility in CH3CN / CH2Cl2 and muilitplying by 1000000 to get volume in microlitre
                    volume_CH3CN = (solubility_CH3CN/(solubility_CH3CN+solubility_CCl2H2))*final_stock_volume*1000000
                
                    self.CCl2H2_volume_vector.append(volume_CCl2H2)
                    self.CH3CN_volume_vector.append(volume_CH3CN)
            else:
                final_stock_volume = 0
                self.CCl2H2_volume_vector.append(0)
                self.CH3CN_volume_vector.append(0)
    
    def save_stock_space_to_csv(self):
        """Saves the generated stock space to a csv"""
        path = USER_SELECTION.generated_csv_path + 'stock_space.csv'
        df = pd.read_csv(path, index_col=None)                                      #reading the mass calculated csv 
        df['CH3CN'] = self.CH3CN_volume_vector                                      #adding the CH3CN volumes to the df
        df['CCl2H2'] = self.CCl2H2_volume_vector                                    #adding the CCl2H2 volumes to the df
        df.to_csv(path, index=False)

    def update_batch_logs(self):
        """Updates the log class with the sample space and saves it as a pickle"""
        
        self.logged_space.update_logs(batch_list=self.sample_space)                  #updating logs
        
        path = USER_SELECTION.generated_pickle_path+'logged_space.pickle'            #saving logs                              
        file = open(path, 'wb')
        pickle.dump(self.logged_space, file)
        file.close()
    
    def save_NMR_JSON(self):
        """Saves a JSON to be read by the script for the NMR autosampler"""
        
        nmr_file_name = 'batch' + str(self.batch_number) + '.json'
        path = USER_SELECTION.generated_json_path + nmr_file_name
        json_to_save = {}
        
        
        for reaction_num, reaction in enumerate(self.sample_space):
            sample_info_text = str(reaction.unique_identifier) + ': '                                              #Generating a string with reaction id, and reagents to be read by Bruker app
            sample_info_text += str(reaction.reagents)
            sample_info_text += ' : ['
            for reagent in reaction.reagents:
                sample_info_text += str(reagent.ID) + ', '
            
            sample_info_text += ']'
                       
            json_to_save[f"{reaction_num + 1}"] = {                                                                #This is the json format readable by the NMR autosampler (autosampler script and code was created by Dr.Filip Szczypinski)
                "sample_info": sample_info_text,
                "solvent":  USER_SELECTION.solvent,
                "nmr_experiments": [
                    {
                        "parameters": USER_SELECTION.parameters,
                        "num_scans": USER_SELECTION.num_scans,
                        "pp_threshold": USER_SELECTION.pp_thershold,
                        "field_presat": USER_SELECTION.field_presat
                    }
                ]
            } 

        with open(path, 'w', newline="\n") as json_output:                                                          # saving the generated NMR json
            json.dump(json_to_save, json_output, indent=4)
            
    def save_MS_csv(self):
        """Saves the batch reactions as samples in a LCMS autosampler readable csv"""

        csv_dct = {                                                                                                 #The dictionary to be saved as a csv                                                                               
            'INDEX': [],                                                                                            #An index for the autosampler is reqruired
            'FILE_NAME': [],                                                                                        #This is the file name for the samples UV and MS spectra
            'FILE_TEXT': [],                                                                                        #IDK what this does, I think it just makes the sample spectra more human interpretable
            'MS_FILE': [],                                                                                          #This is the name of the file used for MS protols (i.e. injection speeds, M/Z range)
            'MS_TUNE_FILE': [],                                                                                     #Similar to the MS_file its a file name. The file is generated by the Water's LCMS machine when a user wants to run the same spectra over different samples
            'INLET_FILE': [],                                                                                       #Agian this is similar to the two previous.
            'SAMPLE_LOCATION': [],                                                                                  #This is the location of the sample in the LCMS rack. In this case, the reaction order in the batch space is the same as the the sample location indx 
            'INJ_VOL': []                                                                                           #This is the injection volume for MS / UV-Vis 
            }

        for reaction_indx, reaction in enumerate(self.sample_space):                                                #Iterating through the reactions in the batch space and adding its sample parameters to the csv_dct 
            text_var = str(reaction.unique_identifier)
            csv_dct['INDEX'].append(reaction_indx + 1)
            csv_dct['FILE_NAME'].append(text_var)
            csv_dct['FILE_TEXT'].append(text_var)                   #The file name is the batchnumber_reactionid
            csv_dct['MS_FILE'].append('SupraChemCage')
            csv_dct['MS_TUNE_FILE'].append('SupraChemCage')
            csv_dct['INLET_FILE'].append('SupraChemCage')
            csv_dct['SAMPLE_LOCATION'].append(f'1:{reaction_indx+1}')
            csv_dct['INJ_VOL'].append(USER_SELECTION.ms_injectoin_volume)

        ms_file_name = 'batch' + str(self.batch_number) + '.csv'
        path = USER_SELECTION.generated_MS_csv_path + ms_file_name                                          #Reading the dictionary as a dataframe and saving it as a csv
        df = pd.DataFrame.from_dict(csv_dct)
        df.to_csv(path, index=False)
    
    def send_NMR_json_and_MS_csv_to_email(self):
        """Sending the generated NMR Jason to email via outlook"""
        
        nmr_file_name = 'batch' + str(self.batch_number) + '.json'
        ms_file_name = 'batch' + str(self.batch_number) + '.csv'

        json_path = USER_SELECTION.generated_json_path + nmr_file_name
        csv_path = USER_SELECTION.generated_MS_csv_path + ms_file_name
        try:
            ol = win32com.client.Dispatch('Outlook.Application')                                                    #sending stock space to print via outlook
            olmailitem=0x0
            newmail = ol.CreateItem(olmailitem)
            newmail.Subject = 'NMR json and MS CVS'
            newmail.To = 'chemspeedgunther@gmail.com'
            newmail.Attachments.Add(json_path)
            newmail.Attachments.Add(csv_path)
            newmail.Display()
            newmail.Send()
            print('NMR json and MS CSV successfully sent')

        except Exception as e:
            print(e)
            print('Email sending failed, manualy send stock space')
            pass
    