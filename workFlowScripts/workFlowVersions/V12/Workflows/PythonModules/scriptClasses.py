
"""
This module is responsible for the pythonic representation of chemistry, reaction handeling, processing and organisation between chemspeed, LCMS and NMR platforms.

Inoder to do so the following classes will be created:
- Various chemical classes: these store information of the chemical and will help with price ranking, calaculating mass, concentrations, generation of reaction spaces, e.t.c.
- Chemical space: stores inforamtion of the possible chemical space Gunther can search.
- Focused chemical space: stores information of the chemical space (a subset of the chemical space whos combinations we are interested in).
- Reaction class: these store information on the reagents, volumes of each chemical in the reaction space to make this reaction (combination). These will compiled to generate a chemspeed readbale csv, to then physicaly carry out these reactions (see batchspace and stockspace).
- Batch space: the space of reactions for a specific batch. This class calculates the volume of reagents in a batch to measure to make up stock solutions on the chemspeedplatform (the stockspace), calcualtes the transfervolumes to make up the reactions in the batchspace and saves them as a csv to be read by the chemsped platform.

A more indepth look at the functioanlity of the classes:

USERSELECTION:
- Imports all the required user parameters depending on the workflow.
- Acts as a container for global variables.

Chemical:
- The parent class for all chemical subtypes. Helps standardise what a 'chemicals' is.
- Containes attributes that are essential for the next parts of the workflow (combination calculations, masses calculations, sorting algorithms).

Metal(chemical):
- Has the same indespensible attributes of the chemical parent class.
- Contains additional information on the coordination number, and the predicted coordination number in the experiment (since metals have different coordinaiton numbers, this has to be considered when generateing combinations and calculating the transfer volumes).
- Contains additional information on metals (not essential to programme).

Dialdehyde(chemical):
- Has the same indespensible attributes of the chemical parent class.
- Contains additional information on dialdehydes (not essential to programme).

Diamine(chemical):
- Has the same indespensible attributes of the chemical parent class.
- Contains additional information on diamines (not essential to programme).

Monoamine(chemical):
- Has the same indespensible attributes of the chemical parent class.
- Contains additional information on dialdehydes (not essential to programme).

Monoaldehdye(chemical):
- Has the same indespensible attributes of the chemical parent class.
- Contains additional information on dialdehydes (not essential to programme).

WholeChemicalSpace:
- Contains all the chemicals the chemspeed platform is capable of handling.
- These chemicals each have a unique ID (makes their identification simple).

SubsetChemicalSpace:
- Is a subset of the wholeChemicalSpace. Chemicals that should not be used for generating combinations are not included in this space. 
- Allows for the division of the subsetspace into the different chemical subclasses (for this project the chemcial subclasses are diamines, monoaldehdyes and metals).


Reaction:
- Stores information on the combinations (the regents in a combination), the concentation of the reagents, and the volume of the reaction mixture.
- Allows for the calcualtion of volume vector = a row that represents the transfer volumes for each reagent in the whole space to make up the reaction (combination). If the combination (reaction) contains a metal, the volume vector will have a transfer volume for the metal column while the columns of the other reagents are 0.

ReactionSpace:
- Calculates all the combinations between different chemical classes (based on user parameters) and stores these combinations as reaction objects.
- Orders the reagents in the reactions by price (this is required for the next sorting algorthim).
- Orders the reactions based on price and reagents (to minimise the number of reagents a chemist has to measure in a batch).
- Adds a standard reaction to batches (a quick way for the chemist to tell if the batch is good or not).
- Save the reactionspace as a csv (is human readable).

BatchSpace:
- Takes reactions from the reactionspace depending on batchsize.
- Calculates the total volume of all reagents required to make up the reactions. This volume is then used to calcualte the mass needed to make stock solutions.
- Generates a csv of all the reagents in the wholechemicalspace, and the masses required to make the stock solutions for this batch.
- Reads a csv of the masses of reagents a chemist measured out, and calcuates the volume of solvents required to hit a concentraion (defined in workflowParameters). These volumes are then saved as a csv for the chemspeed platform to read.
- The volume vectors of the reactions in the batch are saved as a csv for the chemspeed platform to read.

"""


import pickle
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
import math
import json
import copy
import importlib.util
import sys
try:
    import win32com.client    #pip install pywin32   (does not work for mac, hence try and except)
except:
    pass

class USERSELECTION():
    """A class to store user defined variables in one location."""
    
    #Chemical Space definition.
    
    chemicalsInWholeSpace = None
    chemicalsToRemove = None

    #Safety checks to preform during workflow.

    safetyChecks = None

    #Paths of various CSVs and JSONs.
    
    rawCWD = None
    strCWD = None
    generatedCsvPath =  None
    generatedPicklePath = None
    genreatedJsonPath = None
    generatedMsCsvPath = None
    logsPath = None 

    #Concentrations used in experiment.
    
    metalConcentration = None                                                                                               
    dialdehdyeConcentration = None
    diamineConcentration = None 
    monoaldehdyeConcentration = None

    #Volumes used in workflow.

    minTransferVolume = None
    bufferVolume = None
    mosuquitoSampleVolume = None
    nmrSampleVolume = None
    msSampleVolume = None
    reactionVolume = None

    reactionVolumeTransferVolumeRatio = None
    reactionVialTransferVolume = None

    #Information on Batch and sample parameters.

    subTypeInReactionTuple = None
    batchSize = None
    standardReactionIdx = None

    #NMR and LCMS Experiment parameters.
    
    parameters = None
    numScans = None
    ppThershold = None
    fieldPresat = None
    solvent = None
    msInjectionVolume = None

    #Email Addresses.
    
    emailPrinter = None
    emailGunther = None

    @staticmethod
    def udpateParameters(location):
        """Changes the class atributes to the variabels defined in the location folder (workflowParameters.py)"""
        
        #Dynamicaly importing a module in python based on user defined path.
        spec = importlib.util.spec_from_file_location('userParameters', location)                                                       #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
        userParameters = importlib.util.module_from_spec(spec)
        sys.modules['userParameters'] =  userParameters
        spec.loader.exec_module(userParameters)
        
        #paths of various CSVs and JSONs.
    
        USERSELECTION.rawCWD = userParameters.rawCWD
        USERSELECTION.strCWD = userParameters.strCWD
        USERSELECTION.generatedCsvPath =  userParameters.generatedCsvPath
        USERSELECTION.generatedPicklePath = userParameters.generatedPicklePath
        USERSELECTION.generatedJsonPath = userParameters.generatedJsonPath
        USERSELECTION.generatedMsCsvPath = userParameters.generatedMsCsvPath
        USERSELECTION.logsPath = userParameters.logsPath

        #Concentrations used in experiment.
        
        USERSELECTION.metalConcentration = userParameters.metalConcentration
        USERSELECTION.dialdehdyeConcentration = userParameters.dialdehdyeConcentration
        USERSELECTION.diamineConcentration = userParameters.diamineConcentration
        USERSELECTION.monoaldehdyeConcentration = userParameters.monoaldehdyeConcentration

        #Volumes used in workflow.

        USERSELECTION.minTransferVolume = userParameters.minTransferVolume
        USERSELECTION.bufferVolume = userParameters.bufferVolume
        USERSELECTION.mosquitoSampleVolume = userParameters.mosquitoSampleVolume
        USERSELECTION.nmrSampleVolume = userParameters.nmrSampleVolume
        USERSELECTION.msSampleVolume = userParameters.msSampleVolume
        USERSELECTION.reactionVolume = userParameters.reactionVolume

        USERSELECTION.reactionVolumeTransferVolumeRatio = userParameters.reactionVolumeTransferVolumeRatio
        USERSELECTION.reactionVialTransferVolume = userParameters.reactionVialTransferVolume

        #Information on Batch and sample parameters.

        USERSELECTION.subTypeInReactionTuple = userParameters.subTypeInReactionTuple
        USERSELECTION.batchSize = userParameters.batchSize
        USERSELECTION.standardReactionIdx = userParameters.standardReactionIdx

        #NMR and LCMS Experiment parameters.
        
        USERSELECTION.parameters = userParameters.parameters
        USERSELECTION.numScans = userParameters.numScans
        USERSELECTION.ppThershold = userParameters.ppThershold
        USERSELECTION.fieldPresat = userParameters.fieldPresat
        USERSELECTION.solvent = userParameters.solvent
        USERSELECTION.msInjectionVolume = userParameters.msInjectionVolume

        #Email Addresses.
        
        USERSELECTION.emailPrinter = userParameters.emailPrinter
        USERSELECTION.emailGunther = userParameters.emailGunther

        #Chemical Space definition.
    
        USERSELECTION.chemicalsInWholeSpace = userParameters.chemicalsInWholeSpace
        USERSELECTION.chemicalsToRemove = userParameters.chemicalsToRemove

        #Safety checks to preform during workflow.

        USERSELECTION.safetyChecks = userParameters.safetyChecks
        
def sendDocumentToEmail(documentPath: list, emailAdress:str, emailSubject: str, successMessage: str, failedMessage: str):
    """Sends a document (defined by a path) to an email."""
    try:
        ol = win32com.client.Dispatch('Outlook.Application')                                                                            #Sending emial via outlook.
        olmailitem=0x0
        newmail = ol.CreateItem(olmailitem)
        newmail.Subject = emailSubject
        newmail.To = emailAdress
        for document in documentPath:
            newmail.Attachments.Add(document)
        newmail.Display()
        newmail.Send()
        print(successMessage)
    
    except Exception as e:                                                                                                              #Sending email in an automated fashion is not 100% reliable.
        print(e)
        print(failedMessage)
        pass

class Chemical():
    """Parent chemical class with data relavent to all chemicals which are relevant to the workflow."""
    
    chemicalId = 1                                                                                                                      #This is allows the chemist to quickly identify reagents in different stages of the workflow.

    def __init__(self, name: str, CAS:str, molecularWeight:int, solubility:tuple, price:float, volumeInReactionVial:float, concentrationInStockVial:float, newChemical:bool) -> None:
        self.name = name                                                                                                                #name of the reagent. 
        self.CAS = CAS                                                                                                                  #CAS number as shown in the reagent vial. 
        self.molecularWeight = molecularWeight                                                                                          #Molecular weight in grams per mole.
        self.solubility = solubility                                                                                                    #Solubility in CCl2H2:CH3CN (as a ratio in a tuple).
        self.price = price                                                                                                              #The price of the chemical per gram.
        self.volumeInReactionVial = volumeInReactionVial                                                                                #The volume in microlitre that Gunther dispenses into the reaction vials, along side concentration, it is representative of the stoichiometries (i.e. allows you to put reagents in excess).
        self.concentrationInStockVial = concentrationInStockVial                                                                        #The concentration in mM of the chemical in the stock solution. For metals with multiple coordiantion numbers, this is the concentration for the metal at a theoreitcal coordination number of 6 (the script adjusts the concentration based on the metals true coordination number later on).
        self.ID = Chemical.chemicalId                                                                                                   #This is the ID of the chemical.
        if newChemical:
            Chemical.chemicalId += 1                                                                                                    #Updating the chemical id after a new chemical has been instantiated.

    def __repr__(self) -> str:
        return self.name

class Metal(Chemical):
    """These are all chemicals which are metals."""
    
    def __init__(self, name: str, CAS: str, molecularWeight: int, solubility: tuple, price: float, volumeInReactionVial: float, concentrationInStockVial: float, newChemical:bool, noCoordinationSites: tuple, selectedCoordinationNum:int = None) -> None:
        super().__init__(name, CAS, molecularWeight, solubility, price, volumeInReactionVial, concentrationInStockVial, newChemical)
        
        self.noCoordinationSites = noCoordinationSites                                                                                  #This is a tuple with the number of coordination site a metal has (may have) (i.e. silver = 8,7,6). When calulating combinations between chemicals, a metal with two different coordination numbers is considerd as two 'different' metals.
        self.selectedCoordinationNum = selectedCoordinationNum                                                                          #This is the coordination number of the metal assumed in a specific reaction (i.e. the coordination used to calculate the stoichiometry of the metal in the smaple).
        if self.selectedCoordinationNum != None:
            self.volumeInReactionVial = self.volumeInReactionVial*(6/self.selectedCoordinationNum)                                      #[previous metal volume] * (6/ New coor num) :this is the ratio required to for a metal to react with the same (constant) volume of iminie reagent (with a change in coordination number).
        
    def select_coor_num(self, coor_num:int):
        """Changing the coordination number of the metal in an experiment."""
        
        self.selectedCoordinationNum = coor_num

class Dialdehyde(Chemical):
    """These are all chemicals which are dialdehydes."""
    
    def __init__(self, name: str, CAS: str, molecularWeight: int, solubility: tuple, price: float, volumeInReactionVial: float, concentrationInStockVial: float, newChemical:bool, noCoordinationSites:int, noImineReactionSites: int) -> None:
        super().__init__(name, CAS, molecularWeight, solubility, price, volumeInReactionVial, concentrationInStockVial, newChemical)
        
        self.noCoordinationSites = noCoordinationSites                                                                                  #The number of chelating agents in the molecule.
        self.noImineReactionSites = noImineReactionSites                                                                                #The number of site that react to form an imine.
    
class Diamine(Chemical):
    """These are all chemicals which are diamines."""

    def __init__(self, name: str, CAS: str, molecularWeight: int, solubility: tuple, price: float, volumeInReactionVial: float, concentrationInStockVial: float, newChemical:bool, noCoordinationSites:int, noImineReactionSites: int) -> None:
        super().__init__(name, CAS, molecularWeight, solubility, price, volumeInReactionVial, concentrationInStockVial, newChemical)
    
        self.noCoordinationSites = noCoordinationSites                                                                                  #The number of chelating agents in the molecule.
        self.noImineReactionSites = noImineReactionSites                                                                                #The number of site that react to form an imine.
    
class Monoamine(Chemical):
    """These are all chemicals which are monoamines."""
    def __init__(self, name: str, CAS: str, molecularWeight: int, solubility: tuple, price: float, volumeInReactionVial: float, concentrationInStockVial: float, newChemical, noCoordinationSites:int, noImineReactionSites: int) -> None:
        super().__init__(name, CAS, molecularWeight, solubility, price, volumeInReactionVial, concentrationInStockVial, newChemical)
    
        self.noCoordinationSites = noCoordinationSites                                                                                  #The number of chelating agents in the molecule.
        self.noImineReactionSites = noImineReactionSites                                                                                #The number of site that react to form an imine.
    
class Monoaldehdye(Chemical):
    """These are all chemicals which are monoaldehydes."""
    def __init__(self, name: str, CAS: str, molecularWeight: int, solubility: tuple, price: float, volumeInReactionVial: float, concentrationInStockVial: float, newChemical:bool, noCoordinationSites:int, noImineReactionSites: int) -> None:
        super().__init__(name, CAS, molecularWeight, solubility, price, volumeInReactionVial, concentrationInStockVial, newChemical)
    
        self.noCoordinationSites = noCoordinationSites                                                                                  #The number of chelating agents in the molecule.
        self.noImineReactionSites = noImineReactionSites                                                                                #The number of site that react to form an imine.
    
class WholeChemicalSpace():
    """A chemical space defined as variables in the chemspeed platform. Hence chemcials, the platform can physicaly maneuver. These are not neccesary reagents the chemist is interested in (used for generating combinations)."""
   
    def __init__(self, chemical_objects:list) -> None:
        self.space = chemical_objects                                                                                                   #A list of chemicals (as chemical objects) that gunther is able to manipulate (this is limited by the chemspeed script).
    
    def showChemicalSpace(self):
        """Prints out the list of chemicals in the space."""
        
        print(self.space)
    
    def showChemicalSpaceSize(self):
        """Prints out the size of the wholeChemicalSpace (the physical chemspeed platform limits this to 48)."""
        
        print(len(self.space))

    def saveToPickle(self):
        """Saves the whole chemical space to a pickle file."""

        path = USERSELECTION.generatedPicklePath+'WholeChemicalSpace.pickle'
        file = open(path, 'wb')
        pickle.dump(self, file)
        file.close()

class SubsetChemicalSpace():
    """A the chemical space which we wish the ML to study (i.e. the chemicals we want to generate combinations with)."""
    
    def __init__(self, WholeChemicalSpace:WholeChemicalSpace) -> None:
        self.space = WholeChemicalSpace.space.copy()                                                                                    #A list of the chemical space (as above). Irrelavent whemicals in the whole space will be removed to create the subspace.
        self.dividedSpace = {}                                                                                                          #This is a dictionary with the chemical subtype as a key and the list of chemicals of this subtype as the value (divides the space based on chemical subtype).
    
    def removeChemicalsFromSpace(self, chemicals:list):
        """Removes any unwanted chemicals from the whole chemicals space, tranforming it to the subsetspace. Unwated chemicals do are not used to generate combinations."""
        
        for chemicalToRemove in chemicals:                                                                                              #Iterating through chemcials to remove. These are defined in workflowParameters.py
            for wholeChemical in self.space:
                if chemicalToRemove.name == wholeChemical.name:
                    self.space.remove(wholeChemical)
    
    def showChemicalSpace(self):
        """Prints out the list of chemicals in the SubsetChemicalSpace."""
        
        print(self.space)
    
    def showChemicalSpaceSize(self):
        """Prints out the size of the SubsetChemicalSpace."""
        
        print(len(self.space))
    
    def divideSpaceBySubtype(self):
        """Divides the chemical space into the different chemical subtypes and saves them as a dictionary."""
        
        #sadly this implementation sucks as its not dynamic. If the user changes the daughter classes, this section must be changed to.
        
        for chemical in self.space:
            chemicalSubtype = chemical.__class__.__name__ 
            if chemicalSubtype not in self.dividedSpace.keys() and chemicalSubtype != 'Metal':                                          #Adds the initial instance of a chemical subtype to a key (if its not a metal).
                self.dividedSpace[f'{chemicalSubtype}'] = [chemical]
            
            elif chemicalSubtype in self.dividedSpace.keys() and chemicalSubtype != 'Metal':                                            #If subtype key already exists in the dictionary add this chemical to that subset.
                self.dividedSpace[f'{chemicalSubtype}'].append(chemical)

            if chemicalSubtype not in self.dividedSpace.keys() and chemicalSubtype == 'Metal':                                          #As before if subset is not created then create it, however with metals, each different coordination number is seen as a 'unique metal' (this will make combination calculations for reactions with same metal but different coordination number more easy).
                self.dividedSpace[f'{chemicalSubtype}'] = []
                if type(chemical.noCoordinationSites) == int:                                                                           #Checking that if the noCoordinationSites is interpreted as an integer or tuple by python (the coordination number can be either represented as an integert or tuple in the metal class).
                    coordinationNumber =chemical.noCoordinationSites                                             
                    newChemical = Metal(name=chemical.name, CAS=chemical.CAS, molecularWeight=chemical.molecularWeight, solubility=chemical.solubility, price=chemical.price, volumeInReactionVial=chemical.volumeInReactionVial, concentrationInStockVial= chemical.concentrationInStockVial, noCoordinationSites=chemical.noCoordinationSites, selectedCoordinationNum=coordinationNumber, newChemical=False)
                    newChemical.ID = chemical.ID                                                                                        #Making sure that the same checmical have the same chemical.ID, as they are the same reagents.
                    self.dividedSpace[f'{chemicalSubtype}'].append(newChemical)                                                         #Adding the generated newly generated metal (based on metals coordination number).
                
                elif type(chemical.noCoordinationSites) == tuple:
                    for coordinationNumber in chemical.noCoordinationSites:
                        newChemical = Metal(name=chemical.name, CAS=chemical.CAS, molecularWeight=chemical.molecularWeight, solubility=chemical.solubility, price=chemical.price, volumeInReactionVial=chemical.volumeInReactionVial, concentrationInStockVial= chemical.concentrationInStockVial, noCoordinationSites=chemical.noCoordinationSites, selectedCoordinationNum=coordinationNumber, newChemical=False)
                        newChemical.ID = chemical.ID                                                                                     #Making sure that the same metals (regardless of coordination number) have the same chemical.ID.
                        self.dividedSpace[f'{chemicalSubtype}'].append(newChemical)
                
                else:
                    print(f'Check {chemical.name}\'s noCoordinationSites variable')                                                     #Tells user if there is an error with the segregation of metals based on coordination numbers.
                    break

            elif chemicalSubtype in self.dividedSpace.keys() and chemicalSubtype == 'Metal':                                            #If metal subtypekey already exists add chemical to this subset.
                if type(chemical.noCoordinationSites) == int:                                                                           #Checking that if the tuple is interpreted as an integer or tuple by python (as stated before, the coordination number can be either represented as an integert or tuple in the metal class).
                    coordinationNumber = chemical.noCoordinationSites                                             
                    newChemical = Metal(name=chemical.name, CAS=chemical.CAS, molecularWeight=chemical.molecularWeight, solubility=chemical.solubility, price=chemical.price, volumeInReactionVial=chemical.volumeInReactionVial, concentrationInStockVial= chemical.concentrationInStockVial, noCoordinationSites=chemical.noCoordinationSites, selectedCoordinationNum=coordinationNumber, newChemical=False)
                    newChemical.ID = chemical.ID                                                                                        #Making sure that the same checmical have the same chemical.ID.
                    self.dividedSpace[f'{chemicalSubtype}'].append(newChemical)
                
                elif type(chemical.noCoordinationSites) == tuple:
                    for coordinationNumber in chemical.noCoordinationSites:
                        newChemical = Metal(name=chemical.name, CAS=chemical.CAS, molecularWeight=chemical.molecularWeight, solubility=chemical.solubility, price=chemical.price, volumeInReactionVial=chemical.volumeInReactionVial, concentrationInStockVial= chemical.concentrationInStockVial, noCoordinationSites=chemical.noCoordinationSites, selectedCoordinationNum=coordinationNumber, newChemical=False)
                        newChemical.ID = chemical.ID                                                                                    #Making sure that the same checmical have the same chemical.ID.
                        self.dividedSpace[f'{chemicalSubtype}'].append(newChemical)                                                                 
                
                else:
                    print(f'Check {chemical.name}\'s noCoordinationSites variable')                                                     #Tells user if there is an error with the segregation of metals based on coordination numbers.
                    break
            
class Reaction():
    """Stores information of individual reactions (which are based on the generated combinations)."""
    
    reactionGenerated = 1                                                                                                               #Keeps track of the number of chemical reactions generated. This is the reaciton ID.

    def __init__(self, finalReactionVolume:float, reagents:list, wholeSpace:WholeChemicalSpace=None) -> None:
        if wholeSpace != None:                                                                                                          #The basis chemical are just all the reagents in the whole space. These are required to make any generated csv compatible with the chemspeed platform.
            self.basisChemicals = wholeSpace.space
        else:
            self.basisChemicals = None
        
        self.finalReactionVolume = finalReactionVolume                                                                                  #The volume of the reaction sample in the reagent vial (the vial will be topped up with CH3CN). This is a taken from workflorParameters.py.
        self.reagents = reagents                                                                                                        #A list of the reagents in the reaction (does not include solvents).
        self.volumeOfReagentsRequired = []                                                                                              #A list of all chemicals in wholechemicalSpace (basisChemicals) and their volumes required to make this reaction mixture. If a reagent in the basisChemical is not present in the reaction it is assigned a volume of 0.
        self.reagentsVolume = 0                                                                                                         #Keeps track of the total reagent volume (to calculate the volume of solvent to top up the vial with).
        self.unique_identifier = self.reactionGenerated                                                                                 #The uniqe identifier of the reaction is just its generated sequencial number. 
        Reaction.reactionGenerated += 1                                                                                                 #Updating the reaction count with reaction instantiation.

    def _getVolumesVector(self):
        """Gets a vector of the volumes of the reagents present in a reaction, with chemicals in the whole chemicals space as basis."""
        
        for basisChemical in self.basisChemicals:                                                                                       #Iterating through the various basis chemicals (reagents in the whole chemical space) and reagents in the reaction. Compares them, if they are the same, the reagent volume to transfer is added to the vector, if different a volume of 0 is assigned.
            basisChemicalsFound = False
            for reagent in self.reagents:
                if basisChemical.name == reagent.name and reagent.concentrationInStockVial != 0:
                    self.volumeOfReagentsRequired.append(reagent.volumeInReactionVial)                                                  #Adding the transfer volume to the volume of reagents required.
                    self.reagentsVolume += reagent.volumeInReactionVial                                                                 #Adding the found volume to the total reagent volume.
                    basisChemicalsFound = True
            if basisChemicalsFound == False:
                self.volumeOfReagentsRequired.append(0)
            else:
                basisChemicalsFound = False
        
        self.volumeOfReagentsRequired.append(self.finalReactionVolume-self.reagentsVolume)                                              #The volume of CH3CN need to top up to the final volume.   

    def __repr__(self) -> str:
        return str(self.unique_identifier)

class ReactionSpace():
    """A space that contains all the combinations as reactions. Combinations are calculated based on the reagents in the SubsetChemicalSpace."""
    
    def __init__(self, subsetSpace:SubsetChemicalSpace, wholeSpace:WholeChemicalSpace) -> None:
        self.subsetSpace = subsetSpace                                                                                                  #This is the subset chemical space. The divided space will be usefull in the combination calculation.
        self.wholeSpace = wholeSpace                                                                                                    #This is the whole space, it is used for calcualting reagent volumes, and as a basis chemicals (compatibility between python and chemspeed scripts).
        self.reactionSpace = []                                                                                                         #A list that stores different chemical combinations as reaction objects.
        self.currentReactionSpace = None                                                                                                #A duplicate of the reaction space. Reactions that have been carried out will be deleted form this list.
        self.reagentSpace = []                                                                                                          #A list that stores different chemcial reactions as their reagent list (combinations).

    def showSubtypesIndex(self):
        """Shows the chemical subtype and the index for calculating combinations."""
        
        for idx, subtype in enumerate(self.subsetSpace.dividedSpace):                                                                   #Iterates through the divided subsetspace and prints out the name of the chemical subset.
            print(idx, subtype)

    def duplicateSpace(self):
        """Duplicates reactionSpace to keep track of reactions that have been taken and which still need to be taken."""

        self.currentReactionSpace = self.reactionSpace

    def calcSubTypeCombinations(self, noSubtypeInReaction:tuple):
        """Gets the combination of reagents depending on the amount per chemical subtype in a reaction (based on the inputed tuple) and returns a list of these combinations (with reagent in reaction)."""
        
        combinationList = []
        combinationSpace = []

        for keyIndex, chemicalSubtype in enumerate(self.subsetSpace.dividedSpace):                                                      #Iterating through the chemical subtypes        
            for i in range(0, noSubtypeInReaction[keyIndex]):                                                                           #Iterating through the number of times a subtype appears in a reaction (as selected by the tuple argument).
                combinationList.append(self.subsetSpace.dividedSpace[f'{chemicalSubtype}'])
        
        for subtypeList in combinationList:                                                                                             #Iterating through chemical subtypes and merging their combinations each time. This calcualtes the possible combinations between all checmial subtypes.
            combinationSpace = self._addCombination(combinationSpace, subtypeList)

        self.reagentSpace += combinationSpace                                                                                           #Adding the computed combination space to the reaction space.

    def calcImineCombinations(self):
        """Calculates the possible combination of imines."""
        
        #This combination is not used in this project. However, it highlights that multiple combinations can be added to the reaction space. It is also why the sorting algorithm is applied post combination generation.
        amineList = []                                                                                                                  #Current limitation of this imine combination is that more complex imines (i.e. Adamantane-1,3-diamine + 5-Methylpicolinaldehyde + 2-Quinolinecarboxaldehyde) are not possible.
        aldehydeList = []
        combinationList = [amineList, aldehydeList]
        imineSpace = []
        for keyIndex, chemicalSubtype in enumerate(self.subsetSpace.dividedSpace):
            if chemicalSubtype == 'Diamine' or chemicalSubtype == 'Monoamine':
                amineList += self.subsetSpace.dividedSpace[f'{chemicalSubtype}']
            
            elif chemicalSubtype == 'Dialdehyde' or chemicalSubtype == 'Monoaldehdye':
                aldehydeList += self.subsetSpace.dividedSpace[f'{chemicalSubtype}']
        
        for subtypeList in combinationList:                                                                                             #Iterating through amine and aldehdye chemicals and merging their combinations each time.
            imineSpace = self._addCombination(imineSpace, subtypeList)
        
        self.reagentSpace += imineSpace                                                                                                 #Adding the calcualted imine combinations into the reaction space.
    
    def orderChemicalPrices(self):
          """Orders the chemicals in the nested lists (reagents list) based on their price (most cheap to most expensive)."""
          
          #ordering reagents by price is required for orderReactionPrices().
          reaction_list = self.reagentSpace
          numeration = len(reaction_list)
          for i in range(numeration):                                                                                                   #Iterating through all the reactions and calling _orderChemicals() -> this method orders the reagents.
               reaction_list[i] = ReactionSpace._orderChemicals(reaction_list[i])           
    
    def orderReactionPrices(self):
          """Orders the reactions based on their prices (form cheapest to most expensive)."""
          
          listToSort = self.reagentSpace
          self.reagentSpace = ReactionSpace.multiListSort(listToSort)                                                                  #multiListSort() method is responsible for the actual sorting.

    def generateReactionSpace(self):
        """Fills in the empty reaction space with reaction python objects based on list combinaitons (items in self.reagentSpace)."""
        
        for reagentCombination in self.reagentSpace:
            reaction = Reaction(finalReactionVolume=USERSELECTION.reactionVolume, reagents=reagentCombination, wholeSpace=self.wholeSpace)
            reaction._getVolumesVector()                                                                                               #For each reaction, calculate volumes required to make the appropiate combination.
            self.reactionSpace.append(reaction)
    
    def showChemicalSpace(self):
        """Prints out the list of chemicals in the space."""
        
        print(self.reagentSpace)
    
    def getSpaceSize(self):
        """Returns the size of the reaction space."""
        
        return(len(self.reactionSpace))

    def showChemicalSpaceSize(self):
        """Prints out the size of the space."""
        
        print(len(self.reagentSpace))

    def saveToPickle(self):
        """Saves the reaction space oject as a pickle."""
        
        path = USERSELECTION.generatedPicklePath+'ReactionSpace.pickle'
        file = open(path, 'wb')
        pickle.dump(self, file)
        file.close()
    
    def saveToCsv(self):
        """Save the reaction space to a csv, including unique identifiers."""
        
        DictionaryToConvert = {}
        columnNames = ['Unique Identifier']+['Reaction'] + [reagent.name for reagent in self.wholeSpace.space] + ['CH3CN']             #columns are: reaction name + reagents + solvents (order is of utmost importance)
        path = USERSELECTION.generatedCsvPath + 'reactionSpace.csv'
        
        for reactionIdx, reaction in enumerate(self.reactionSpace):                                                                    #Iterating through reactions and adding their appropiate information into the dictionary. 
            DictionaryToConvert[f'{reactionIdx}'] = [reaction.unique_identifier]+[str(reaction.reagents)]+reaction.volumeOfReagentsRequired
        
        df = pd.DataFrame.from_dict(DictionaryToConvert, orient='index', columns=columnNames)                                          #Saving the dinctionary as a csv.
        df.to_csv(path, index=False)
    
    @staticmethod
    def _addCombination(list1:list, list2:list):
        """Takes in two reagent lists and returns all their possible combinations."""
        
        combinationList = []                                                                                                           #List to return.
        
        if len(list1) == 0 or len(list2) == 0:                                                                                         #If either list is empty the combination list is just the filled list. 
                combinationList = list1 + list2
        else:
            for chemical2 in list2:                                                                                                    #Enumerating through all list items.
                for chemical1 in list1:
                    if type(chemical1) == list and type(chemical2) == list:                                                            #A conditional so that the appended items will allways result in the form [reagent_1, reagent_2]. Prevents post combination cleanup.
                        combinationList.append(chemical1 + chemical2)
                    
                    elif type(chemical1) == list and type(chemical2) != list:
                        combinationList.append(chemical1 + [chemical2])
                    
                    elif type(chemical1) != list and type(chemical2) == list:
                        combinationList.append([chemical1] + chemical2)
                        
                    else:
                        combinationList.append([chemical1,chemical2])
        
        return combinationList
        
    def _orderChemicals(reaction):
          """Orders chemicals in a reaction from the most expensive to the least expensive."""
          
          #bubble sort algorithm taken from https://www.geeksforgeeks.org/bubble-sort/
          #I recommend learning vanilla bubble sort before looking at my code (they are pretty much exactly the same, just values change).
          
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
    
    def multiListSort(listToSort):
        """Sorts a list based on the chemical prices inside the nested list (this algorthim is resposible for sorting reactions)."""
        
        sortedList = []
        
        for reaction in listToSort:
            largestFound = 0
            for sortedReactionIdx, sortedReaction in enumerate(sortedList):
                if len(sortedList) == 0:
                        sortedList.append(reaction)
                
                #Iterating through the two reagents in the reaction untill a difference is found.
                
                price_idx = 0
                while reaction[price_idx].price*reaction[price_idx].volumeInReactionVial == sortedReaction[price_idx].price*sortedReaction[price_idx].volumeInReactionVial and min(len(reaction), len(sortedReaction))-1 > price_idx:
                    price_idx +=1
                
                #Conditions and consequences to take once difference is found:
                
                #If reactions are the exact same. 
                if reaction == sortedReaction:
                    largestFound += 1
                
                #If reactions are the same but one has additional chemicals.
                elif len(reaction) > len(sortedReaction) and reaction[price_idx].price*reaction[price_idx].volumeInReactionVial == sortedReaction[price_idx].price*sortedReaction[price_idx].volumeInReactionVial:
                    largestFound += 1
                
                #If the reactions prices are not the same and have the number of reagents.
                elif len(reaction) == len(sortedReaction) and reaction[price_idx].price*reaction[price_idx].volumeInReactionVial > sortedReaction[price_idx].price*sortedReaction[price_idx].volumeInReactionVial:
                    largestFound += 1
                
                #If reactions are not the same and have different string lengths.
                elif len(reaction) > len(sortedReaction) and reaction[price_idx].price*reaction[price_idx].volumeInReactionVial > sortedReaction[price_idx].price*sortedReaction[price_idx].volumeInReactionVial:
                    largestFound += 1
                
                #If reactions are not the same and have different string lengths.
                elif len(reaction) < len(sortedReaction) and reaction[price_idx].price*reaction[price_idx].volumeInReactionVial > sortedReaction[price_idx].price*sortedReaction[price_idx].volumeInReactionVial:
                        largestFound += 1
            
            sortedList.insert(largestFound, reaction)
            largestFound = 0
        return sortedList

class SampleSpace():
    """A space responsible for the manipulation of samples."""

    def __init__(self) -> None:
        self.ReactionSpace = None                                                                   #This is the Reaction space class
        self.currentReactionSpace = None                                                            #This is the list of reaction that still have to be taken.
        self.takenSamplesSpace = []                                                                 #This is the samples that have been taken. This is to be queried if a batch has failed.
        self.sampleSpace = []                                                                       #This is the curent reaction space divided into batches.
        self.batchSize = None                                                                       #This is the number of samples in a batch.
        self.standardReactionIdx = None                                                             #This is the index of the standard reaction
        self.standardReactionNumber = 0                                                             #This keeps track of the number of standard reactions added.
    
    def importReactionSpace(self):
        """Imports the reaction space after initiation."""
        
        path = USERSELECTION.generatedPicklePath+'ReactionSpace.pickle'
        file = open(path, 'rb')
        self.ReactionSpace = pickle.load(file)
        file.close()

    def batchCheck(self):
        """Checks if its possible to get the next batch."""
        try:
            self.sampleSpace[0] 
            return True
        except:
            return False

    def duplicatereactionSpace(self):
        """Duplicates reaction space for mutability reasons."""

        self.currentReactionSpace = self.ReactionSpace.reactionSpace.copy()

    def generateSampleSpace(self, batchSize:int):
        """Takes the current reaction space and generates the sample space. The sample space is in the form of [[batch0], [batch1], [batchx]]"""
        
        self.batchSize = batchSize

        currentReactionSpaceSize = len(self.currentReactionSpace)                                                                          #gets the size of the current reaction space.
        noItterations = math.ceil(currentReactionSpaceSize/(self.batchSize-1))-1
        
        #Reseting the sample space.

        self.sampleSpace.clear()
        
        #Dividing the current reaction space into batches

        for iteration in range(noItterations+1):
            self.sampleSpace.append(self.currentReactionSpace[iteration*(self.batchSize-1):(iteration+1)*(self.batchSize-1)])  

    def generateStandardReaction(self):
        """Creates a standard reaction and retuns it"""  
        #Getting the attributes of the standard reaction.
        
        standardReaction = self.ReactionSpace.reactionSpace[self.standardReactionIdx]                                                                                  #Retrieving the standard reaction. Along with its attributes.
        standardReactionFinalVolume = standardReaction.finalReactionVolume
        standardReactionReagents = standardReaction.reagents
        standardReactionBasisChemicals = standardReaction.basisChemicals
        standardReactionReagentsVolume = standardReaction.reagentsVolume
        standardReactionVolumeOfReagentsRequired = standardReaction.volumeOfReagentsRequired

        #Creating a new reaction with the same attributes as the standard reaction
        
        reaction = Reaction(finalReactionVolume=standardReactionFinalVolume, reagents=standardReactionReagents)
        reaction.basisChemicals = standardReactionBasisChemicals
        reaction.finalReactionVolume = standardReactionFinalVolume
        reaction.reagents = standardReactionReagents
        reaction.volumeOfReagentsRequired = standardReactionVolumeOfReagentsRequired
        reaction.reagentsVolume = standardReactionReagentsVolume
        reaction.unique_identifier = str(self.standardReactionIdx)+'batch'+str(self.standardReactionNumber)

        self.standardReactionNumber += 1

        return reaction

    def addStandardReactionIdx(self, standardReactionIdx):
        """Updates the standard reaction index of to add in batch samples."""
        self.standardReactionIdx = standardReactionIdx

    def getBatchSamples(self):
        """Gets the reactions for the batch (depends on the batch number)."""
        
        standardReaction = self.generateStandardReaction()

        currentSamples = [standardReaction] + self.sampleSpace[0]
        
        #Removing the taken samples from the sample space and current reactions.
        self.sampleSpace = self.sampleSpace[1:]
        for sample in currentSamples:
            self.currentReactionSpace = self.currentReactionSpace[1:]

        #Returning the required batch samples while keeping track of them.
        self.takenSamplesSpace.append(currentSamples)
        return currentSamples
    
    def retakeBatches(self, batches:list):
        """Takes in batch numbers, reads them to reactions to take."""

        for batchNumber in batches:
            #taking the batch samples.
            batch = self.takenSamplesSpace[batchNumber]
            reactions = batch[1:]

            #Updating the current reaction space.
            for reaction in reactions:
                self.currentReactionSpace.append(reaction)

        #Updating the sample space.
        self.generateSampleSpace(self.batchSize)
        print(self.sampleSpace)

    def retakeReactions(self, reactionIDXs:str):
        """Takes in reaction indexs, adds them back to the reactions to take."""

        #appending the current reaction space based on reaction indexes.
        for reactionIDX in reactionIDXs:
            reaction = self.ReactionSpace.reactionSpace[reactionIDX-1]
            self.currentReactionSpace.append(reaction)
        
        #Updating the sample space.
        self.generateSampleSpace(self.batchSize)

        print(self.sampleSpace)


    def saveToPickle(self):
        """Saves the batch space to a pickle file."""
        
        path = USERSELECTION.generatedPicklePath+'SampleSpace.pickle'
        file = open(path, 'wb')
        pickle.dump(self, file)
        file.close()


class BatchSpace():
    """A space with the reactions to carry out."""
    
    def __init__(self, batchSize:int) -> None:
        self.batchSize = batchSize
        self.batchNumber = -1                                                                                                          #This is the current batch number. Instantiated at 1, as the first time the takeNewBatch() function is called in main, it adds 1 to the batchNumber
        self.stockSpaceGenerated = False                                                                                               #A flag to ensure sample spaces are only generated after the stock space.
        self.sampleSpaceGenerated = False                                                                                              #A flag to ensure stock sapaces are only taken after samples spaces are generated.
        self.WholeChemicalSpace = None                                                                                                 #This is the whole chemical space.
        self.stockSpace = None                                                                                                         #This is the stockspace. It handles the formation of stock solutions. 
        self.SampleSpace = None                                                                                                        #Imports the Samplespace object.
        self.batchSpace = None                                                                                                         #This is the samples in the batch.
        self.stockMassVector = []                                                                                                      #This is a list contaning the mass of each chemical in the wholechemicalspace needed to make stock solutions (reagents not in present in the batch space get a mass of 0).
        self.AcetonitrileVolumeVector = []                                                                                             #The volume (in microlitres) of CH3CN required for each chemical in the whole chemical space (chemicals not in the batch space are get a volume of 0).
        self.DichloromethaneVolumeVector = []                                                                                          #The volume (in microlitres) of CH2Cl2 required for each chemical in the whole chemical space (chemicals not in the batch space are get a volume of 0).
        self.finalBatchNumber = None

    def setSampleFlagToTrue(self):
        """If the samplespace has been taken it sets True."""
        
        self.sampleSpaceGenerated = True
    
    def setSampleFlagToFalse(self):
        """If the samplespace has been taken it sets False."""
        
        self.sampleSpaceGenerated = False

    def setStockFlagToTrue(self):
        """If the batch has been taken it sets True."""
        
        self.stockSpaceGenerated = True
    
    def setStockFlagToFalse(self):
        """If the batch has been taken it sets False."""
        
        self.stockSpaceGenerated = False
    
    def stockSpaceFlag(self):
        """The different requirements that need to be fufilled to generate a StockSpace"""
        
        if self.sampleSpaceGenerated==True or self.batchNumber==-1:
            if not self.SampleSpace.batchCheck():
                print(f'All batches Taken. Either add reactions or batches to retake, or go home and relax.')
            else:
                return True
                
        else:
            print(f'Please run getBatchSpacesCsvs() in main.')
        
    def sampleSpaceFlag(self):
        """The different requirements that need to be fufilled to generate a samplespace"""
        
        if self.stockSpaceGenerated==True:
            if self.SampleSpace.batchCheck():
                return True
            elif not self.SampleSpace.batchCheck():
                return True
        else:
            if not self.SampleSpace.batchCheck():
                pass
            else:
                print('Please run takeNewBatch() in main.')


    def changeBatchNumber(self):
        """Changes the batch number and Final Batch number depending on the batch flag and number of reactions to take."""

        self.batchNumber += 1
        takenBatches = len(self.SampleSpace.takenSamplesSpace)
        batchesToTake = len(self.SampleSpace.sampleSpace)
        self.finalBatchNumber = takenBatches + batchesToTake - 1

        print(f'The current batch running is {self.batchNumber}. The final batch number is {self.finalBatchNumber}. Batches start from 0')
        
    def importSampleSpace(self):
        """Imports the reaction space after initiation."""
        
        path = USERSELECTION.generatedPicklePath+'SampleSpace.pickle'
        file = open(path, 'rb')
        self.SampleSpace = pickle.load(file)
        file.close()

    def importWholeChemicalSpace(self):
        """Imports the whole chemical space after initiation."""
        
        path = USERSELECTION.generatedPicklePath+'WholeChemicalSpace.pickle'
        file = open(path, 'rb')
        self.WholeChemicalSpace = pickle.load(file)
        file.close()

    def getBatchSpace(self):
        """Function gets the batch space from the sample space."""
        
        #Checking if the previous batch has been taken or its the frist batch to take.
        self.batchSpace = self.SampleSpace.getBatchSamples()

    def saveToPickle(self):
        """Saves the batch space to a pickle file."""
        
        path = USERSELECTION.generatedPicklePath+'BatchSpace.pickle'
        file = open(path, 'wb')
        pickle.dump(self, file)
        file.close()

    def saveBatchSpaceToCsv(self):
        """Saves the sample space to a Gunther readable csv."""
        
        DictionaryToConvert = {} 
        columnNames = ['Unique Identifier']+['Reaction']+[reagent.name for reagent in self.WholeChemicalSpace.space] + ['CH3CN']       #columns are: reaction name + reagents + solvents (order of columns is of utmost importance).
        pathCsv = USERSELECTION.generatedCsvPath + 'batchSpace.csv'
        pathLogs = USERSELECTION.logsPath + str(self.batchNumber) + '_batchSpace.csv'
        
        for reactionIdx, reaction in enumerate(self.batchSpace):
            DictionaryToConvert[f'{reactionIdx}'] = [reaction.unique_identifier] + [str(reaction.reagents)] + reaction.volumeOfReagentsRequired
        
        df = pd.DataFrame.from_dict(DictionaryToConvert, columns=columnNames, orient='index')
        df.to_csv(pathCsv, index=False)                                                                                                 #Saving the csv in the generated CSV folder.
        df.to_csv(pathLogs, index=False)                                                                                                #Saving the csv as a log.                                                                                                                       #updates the batch number for next batch use.

    def calcStockMasses(self):
        """Calculates the masses of the chemicals required to make up the reactions in the batch space and appends them to the stock mass vector."""
        
        self.stockMassVector.clear()
        for chemical in self.WholeChemicalSpace.space:                                                                                  #Iterating through the chemicals in the whole chemical sapce and checks their presence in the batch space.
            chemicalVolume = 0
            for reaction in self.batchSpace:                                                                                           #Getting the total volume of a chemical in the batch space.
                for reagent in reaction.reagents:
                    if chemical.name == reagent.name:
                        chemicalVolume += reagent.volumeInReactionVial
            
            if chemicalVolume == 0:
                self.stockMassVector.append(0)
            
            else:
                minTransferVolume = USERSELECTION.minTransferVolume                                                                     #Minimum transfer volume for blue caps (800≈900 microlires) at calibration (0,0,0) for shaker and (0,0,-59) for shaker insert, minimum transfer for white caps (770≈900 microlires) at calibration (0,0,0) for shaker and (0,0, -59) for shaker insert.
                bufferVolume = (chemical.volumeInReactionVial)*2 
                totalVolume = chemicalVolume + bufferVolume + minTransferVolume                                                         #This is the total stock volume required for a specific reagent.
                chemicalMw = chemical.molecularWeight
                chemcialConcentration = chemical.concentrationInStockVial
                chemicalMassRequired = (chemcialConcentration/1000)*(totalVolume/1000000)*chemicalMw                                    #concentration = moles/volume = mass/Mw/volume (mass = concentration*volume*Mw)
                self.stockMassVector.append(chemicalMassRequired)
                chemicalVolume = 0                                                                                                      #At the end of the chemical iteration, add the calculated mass required to the mass vector and reset the chemicalVolume.

    def saveCalcStockMassesToCSv(self):
        
        """Saves the reqiured masses to measure to a human readable csv. These are the massses the chemist as to measure."""
        
        mass_dct = {}                                                                                                                   #An empty dictionary to populate and then read as a pandas dataframe.
        path = USERSELECTION.generatedCsvPath + 'stockSpace.csv'

        mass_dct['chemicalIdx'] = [i+1 for i in range(len(self.WholeChemicalSpace.space))]
        mass_dct['Chemical'] = self.WholeChemicalSpace.space
        mass_dct['Mass to measure (in grams)'] = self.stockMassVector
        mass_dct['Actual mass measured'] = [None if mass !=0 else 0 for mass in self.stockMassVector]                                   #To make it more userfriendly, reagents not present in the batch space are automaticaly assigned 0.

        df = pd.DataFrame.from_dict(mass_dct, orient='columns')                                                                         #Making a pandas dataframe as its more simple to create + save objects as a csv (yes I am that lazy).
        df.to_csv(path, index=False)

    def sendStockSpaceToEmail(self):
        """Sends the generated csv to email to be printed."""
        
        dfPath = USERSELECTION.generatedCsvPath + 'stockSpace.csv'
        df = pd.read_csv(dfPath)

        pdfPath = USERSELECTION.generatedCsvPath + 'stockSpace.pdf'
        
        fig, ax =plt.subplots(figsize=(12,4))                                                                                           #Saving the df as a matplot table, to then save as pdf (code taken from https://stackoverflow.com/questions/33155776/export-pandas-dataframe-into-a-pdf-file-using-python)
        ax.axis('tight')
        ax.axis('off')
        the_table = ax.table(cellText=df.values,colLabels=df.columns,loc='center')

        pp = PdfPages(pdfPath)
        pp.savefig(fig, bbox_inches='tight')
        pp.close()

        sendDocumentToEmail(documentPath=[pdfPath], emailAdress=USERSELECTION.emailPrinter, emailSubject='Print CSV', successMessage= 'Stock space successfully sent', failedMessage='Email sending failed, manualy send stock space')


    def getMassMeasured(self):
        """Gets the actual mass measured and adds them into a list."""
        
        path = USERSELECTION.generatedCsvPath + 'stockSpace.csv'                                                                   
        df = pd.read_csv(path, index_col=None)
        self.stockMassVector = df['Actual mass measured'].tolist()
        originalMass = df['Mass to measure (in grams)'].tolist()
     
    def getStockSpace(self):
        """Calculates the volumes of CH3CN and CH2Cl2 to make up stock solutions for each chemiacl in the batch space."""
        
        self.DichloromethaneVolumeVector = []                                                                                           #Ensures that the lists are completly empty.
        self.AcetonitrileVolumeVector = []

        for chemicalIdx, chemical in enumerate(self.WholeChemicalSpace.space):                                                          #Iterating through the reagents.
            chemical_mass = self.stockMassVector[chemicalIdx]
            chemicalMw = chemical.molecularWeight
            chemcialConcentration = chemical.concentrationInStockVial/1000                                                              #Divide by 1000 to get concentration in M.
            if chemcialConcentration != 0:                                                                                              #some chemicals have a may have a concentration of 0 (division by 0 = error).
                final_stock_volume = chemical_mass/chemicalMw/chemcialConcentration                                                     #volume = mass/MW/concentration
                solubility_CCl2H2, solubility_CH3CN = chemical.solubility
                if solubility_CCl2H2 == 0 and solubility_CH3CN == 0:                                                                    #Some chemicals my be insoluble in both solvents. Solubility tuple = (0,0).  
                    self.DichloromethaneVolumeVector.append(0)
                    self.AcetonitrileVolumeVector.append(0) 

                else:
                    volume_CCl2H2 = (solubility_CCl2H2/(solubility_CCl2H2+solubility_CH3CN))*final_stock_volume*1000000                 #Subdividing the stock volume based on the chemicals solubility in CH3CN / CH2Cl2 and muilitplying by 1000000 to get volumes in microlitre.
                    volume_CH3CN = (solubility_CH3CN/(solubility_CH3CN+solubility_CCl2H2))*final_stock_volume*1000000
                
                    self.DichloromethaneVolumeVector.append(volume_CCl2H2)
                    self.AcetonitrileVolumeVector.append(volume_CH3CN)
            else:
                final_stock_volume = 0
                self.DichloromethaneVolumeVector.append(0)
                self.AcetonitrileVolumeVector.append(0)

    def saveStockSpaceToCsv(self):
        """Saves the generated stock space to a csv."""

        pathCsv = USERSELECTION.generatedCsvPath + 'stockSpace.csv'
        pathLogs = USERSELECTION.logsPath + str(self.batchNumber) + '_stockSpace.csv'
        df = pd.read_csv(pathCsv, index_col=None)                                                                                       #Reading the mass calculated csv.
        df['CH3CN'] = self.AcetonitrileVolumeVector                                                                                     #Adding the CH3CN volumes to the df.
        df['CCl2H2'] = self.DichloromethaneVolumeVector                                                                                 #Adding the CCl2H2 volumes to the df.
        df.to_csv(pathCsv, index=False)                                                                                                 #Saving the csv to the generated csvs folder.
        df.to_csv(pathLogs)                                                                                                             #Saving the csv to logs (stores information on the measured masses inputted by the chemist).


    def saveNmrJson(self):
        """Saves a JSON to be read by the NMR autosampler."""
        
        nmrFileName = 'batch' + str(self.batchNumber) + '.json'
        path = USERSELECTION.generatedJsonPath + nmrFileName
        jsonToSave = {}
        
        
        for reaction_num, reaction in enumerate(self.batchSpace):
            sampleInfoText = str(reaction.unique_identifier) + ': '                                                                     #Generating a string with reaction id, and reagents to be read by Bruker app.
            sampleInfoText += str(reaction.reagents)
            sampleInfoText += ' : ['
            for reagent in reaction.reagents:
                sampleInfoText += str(reagent.ID) + ', '
            
            sampleInfoText = sampleInfoText[:-2]
            sampleInfoText += ']'
                       
            jsonToSave[f"{reaction_num + 1}"] = {                                                                                       #This is the json format readable by the NMR autosampler (autosampler script and code was created by Dr.Filip Szczypinski, say hi to him for me).
                "sample_info": sampleInfoText,
                "solvent":  USERSELECTION.solvent,
                "nmr_experiments": [
                    {
                        "parameters": USERSELECTION.parameters,
                        "num_scans": USERSELECTION.numScans,
                        "pp_threshold": USERSELECTION.ppThershold,
                        "field_presat": USERSELECTION.fieldPresat
                    }
                ]
            } 

        with open(path, 'w', newline="\n") as json_output:                                                                              #saving the generated NMR json to the appropiate folder.
            json.dump(jsonToSave, json_output, indent=4)
            
    def saveMsCsv(self):
        """Saves the batch reactions as a LCMS autosampler readable csv."""

        csvDictionary = {                                                                                                               #The dictionary to be saved as a csv.                                                                               
            'INDEX': [],                                                                                                                #An index for the autosampler is reqruired.
            'FILE_NAME': [],                                                                                                            #This is the file name for the samples UV and MS spectra.
            'FILE_TEXT': [],                                                                                                            #IDK what this does, I think it just makes the sample spectra more human interpretable.
            'MS_FILE': [],                                                                                                              #This is the name of the file used for MS protols (i.e. injection speeds, M/Z range).
            'MS_TUNE_FILE': [],                                                                                                         #Similar to the MS_file its a file name. The file is generated by the Water's LCMS machine when a user wants to run the same spectra over different samples.
            'INLET_FILE': [],                                                                                                           #Agian this is similar to the two previous.
            'SAMPLE_LOCATION': [],                                                                                                      #This is the location of the sample in the LCMS rack. In this case, the reaction order in the batch space is the same as the the sample location indx.
            'INJ_VOL': []                                                                                                               #This is the injection volume for MS / UV-Vis.
            }

        for reaction_indx, reaction in enumerate(self.batchSpace):                                                                     #Iterating through the reactions in the batch space and adding its sample parameters to the csvDictionary.
            text_var = str(reaction.unique_identifier)
            csvDictionary['INDEX'].append(reaction_indx + 1)
            csvDictionary['FILE_NAME'].append(text_var)
            csvDictionary['FILE_TEXT'].append(text_var)                                                                                 #The file name is the batchnumber_reactionid
            csvDictionary['MS_FILE'].append('SupraChemCage')
            csvDictionary['MS_TUNE_FILE'].append('SupraChemCage')
            csvDictionary['INLET_FILE'].append('SupraChemCage')
            csvDictionary['SAMPLE_LOCATION'].append(f'1:{reaction_indx+1}')
            csvDictionary['INJ_VOL'].append(USERSELECTION.msInjectionVolume)

        msFileName = 'batch' + str(self.batchNumber) + '.csv'
        path = USERSELECTION.generatedMsCsvPath + msFileName                                                                            #Reading the dictionary as a dataframe and saving it as a csv.
        df = pd.DataFrame.from_dict(csvDictionary)
        df.to_csv(path, index=False)


    def sendNmrJasonAndMsCsvToEmail(self):
        """Sending the generated NMR Jason to email via outlook."""
        
        nmrFileName = 'batch' + str(self.batchNumber) + '.json'
        msFileName = 'batch' + str(self.batchNumber) + '.csv'

        jsonPath = USERSELECTION.generatedJsonPath + nmrFileName
        CsvPath = USERSELECTION.generatedMsCsvPath + msFileName
        
        sendDocumentToEmail(documentPath=[jsonPath, CsvPath], emailAdress=USERSELECTION.emailGunther, emailSubject='NMR Json and MS CSV', successMessage= 'NMR json and MS CSV successfully sent', failedMessage='Email sending failed, manualy send NMR Json and MS CSV')
    
    def exportSampleSpace(self):
        """Saves the ReactionSpace nested in the BatchSpace as a seperate ReactionSpace object."""
        
        path = USERSELECTION.generatedPicklePath+'SampleSpace.pickle'
        with open(path, 'wb') as pickleFile:
            pickle.dump(self.SampleSpace, pickleFile)

    def retakeBatches(self, batches: list):
        """Function allows for failed batches to be retaken."""
        
        self.SampleSpace.retakeBatches(batches)
    
    def retakeReactions(self, reactionIDXs:list):
        """Function allows for failed reactions to be retaken."""
        
        self.SampleSpace.retakeReactions(reactionIDXs)