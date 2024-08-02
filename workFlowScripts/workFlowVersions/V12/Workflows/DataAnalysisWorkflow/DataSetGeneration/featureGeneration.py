"""
The goal of this script is to generate features for ML tool. The way its structed is that featuers for indivual reagents are calculated in the form of a hash table. Then reactions are itterated through and their reagents mapped via the dictionary.
Features are generated individualy as a function. To use the function a mapping function is used.
The features generated for the following chemical subtypes are:

Metal: 'metalSize', 'metalCharge', 'preferredCoordinationGeometry', 'id', 'smiles', 'formula' 'molecularWeight', 'commonName', 'chemSpiderObject', 'chemicalClass', 'morganFingerPrint'	 #NOTE the expected cordination number is note added in the hashtable as this is calculted when reactions are geenrated. Instead to get the expected coordination number, get the metal object in reagents of the reaction object, and use the .selectedCoordinationNum attribute of the metal.
Aldehdye: 'ringSize', 'substituentVolume', 'coordinatingNitrogenPartialCharge', 'carbonCarbonylPartialCharge', 'oxygenCarbonylPartialCharge', 'HomoLumoGap', 'id', 'smiles', 'formula', 'molecularWeight', 'commonName', 'chemSpiderObject', 'chemicalClass', 'morganFingerPrint', 'spectrumIR', 'atomCoodinates'
Amine: 'amineDistance', 'amineRigidity', 'numRotatableBonds', 'amineDihedralAngle', 'numPrimaryAmines', 'numAromaticAmimes', 'amineClass', 'nitrogen1PartialCharge', 'nitrogen2PartialCharge', 'HomoLumoGap', 'id', 'smiles', 'formula', 'molecularWeight', 'commonName', 'chemSpiderObject', 'chemicalClass', 'morganFingerPrint', 'spectrumIR', 'atomCoodinates'

For information of the features see the doc: featureDescription.docx.

The hashtable is initialy in the form of:
'compound CAS': [APIsearchResult1:{feature1: value1, feature2: value2},
                 APIsearchResult2:{feature1: value1, feature2: value2}]

For compounds with multiple API search results, the values of features of search results are combined. 
This hash table is then decreased for the masterthesis project into:

Metal: 'metalSize'
Aldehdye: 'ringSize', 'substituentVolume', 'carbonCarbonylPartialCharge'
Amine: 'numRotatableBonds', 'amineDihedralAngle', 'amineClass'

Reactions (from sampleSpace.pickle) are then iterated through, taking the reagents in each reaction along with the reagents mapping hastablevalues. To create a featureDictionary.pickle. This pickle file is then used to add labels of reaction out comes (see RunningWorkflow.docx).

"""

from rdkit import Chem, DataStructs
import matplotlib.pyplot as plt
from rdkit.Geometry import rdGeometry
from rdkit.Chem import rdMolTransforms
from rdkit.Chem import rdMolDescriptors, rdDistGeom, rdDepictor, Fragments
from rdkit.Chem import Draw, AllChem, rdmolops, rdForceFieldHelpers, rdmolfiles
import rdkit.Chem.AllChem as rdchem
from rdkit.Chem.Draw import IPythonConsole
from chemspipy import ChemSpider
import numpy as np
import os
import importlib.util
import sys
import time
from random import random
import pandas as pd
import pickle
import subprocess
import orca_parser as op
from PIL import Image
import math


#Importing script classes
rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])
scriptClasses = strCWD + '/PythonModules/scriptClasses.py'
spec = importlib.util.spec_from_file_location('scriptClasses', scriptClasses)
scriptClasses = importlib.util.module_from_spec(spec)
sys.modules['scriptClasses'] = scriptClasses
spec.loader.exec_module(scriptClasses)

#Importing combination workflow parameters
combinationParametersPath = strCWD + '/ReactionCombinationsworkflow/MainScripts/workflowParameters.py'
spec = importlib.util.spec_from_file_location('combinationParameters', combinationParametersPath)
combinationParameters = importlib.util.module_from_spec(spec)
sys.modules['combinationParameters'] = combinationParameters
spec.loader.exec_module(combinationParameters)

#chemicalsInWholeSpace is a list of chemicals the chemspeed platform can handle. chemicalsToRemove are chemicals that are not part of the combination libraries.
chemicalsInWholeSpace = combinationParameters.chemicalsInWholeSpace                                                                                         
chemicalsToRemove = combinationParameters.chemicalsToRemove
chemicals = chemicalsInWholeSpace.copy()

#Removing chemicals that are not part of the combianation libraries (no reactions contain these chemicals).
for chemical in chemicalsToRemove:
    for wholeChemical in chemicalsInWholeSpace:
        if chemical.name == wholeChemical.name:
            chemicals.remove(wholeChemical)

def exportToPickle(location:str, compoundHashTable:dict):
    """Saves the generated hashtable to a pickle."""
    
    with open(location, 'wb') as handle:
        pickle.dump(compoundHashTable, handle, protocol=pickle.HIGHEST_PROTOCOL)

def mapData(function):
    """Takes in the compoundHashTable, a function and applies the function to the hash table."""

    #Reading the hashtable pickle
    hashTablePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/compoundHashTable.pickle'
    
    with open(hashTablePath, 'rb') as f:
        dictionary = pickle.load(f)

    iterdictionary = dictionary.copy()
    for compound in iterdictionary.items():
        compoundCAS, compoundData = compound
        result = function(compoundCAS, compoundData)
        dictionary[f'{compoundCAS}'] = result
    
    exportToPickle(location=hashTablePath, compoundHashTable=dictionary)
    # #Amine Example
    # print(dictionary['479-27-6'])

    # #Aldhyde Example
    # print(dictionary['54221-96-4'])

    # #Metal Example
    # print(dictionary['27860-83-9'])

    return dictionary

def getMoleculeClass(compoundCAS, compoundData):
    """Lables the reagent based on its subdivision (Metal, Diamine, Monoaldhyde, Dialdehyde, Monoamine). This is done by looking at its class instance."""

    for reagent in chemicals:
        if reagent.CAS == compoundCAS:
            for data in compoundData:
                data['chemicalClass'] = reagent.__class__.__name__

    return compoundData

def generateXYZFileForGeometryOptimization(compoundCAS, compoundData):
    """Adds hyrdogens to the chemspider object, calculates the lowest energy conformer and saves it as an XYZ file. This file will be run in orca for geometry optimization and then single point energy calcluations."""
             
    #Searches might have different results, and so must be iterated through.
    for resultIdx, result in enumerate(compoundData):
        if result['chemicalClass'] == 'Diamine' or  result['chemicalClass'] == 'Monoaldehdye':                                                #Checking that the reagent is an amine, if not returns the data unedited.
            #Creating a folder to put in all calculation information
            newpath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/calculationFiles/' + str(result['id']) + '/geometryOptimization'
    
            #Checking that the directory does not exist. If it doesnt, then it makes the directory and generates the xyz file.
            if not os.path.exists(newpath):
                os.makedirs(newpath)
            
            try:
                result['chemSpiderObject'] = Chem.rdmolops.AddHs(result['chemSpiderObject'], addCoords=True)                    #Adding hydrogens to the chemspiderobject.
                Chem.rdDepictor.Compute2DCoords(result['chemSpiderObject'])                 #Getting coordinates of the atoms.

                params = AllChem.ETKDGv3()
                params.randomSeed = 0xf00d
                params.useSmallRingTorsions = True

                AllChem.EmbedMultipleConfs(              #Generating conformers.
                    result['chemSpiderObject'],
                    numConfs=1000,
                    params=params
                    )
                
                optConf = Chem.rdForceFieldHelpers.MMFFOptimizeMoleculeConfs(    #Optimization of structure with MMFF, returns list of [tuple(is_converged,energy))]
                    result['chemSpiderObject'], 
                    maxIters=1000,
                    )
                
                lowestEnergy = optConf[0][1]
                conformerId = 0

                for conformer in optConf:               #Finding the lowest energy conformer.
                    if conformer[1] < lowestEnergy:
                        lowestEnergy = conformer[1]
                        conformerId = optConf.index(conformer)

                mmffps = Chem.rdForceFieldHelpers.MMFFGetMoleculeProperties(result['chemSpiderObject'])

                ff = Chem.rdForceFieldHelpers.MMFFGetMoleculeForceField(            #Calcualting the MMF forcefield.
                    result['chemSpiderObject'],
                    mmffps,
                    confId=int(conformerId),
                    )

                maxIters = 10
                while ff.Minimize(maxIts=10000) and maxIters>0:
                    maxIters -= 1
                
                
                # Save the lowest conformer as XYZ file
                # fileName = newpath + '/' + str(result['id']) + '.inp'
                # Chem.rdmolfiles.MolToXYZFile(result['chemSpiderObject'], fileName, confId=int(conformerId))

                
            except Exception as e:
                print(e)

    return compoundData

def prepareXYZFileForOrcaOptimization(compoundCAS, compoundData):
    """Function looks at all results of compound XYZfiles and changes them to make them Orca interpretable."""
    
    for result in compoundData:
        if result['chemicalClass'] == 'Diamine' or  result['chemicalClass'] == 'Monoaldehdye':

            filePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/calculationFiles/' + str(result['id']) + '/geometryOptimization' + '/' + str(result['id']) + '.inp'
            filePathNew =  strCWD + '/DataAnalysisWorkflow/DataSetGeneration/calculationFiles/' + str(result['id']) + '/geometryOptimization' + '/' + str(result['id']) + 'New' + '.inp'
            
            #Checking that the file exists
            if os.path.exists(filePath):
            
                #Getting simulated IR spectra, with geometry optimization: !B3LYP DEF2-SVP OPT RIJCOSX FREQ
                with open(filePath,'r') as f:
                    with open(filePathNew,'w') as f2: 
                        f2.write(
                            "# Input file for Orca geometry optimization and IR calculation."
                            "\n!B97-3c LARGEPRINT Opt Freq"
                            "\n%MaxCore 900"
                            "\n%pal nprocs 5 end"
                            "\n\n* xyz 0 1"
                        )
                        next(f)
                        f2.write(f.read())
                        f2.write("*")

                os.remove(filePath)
                os.rename(filePathNew,filePath)
        
    return compoundData

def optimizeGeometryOrca(compoundCAS, compoundData):
    """Runs the xyz file for geometry optimization and IR spectra simulation"""
    
    #Searches might have different results, and so must be iterated through.
    for resultIdx, result in enumerate(compoundData):
        if result['chemicalClass'] == 'Diamine' or  result['chemicalClass'] == 'Monoaldehdye':                                                #Checking that the reagent is an amine, if not returns the data unedited.
        
            #Getting various paths to different files.
            geometryOptimizationLocation = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/calculationFiles/' + str(result['id']) + '/geometryOptimization/'        #This is the calculation folder for the compound of interest.
            orcaFileLocation =  geometryOptimizationLocation + str(result['id']) + '.inp'                                                                               #This is the orca input file.
            orcaNewFileLocation = geometryOptimizationLocation + str(result['id']) + 'New' + '.inp'                                                                     #This is the orca output file.
            orcaAppLocation = "C:/Users/emanuele/Desktop/Orca/orca"                                                                                                     #This is the orca App location (to run processes).
            
            #Checking that the orca file exists and the new file has not been generated as computationaly expensive.
            
            if os.path.exists(orcaFileLocation) and not os.path.exists(orcaNewFileLocation):                
                
                commandToExecute = orcaAppLocation + ' ' + orcaFileLocation + ' > ' + orcaNewFileLocation                                                               #This is the powershell command to execute.

                returnCode = subprocess.call(["powershell", "-Command", commandToExecute])                                                                              #Executing command in powershell with subprocesses. 

                if returnCode == 0:
                    print('Geometry optimization of ' + str(result['id']) + ' successful')
                
                else:
                    print(str(result['id']) + ' failed optimization')
            
            #Checking the calculation file has already been generated.
            elif os.path.exists(orcaNewFileLocation):
                print('Geometry optimization of ' + str(result['id']) + ' successful')
        

    return compoundData

def extractGeometryOptimizationOrcaFile(compoundCAS, compoundData):
    """Extracts atoms coordinates, relavent partial charges, IR spectrum of relevent compounds."""

    #Searches might have different results, and so must be iterated through.
    for resultIdx, result in enumerate(compoundData):
        if result['chemicalClass'] == 'Diamine' or  result['chemicalClass'] == 'Monoaldehdye': 
            orcaFile = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/calculationFiles/' + str(result['id']) + '/geometryOptimization/' + str(result['id']) + 'New' + '.inp'                 #This is the output orca file of the geometry optimization.

            orcaData = op.ORCAParse(orcaFile)
            
            #checking that optimization has converged.
            if orcaData.valid:

                #Getting the appropiate information form Orca file

                #IR spectrum
                orcaData.parse_IR()
                spectrumIR = orcaData.IR.to_dict()  #The IR spectrum is parsed as a pandas dataframe. This is converted to a dictionary.
                result['spectrumIR'] = spectrumIR

                #Optimized coordinates (x,y,z) are in the form: [(atom, [coordinates]), (atom, [coordinates]), (atom, [coordinates])]
                atomCoordinates = []
                orcaData.parse_coords()
                XyzCoordiantes = orcaData.coords[-1].tolist()                                                            #This is the goemetry optimzied atom coordinates.
                orcaData.parse_charges()
                atoms = orcaData.atoms                                                                                   #These are the atoms in the compound.
                
                for atomCoordinatePair in zip(atoms, XyzCoordiantes):
                    atomCoordinates.append(atomCoordinatePair)
                
                result['atomCoodinates'] = atomCoordinates

                #Getting partial charges information
                charges = orcaData.charges                                                                                #These are the calculated partial charges (Mulliken, Loewdin, Mayer)

                #Depending on if the compound is an amine or aldehyde partial charges of different atoms are taken
                # Amine: parital charge of reacting nitrogens H2N-R-NH2
                #Aldhdye: partical chage of reaction C, O in carbonyl group, and Nitrogen in chelating bond R-N-C-C=O

                if result['chemicalClass'] == 'Diamine':
                     chemSpiderObject = result['chemSpiderObject']
                     amineFragment = rdchem.MolFromSmarts('[NH2]')                                                               #The amine fragement to find in the compound
                     posAmine = rdchem.Mol.GetSubstructMatches(chemSpiderObject, amineFragment, uniquify=False)
                     posAmine1 = (posAmine[0][0])                                                                        #Index of the first amien fragment.
                     posAmine2 = (posAmine[1][0])                                                                        #Index of the second amine fragment.
                     
            
                     #Getting their Mulliken partial charges
                     result['nitrogen1PartialCharge'] = charges["Mulliken"][posAmine1]
                     result['nitrogen2PartialCharge'] = charges["Mulliken"][posAmine2]

                if result['chemicalClass'] == 'Monoaldehdye':
                    chemSpiderObject = result['chemSpiderObject']
                    
                    #Getting the locations of the atoms of interest.
                    nitrogenCarbonylFragment = Chem.MolFromSmarts('[nX2][#6][CX3H1](=O)')                                                    #The aldhdehyde fragment to find in the compound.
                    posFragement = rdchem.Mol.GetSubstructMatches(
                        chemSpiderObject, 
                        nitrogenCarbonylFragment,
                        uniquify=True,
                        )
            
                    #The locations of atoms of interest.
                    coordinatingNitrogenIdx = posFragement[0][0]
                    carbonCarbonylIdx = posFragement[0][2]
                    oxygenCarbonylIdx = posFragement[0][3]

                    #Getting their Mulliken partial charges
                    result["coordinatingNitrogenPartialCharge"] = charges["Mulliken"][coordinatingNitrogenIdx]
                    result["carbonCarbonylPartialCharge"] = charges["Mulliken"][carbonCarbonylIdx]
                    result["oxygenCarbonylPartialCharge"] = charges["Mulliken"][oxygenCarbonylIdx]

            else:
                print(str(result['id']) + 'has failed to converge. Please rerun file in orca and then re-execute extractGeometryOptimizationOrcaFile().')

    return compoundData

def generateXYZFilesForHomoLumo(compoundCAS, compoundData):
    """Generates a cation radical, anion radical, and neutral species orca input files, to then be used to calculate HOMO, LUMO and HOMO-LUMO gap."""
    
    #Searches might have different results, and so must be iterated through.

    for resultIdx, result in enumerate(compoundData):
        if result['chemicalClass'] == 'Diamine' or  result['chemicalClass'] == 'Monoaldehdye': 
            filePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/calculationFiles/' + str(result['id']) + '/'                   #This is the folder for the reagent and all its calculations.
            
            #Functional (PWPB95) ! RIJK RI-PWPB95 D3BJ def2-TZVP def2/JK def2-TZVP/C TIGHTSCF) as it was one of the best preformers in the GMTKN30 benchmark study (https://sites.google.com/site/orcainputlibrary/dft-calculations/double-hybrid-dft), is a double hybrids DFT calculation (double hyhbrids are seen as the last rug on the DFT Jacob's ladder = https://computationalchemistry.fandom.com/wiki/Double_hybrid), is not computationaly expensive and can be run on most mid-ranged laptops.
            
            #To calculate HOMO and LUMO gap the single point energy of the cation and anion radicals must be calculated. Therefore orca files for these species must be generated.
            for species in [[filePath+'/neutralCompound/', '0', '1'],
                                    [filePath+'/cationRadical/', '+1', '2'], 
                                    [filePath+'/anionRadical/', '-1', '2']]:

                speciesPath = species[0]
                speciesCharge = species[1]
                speciesMultiplicity = species[2]

                #generating the calculation directories.
                if not os.path.exists(speciesPath+'/'+str(result['id'])+'.inp'):
                    os.makedirs(speciesPath)
                    with open(speciesPath+'/'+str(result['id'])+'.inp', 'w') as f:
                        f.write(
                            "# Input file for Orca single point energy calculation."
                            "\n! RIJK RI-PWPB95 D3BJ def2-TZVP def2/JK def2-TZVP/C TIGHTSCF"
                            "\n%MaxCore 900"
                            "\n%pal nprocs 5 end"
                            f"\n\n* xyz {speciesCharge} {speciesMultiplicity}"
                        )

                        for atom, atomCoordintes in result['atomCoodinates']:
                            f.write(f'\n{atom} {atomCoordintes[0]} {atomCoordintes[1]} {atomCoordintes[2]}')
                        f.write("\n*")
    return compoundData

def calcualtePointEnergiesOrca(compoundCAS, compoundData):
    """This runs the generated orca files to calculate point energies for neutral, cation radical, anion radical species"""
    #Searches might have different results, and so must be iterated through.

    for resultIdx, result in enumerate(compoundData):
        if result['chemicalClass'] == 'Diamine' or  result['chemicalClass'] == 'Monoaldehdye': 
            
            #Relevant paths.
            filePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/calculationFiles/' + str(result['id']) + '/'                   #This is the folder for the reagent and all its calculations.
            orcaAppLocation = "C:/Users/emanuele/Desktop/Orca/orca"

            #Functional (PWPB95) ! RIJK RI-PWPB95 D3BJ def2-TZVP def2/JK def2-TZVP/C TIGHTSCF) as it was one of the best preformers in the GMTKN30 benchmark study (https://sites.google.com/site/orcainputlibrary/dft-calculations/double-hybrid-dft), is a double hybrids DFT calculation (double hyhbrids are seen as the last rug on the DFT Jacob's ladder = https://computationalchemistry.fandom.com/wiki/Double_hybrid), is not computationaly expensive and can be run on most mid-ranged laptops.
            
            #Running orca files for all three species (eutral, cation radical, anion radical).
            for species in [filePath+'/neutralCompound/', filePath+'/cationRadical/', filePath+'/anionRadical/']:
                
                #Checking that the orca file exists and the new file has not been generated as computationaly expensive.

                orcaFileLocation = species+str(result['id'])+'.inp'
                orcaNewFileLocation = species+str(result['id'])+'New'+'.inp'

                if os.path.exists(orcaFileLocation) and not os.path.exists(orcaNewFileLocation):                
                    
                    commandToExecute = orcaAppLocation + ' ' + orcaFileLocation + ' > ' + orcaNewFileLocation                                                               #This is the powershell command to execute.

                    returnCode = subprocess.call(["powershell", "-Command", commandToExecute])                                                                              #Executing command in powershell with subprocesses. 

                    if returnCode == 0:
                        print('Single point energy calculation of ' + str(result['id']) + ' successful')
                    
                    else:
                        print(str(result['id']) + ' failed optimization')
                
                #Checking the calculation file has already been generated.
                elif os.path.exists(orcaNewFileLocation):
                    print('Single point energy calculation of ' + str(result['id']) + ' successful')

    return compoundData

def recalculatePointEnergiesOrca(compoundCAS, compoundData):
    """This reruns the generated orca files to calculate point energies for neutral, cation radical, anion radical species"""
    #Searches might have different results, and so must be iterated through.

    for resultIdx, result in enumerate(compoundData):
        if result['chemicalClass'] == 'Diamine' or  result['chemicalClass'] == 'Monoaldehdye': 
            
            #Relevant paths.
            filePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/calculationFiles/' + str(result['id']) + '/'                   #This is the folder for the reagent and all its calculations.
            orcaAppLocation = "C:/Users/emanuele/Desktop/Orca/orca"

            #Functional (PWPB95) ! RIJK RI-PWPB95 D3BJ def2-TZVP def2/JK def2-TZVP/C TIGHTSCF) as it was one of the best preformers in the GMTKN30 benchmark study (https://sites.google.com/site/orcainputlibrary/dft-calculations/double-hybrid-dft), is a double hybrids DFT calculation (double hyhbrids are seen as the last rug on the DFT Jacob's ladder = https://computationalchemistry.fandom.com/wiki/Double_hybrid), is not computationaly expensive and can be run on most mid-ranged laptops.
            
            #Running orca files for all three species (eutral, cation radical, anion radical).
            for species in [filePath+'/neutralCompound/', filePath+'/cationRadical/', filePath+'/anionRadical/']:
                
                #Checking that the orca file exists and the new file has not been generated as computationaly expensive.

                orcaFileLocation = species+str(result['id'])+'.inp'
                orcaNewFileLocation = species+str(result['id'])+'New'+'.inp'
                orcaData = op.ORCAParse(orcaNewFileLocation)

                if orcaData.valid == False:                
                    
                    commandToExecute = orcaAppLocation + ' ' + orcaFileLocation + ' > ' + orcaNewFileLocation                                                               #This is the powershell command to execute.

                    returnCode = subprocess.call(["powershell", "-Command", commandToExecute])                                                                              #Executing command in powershell with subprocesses. 

                    if returnCode == 0:
                        print('Single point energy calculation of ' + str(result['id']) + ' successful')
                    
                    else:
                        print(str(result['id']) + ' failed optimization')
                
                #Checking the calculation file has already been generated.
                elif os.path.exists(orcaNewFileLocation):
                    print('Single point energy calculation of ' + str(result['id']) + ' successful')

    return compoundData

def calculateHomoLumoFromPointEnergiesOrca(compoundCAS, compoundData):
    """This calculates the HOMO LUMO gap from the generated orca files to calculate point energies for neutral, cation radical, anion radical species"""
    
    #Searches might have different results, and so must be iterated through.

    for resultIdx, result in enumerate(compoundData):
        if result['chemicalClass'] == 'Diamine' or  result['chemicalClass'] == 'Monoaldehdye':         
            #Relevant paths.
            filePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/calculationFiles/' + str(result['id'])                    #This is the folder for the reagent and all its calculations.
            cationRadicalPath = filePath + '/cationRadical/' + str(result['id']) + 'New.inp'                                       #Cation radical orca file.
            anionRadicalPath = filePath + '/anionRadical/' + str(result['id']) + 'New.inp'                                        #Anion radical orca file.
            neutralMoleculePath = filePath + '/neutralCompound/' + str(result['id']) + 'New.inp'                                     #Neutral molecule orca file.

            #Parsing Orca file and their energies.
            cationRadicalData = op.ORCAParse(cationRadicalPath)
            anionRadicalData = op.ORCAParse(anionRadicalPath)
            neutralMoleculeData = op.ORCAParse(neutralMoleculePath)

            #Checking if calculations are valid before extracting single point energies.
            if cationRadicalData.valid and anionRadicalData.valid and neutralMoleculeData.valid:
                print(result['id'])
                cationRadicalData.parse_energies()
                anionRadicalData.parse_energies()
                neutralMoleculeData.parse_energies()

                cationSinglePointEnergy = cationRadicalData.energies[-1]
                anionSinglePointEnergy = anionRadicalData.energies[-1]
                neutralSinglePointEnergy = neutralMoleculeData.energies[-1]
                

            #Calculating the HOMO LUMO gap. Calculation based on https://www.reddit.com/r/comp_chem/comments/16qaejw/functional_for_homolumo_gap_of_organic_dyes/
            # n-1 (radical cation) and n+1 (radical anion) electron system to get IP (E(n) - E(n-1)) and EA (E(n+1) - E(n)).
            #The electronic (HOMO-LUMO) gap is then just IP-EA.
            IP = neutralSinglePointEnergy - cationSinglePointEnergy
            EA = anionSinglePointEnergy - neutralSinglePointEnergy
            result['HomoLumoGap'] = IP - EA
            
    return compoundData

def getMorganFingePrint(compoundCAS, compoundData):
    """Get the morgan finger print of the compound adds it to compound data as 'morganFingerPrint' key'"""
    
    #Searches might have different results, and so must be iterated through.
    
    features = []
    for result in compoundData:
        bit={}
        morganFingerPrint = rdchem.GetMorganFingerprintAsBitVect(result['chemSpiderObject'], 3, 1024, bit)
        mfpVector = np.array(morganFingerPrint).tolist()
        result['morganFingerPrint'] = mfpVector
        print(mfpVector)
    return compoundData

def getAmineInformation(compoundCAS, compoundData):
    """This gets features relevent to the amines.
    Takes in variable as a list of features from the compoundHashTable.
    Generates features in the form: [{rdchem object, Commmon name , molecular formula, smiles, molecular wieght, record id} ] 
    number of primary amines
    number of aromatic amines
    number of rotatable bonds
    number of bonds between amines (from nitrogens)
    Rigidity of bond between amines
    Dihedral angle between amines
    Class of amine (alkyl and aromatic amine, alkyl amine, aromatic amine)
    """

    def calcamineDistance(chemSpiderObject):
        """Function calculates the distance between nitrogens in the amine group."""
        amine = rdchem.MolFromSmarts('[NH2]')
        posAmine = rdchem.Mol.GetSubstructMatches(chemSpiderObject, amine, uniquify=True)
        posAmine1 = (posAmine[0][0])
        posAmine2 = (posAmine[1][0])
        distance = len(rdchem.GetShortestPath(
            chemSpiderObject, 
            posAmine1, 
            posAmine2,
        )) -1
        return distance
    
    def calcamineDihedralAngle(chemspiderobject):
        """Function calculates the dihedral angle between amines and its regidity. Returns a tuple in the form (dihedral angle, regidity)"""
        
        #Getting the amine fragment
        carbonAmineFragement = Chem.MolFromSmarts('[#6]-[NH2]')
        chemspiderobjectWithHydrogens = Chem.rdmolops.AddHs(chemspiderobject, addCoords=True)
        fragmentLocations = rdchem.Mol.GetSubstructMatches(
            chemspiderobjectWithHydrogens,
            carbonAmineFragement,
            uniquify=True
        )


        #Getting carbon positions in compound
        carbonPosition1 = fragmentLocations[0][0]
        nitrogenPosition1 = fragmentLocations[0][1]
        carbonPosition2 = fragmentLocations[1][0]
        nitrogenPosition2 = fragmentLocations[1][1]

        #Getting different possible compound confomers
        numConformers = chemspiderobjectWithHydrogens.GetNumConformers()

        dihedralAngles = []

        #Calculating the dihedral angle between the two fragments for each conformer
        for conformerIdx in range(numConformers):
            conformer = chemspiderobjectWithHydrogens.GetConformer(conformerIdx)
            
            carbonPosition1Coordinates = conformer.GetAtomPosition(carbonPosition1)
            nitrogenPosition1Coordinates = conformer.GetAtomPosition(nitrogenPosition1)
            carbonPosition2Coordinates = conformer.GetAtomPosition(carbonPosition2)
            nitrogenPosition2Coordinates = conformer.GetAtomPosition(nitrogenPosition2)

            vector1 = rdGeometry.Point3D.DirectionVector(
                carbonPosition1Coordinates,
                nitrogenPosition1Coordinates
            )

            vector2 = rdGeometry.Point3D.DirectionVector(
                carbonPosition2Coordinates,
                nitrogenPosition2Coordinates
            )
            
            dihedralAngle = rdGeometry.Point3D.AngleTo(
                vector1,
                vector2
            )

            dihedralAngle = math.degrees(dihedralAngle)

            dihedralAngles.append(abs(dihedralAngle))
        
        #Cacluate standard deviation of dihedral angles. This is a proxy for rigidity of diamines.
        deviation = np.std(dihedralAngles)

        if deviation <= 10:
            dihedralAngle = np.average(dihedralAngles)
        
        else:
            dihedralAngle = 360

        #returning the 'rigidity' of the bond and the dihedral angle as a tuple (regidity, angle)
        print(deviation, dihedralAngle)
        return(deviation, dihedralAngle)

    def getAmineClass(chemSpiderObject):
        """Gets the type of amine of the compound (alkyl and aromatic amine, alkyl amine, aromatic amine)"""

        #Getting the positions of the carbon amine fragments

        alkylcarbonAmineFragment = Chem.MolFromSmarts('[C]-[NH2]')
        positionAlkylFragment = rdchem.Mol.GetSubstructMatches(
            chemSpiderObject, 
            alkylcarbonAmineFragment,
            uniquify=True,
            )
        
        aromaticCarbonAmineFragment = Chem.MolFromSmarts('[c]-[NH2]')
        positionAromaticFragment = rdchem.Mol.GetSubstructMatches(
        chemSpiderObject, 
        aromaticCarbonAmineFragment,
        uniquify=True,
        )
            
        if len(positionAlkylFragment) > 0 and len(positionAromaticFragment) > 0:
            return "alkyl and aromatic amine"

        elif len(positionAlkylFragment) > 0 and len(positionAromaticFragment) == 0:
            return "alkyl amine"
 
        elif len(positionAlkylFragment) == 0 and len(positionAromaticFragment) > 0:
            return "aromatic amine"
        
        else:
            return None

    #Searches might have different results, and so must be iterated through.
    for result in compoundData:
        if result['chemicalClass'] != 'Diamine':                                                #Checking that the reagent is an amine, if not returns the data unedited.
            return compoundData
        else:
            result['numPrimaryAmines'] = Fragments.fr_NH2(result['chemSpiderObject'])
            result['numAromaticAmimes'] = Fragments.fr_Ar_NH(result['chemSpiderObject'])
            result['numRotatableBonds'] = rdMolDescriptors.CalcNumRotatableBonds(result['chemSpiderObject'], False)
            result['amineDistance'] = calcamineDistance(result['chemSpiderObject'])
            result['amineRigidity'], result['amineDihedralAngle']  = calcamineDihedralAngle(result['chemSpiderObject'])
            result['amineClass'] = getAmineClass(result['chemSpiderObject'])
            return compoundData

def getAldehdyeInformation(compoundCAS, compoundData):
    """This gets features relevent to the aldehdyes.
    Features:
    Size of ring attached to the aldehdye group.
    Volume substituent on in alpha of nitrogen.
    """
    
    def getRingSize(chemSpiderObject):
        """Calculates the number of carbon atoms in the ring attached to the aldehdye."""

        #getting the carbon position of the aldhdye group
        carbonAldehdyeFragment = Chem.MolFromSmarts('[#6][CX3H1](=O)')
        positionAldehdye = rdchem.Mol.GetSubstructMatches(
            chemSpiderObject, 
            carbonAldehdyeFragment,
            uniquify=True,
            )
        
        carbonPosition = positionAldehdye[0][0]

        #getting ring size of carbon attached to fragment
        ringInfo = chemSpiderObject.GetRingInfo()
        ringSize = (ringInfo.AtomRingSizes(carbonPosition))[0]

        return ringSize
    
    def calcSubstituentVolume(chemspiderobject):
        """Calculates the volume of the substituent on the nitrogen (which adds sterics to the coordination sphere). Returns calculated volume."""

        # Find volume of the substituant in alpha of the nitrogen

        # Getting the position of the carbon alpha nitrogen (the carbon without the aldehyde)
        nitrogenCarbonylFragment = Chem.MolFromSmarts('[#6][nX2][#6][CX3H1](=O)')
        fragmentLocation = rdchem.Mol.GetSubstructMatches(
            chemspiderobject, 
            nitrogenCarbonylFragment,
            uniquify=True,
        )

        # Find neighbours of carbon with bulky group.
        neighbours = chemspiderobject.GetAtomWithIdx(fragmentLocation[0][0]).GetNeighbors()

        # Find neighbours not in the same ring than the carbon
        substituent = []
        ri2 = chemspiderobject.GetRingInfo()
        for n in neighbours:
            # Use position of nitrogen (fragmentLocation[0][1]) for determining 1st ring
            if ri2.AreAtomsInSameRing((fragmentLocation[0][1]), n.GetIdx()) == False:
                substituent.append(n.GetIdx())
                
                neighboursBeta = chemspiderobject.GetAtomWithIdx(n.GetIdx()).GetNeighbors()
                for nB in neighboursBeta:
                    if nB.GetIdx() != (fragmentLocation[0][0]):
                        if ri2.AreAtomsInSameRing((fragmentLocation[0][0]), nB.GetIdx()) == False:
                            substituent.append(nB.GetIdx())

                            neighboursGamma = chemspiderobject.GetAtomWithIdx(nB.GetIdx()).GetNeighbors()
                            for nG in neighboursGamma:
                                if nG.GetIdx() != (n.GetIdx()):
                                    if ri2.AreAtomsInSameRing((nB.GetIdx()), nG.GetIdx()) == False:
                                        substituent.append(nG.GetIdx())
                                        
                                        neighboursDelta = chemspiderobject.GetAtomWithIdx(nG.GetIdx()).GetNeighbors()
                                        for nD in neighboursDelta:
                                            if nD.GetIdx() != (nB.GetIdx()):
                                                if ri2.AreAtomsInSameRing((nG.GetIdx()), nD.GetIdx()) == False:
                                                    substituent.append(nD.GetIdx())

        # list all atoms molecule removes those of the substituent 
        atomsToRemove = []
        for atom in chemspiderobject.GetAtoms():
            if atom.GetIdx() not in substituent:
                atomsToRemove.append(atom.GetIdx())

        # Create the substituent as a fragment of the molecule 

        bulkyFragment = Chem.RWMol(chemspiderobject)
        for atom in sorted(atomsToRemove, reverse=True):
            bulkyFragment.RemoveAtom(atom)

        # Compute the volume of the fragment

        bulkyFragmentVolume = rdchem.ComputeMolVolume(bulkyFragment, confId= -1, gridSpacing=0.2, boxMargin=2.0)
        return bulkyFragmentVolume

    #Searches might have different results, and so must be iterated through.
    for result in compoundData:
        if result['chemicalClass'] == 'Monoaldehdye':                                                #Checking that the reagent is an aldehdye, if not returns the data unedited.
            result['ringSize'] = getRingSize(result['chemSpiderObject'])                             #C
            result['substituentVolume'] = calcSubstituentVolume(result['chemSpiderObject'])          #Calculating the volume of the bulky substituent.
    return compoundData

def getMetalInformation(compoundCAS, compoundData):
    """This gets features relevent to the metals. Unfortunatly I had to type things out manualy"""
    #Searches might have different results, and so must be iterated through.
    for resultIdx, result in enumerate(compoundData):
        if result['chemicalClass'] == 'Metal':                                                #Checking that the reagent is a metal, if not returns the data unedited.
            
            #I had to manualy search up this information
            #Ionic radi information taken from http://abulafia.mt.ic.ac.uk/shannon/ptable.php

            #Iron (II)
            if compoundCAS == '13877-16-2':
                result['metalSize'] = 0.61
                result['metalCharge'] = '+2'
                result['preferredCoordinationGeometry'] = 'octahedral'
                result['molecularWeight'] = 55.845

            #Zinc (II)
            elif compoundCAS == '27860-83-9':
                result['metalSize'] = 0.74
                result['metalCharge'] = '+2'
                result['preferredCoordinationGeometry'] = 'octahedral'
                result['molecularWeight'] = 65.38

            #Yitrium (III)
            elif compoundCAS == '52093-30-8':
                result['metalSize'] = 1.075
                result['metalCharge'] = '+3'
                result['preferredCoordinationGeometry'] = 'tricapped trigonal prism'
                result['molecularWeight'] = 88.9059
            
            #Copper (I)
            elif compoundCAS == '15418-29-8':
                result['metalSize'] = 0.6
                result['metalCharge'] = '+1'
                result['preferredCoordinationGeometry'] = 'tetrahedral'
                result['molecularWeight'] = 63.546

            #Silver (I)
            elif compoundCAS == '14104-20-2':
                result['metalSize'] = 1
                result['metalCharge'] = '+1'
                result['preferredCoordinationGeometry'] = 'tetrahedral'
                result['molecularWeight'] = 107.8682
    return compoundData

def getBasicDetails(compoundCAS, compoundData):
    """Generates a list of dictionaries for each chemspider result in the form: [{rdchem object, Commmon name , molecular formula, smiles, molecular wieght, record id}]
    Returns list."""
    
    cs = ChemSpider("dlQz0DeU9yQWP1J1CtVGBzpsLFkrQxWH")
    
    result = cs.get_details_batch(compoundData, fields=['SMILES', 'CommonName', 'Formula', 'MolecularWeight'])
    featureList = []
    
    #Iterating through results to gain basic reagent info, and their rdchem objects.
    for compound in result:
        featureDictionary = {
            'id': compound['id'],
            'smiles': compound['smiles'],
            'formula': compound['formula'],
            'molecularWeight': compound['molecularWeight'],
            'commonName': compound['commonName'],
            'chemSpiderObject': rdchem.MolFromSmiles(f"{compound['smiles']}")
        }
        featureList.append(featureDictionary)
    
    return featureList

def combineMultipleResults(compoundCAS, compoundData):
    """Some searches return multiple possible results. To finilase the hash table the multiple results are combined into one"""
    #Checking if search has multiple results.

    if len(compoundData) > 1:
        
        combinedFeatures = {}                       #Dictionary is in the form: {'feature': [result1, result2, result 3]}
        
        for resultIdx, result in enumerate(compoundData):
            
            #Iterating through results and adding them to combined features
            for feature in result.keys():
                
                #Checking combined feature exists already, if not create new list for it.
                if feature not in combinedFeatures.keys():
                    combinedFeatures[feature] = []
                
                combinedFeatures[feature].append(result[feature])
            
        #After having placing all the features into the combinedFeatures dictionary, differences must be found.
        
        #The dictionary to replace previous compoundData
        newDictionary = {}

        for feature, featureValues in combinedFeatures.items():
            sameValue = None
            differentValues = []
            for resultFeature in featureValues:

                #Instantiation of sameValue.
                if sameValue == None:
                    sameValue = resultFeature
                
                else:
                    #If the featureValue is the same as the privious it does nothing.
                    if sameValue == resultFeature:                      
                        pass
                    
                    else:
                        differentValues.append(resultFeature)
                        differentValues.append(sameValue)

            #Deciding what to do depending on the differences between the results.
            #This is a very unclean way of doing things. How to deal with differences varies from project to project.

            #If no differences are found, the feature is added to the new dicationary as is 
            if len(differentValues) == 0:
                newDictionary[feature] = sameValue
            
            else:
                #If a features lies within the list, the average between features is taken
                if compoundCAS == '10303-95-4':
                    newDictionary[feature] = differentValues[1]
                
                if compoundCAS == '13877-16-2':
                    newDictionary[feature] = differentValues[1]
                
    
        #Deleting old comopund data and adding the newDictionary
        compoundData.clear()
        compoundData.append(newDictionary)
    return compoundData

def testAllFeaturesDone(compoundCAS, compoundData):
    """This function is to test and process data"""

    metalFeaturesRequired = ['metalSize','metalCharge', 'preferredCoordinationGeometry', 'expectedCoordinationNumber', 'id', 'smiles', 'formula', 'molecularWeight', 'commonName', 'chemSpiderObject', 'chemicalClass', 'morganFingerPrint']
    aldehydeFeaturesRequried = ['ringSize', 'substituentVolume', 'coordinatingNitrogenPartialCharge', 'carbonCarbonylPartialCharge', 'oxygenCarbonylPartialCharge', 'HomoLumoGap', 'id', 'smiles', 'formula', 'molecularWeight', 'commonName', 'chemSpiderObject', 'chemicalClass', 'morganFingerPrint', 'spectrumIR', 'atomCoodinates'] 
    amineFeaturesRequired = ['amineDistance', 'amineRigidity', 'numRotatableBonds', 'amineDihedralAngle', 'numPrimaryAmines', 'numAromaticAmimes', 'amineClass', 'nitrogen1PartialCharge', 'nitrogen2PartialCharge', 'HomoLumoGap', 'id', 'smiles', 'formula', 'molecularWeight', 'commonName', 'chemSpiderObject', 'chemicalClass', 'morganFingerPrint', 'spectrumIR', 'atomCoodinates']
    #Searches might have different results, and so must be iterated through.
    
    for resultIdx, result in enumerate(compoundData):
        
        featureDictionary = {
            'Diamine': amineFeaturesRequired,
            'Monoaldehdye': aldehydeFeaturesRequried,
            'Metal': metalFeaturesRequired
        }

        currentFeatures = result.keys()
        chemicalClass = result['chemicalClass']
        featuresOfInterst = featureDictionary[chemicalClass] 
        for feature in currentFeatures:
            if feature in featuresOfInterst:
                featuresOfInterst.remove(feature)
        
        print(f'The remaing {chemicalClass} features are {featuresOfInterst}')

    # if compoundCAS == '13877-16-2' or compoundCAS == '10303-95-4':
    #     print(compoundData)
    
    return compoundData

def testSingleFeature(compoundCAS, compoundData):
    """This function is to test and process data"""

    metalFeaturesRequired = ['metalSize','metalCharge', 'preferredCoordinationGeometry' 'expectedCoordinationNumber', 'id', 'smiles', 'formula', 'molecularWeight', 'commonName', 'chemSpiderObject', 'chemicalClass', 'morganFingerPrint']
    aldehydeFeaturesRequried = ['ringSize', 'substituentVolume', 'coordinatingNitrogenPartialCharge', 'carbonCarbonylPartialCharge', 'oxygenCarbonylPartialCharge', 'HomoLumoGap', 'id', 'smiles', 'formula', 'molecularWeight', 'commonName', 'chemSpiderObject', 'chemicalClass', 'morganFingerPrint', 'spectrumIR', 'atomCoodinates'] 
    amineFeaturesRequired = ['amineDistance', 'amineRigidity', 'numRotatableBonds', 'amineDihedralAngle', 'numPrimaryAmines', 'numAromaticAmimes', 'amineClass', 'nitrogen1PartialCharge', 'nitrogen2PartialCharge', 'HomoLumoGap', 'id', 'smiles', 'formula', 'molecularWeight', 'commonName', 'chemSpiderObject', 'chemicalClass', 'morganFingerPrint', 'spectrumIR', 'atomCoodinates']

    featureDictionary = {
    'Diamine': amineFeaturesRequired,
    'Monoaldehdye': aldehydeFeaturesRequried,
    'Metal': metalFeaturesRequired
    }

    #Searches might have different results, and so must be iterated through.

    
    chemicalClass = 'Diamine'
    feature = featureDictionary[chemicalClass][3]
    feature = 'amineClass'
    for resultIdx, result in enumerate(compoundData):
        if result['chemicalClass'] == chemicalClass:

            #Getting the literature index of the chemical
            for chemical in chemicals:
                if compoundCAS == chemical.CAS:
                    literatureIdx = reagentFigureIndex[chemical.ID]
            # print(str(literatureIdx) + '    ' + str(result['amineRigidity']) + '    ' + str(result['amineDihedralAngle']) )
            print( str(literatureIdx) + '   ' + feature + '   '+ str(result[feature])) 
            
    return compoundData

def test(compoundCAS, compoundData):
    if compoundCAS == '13877-16-2':
        print(compoundData)
    return compoundData
# A hash table of the reagent CAS number used in the experiment and thier chemSpiderIds. This was done manualy as iterating through searches via python causes HTML request errors to appear.
compoundHashTable = {
    '13877-16-2': [22369399, 23955761],
    '27860-83-9': [13378569],
    '52093-30-8': [2015702],
    '15418-29-8': [9165868],
    '14104-20-2': [140438],
    '34124-14-6': [89131],
    '929-59-9': [63433],
    '2752-17-2': [68482],
    '101-77-9': [7296],
    '1477-55-0': [14404],
    '10303-95-4': [185118, 29367721],
    '15499-84-0': [548388],
    '479-27-6': [61381],
    '101-80-4': [7298],
    '18741-85-0': [19371],
    '1122-72-1': [63902],
    '157402-44-3': [16165424],
    '134296-07-4': [9270418],
    '5470-96-2': [71926],
    '4985-92-6': [8639750],
    '103854-64-4': [1265903],
    '64379-45-9': [1544882],
    '20949-84-2': [2043880],
    '54221-96-4': [13500176],
    '13750-81-7': [123094], 
    '3012-80-4': [666291],
    '13750-68-0': [3470896]
    }

#A hash table that maps the reagents index to their numbers used in the paper.
reagentFigureIndex = {1: None,
                      2: None,
                      3: None,
                      4: None,
                      5: None,
                      6: None,
                      7: None,
                      8: 20,
                      9: 19,
                      10: 22,
                      11: 17,
                      12: 18,
                      13: 16,
                      14: 13,
                      15: None,
                      16: None,
                      17: 21,
                      18: 15,
                      19: None,
                      20: 14,
                      21: 8,
                      22: 2,
                      23: 9,
                      24: 4,
                      25: 3,
                      26: 7,
                      27: 11,
                      28: 1,
                      29: 6,
                      30: 12,
                      31: 5,
                      32: 10}

#Checking if the compoundhashtable has been saved as a pickle. If not, it first gets objects from requests and then saves them as a pickle. This ensure request api is run only once.
picklePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/compoundHashTable.pickle'
if not os.path.exists(picklePath):
    #saving current hashmap as a pickle.
    exportToPickle(compoundHashTable=compoundHashTable, location=picklePath)
    compoundHashTable = mapData(getBasicDetails)
else:
    print('Hashtable already exists')


#Functions must be called in sequenctial order. As some functions depend on data generated by previous functions. 

# mapData(getMoleculeClass)
# mapData(getMorganFingePrint)
# mapData(getAmineInformation)
# mapData(generateXYZFileForGeometryOptimization)
# mapData(prepareXYZFileForOrcaOptimization)
# mapData(optimizeGeometryOrca)
# mapData(extractGeometryOptimizationOrcaFile)
# mapData(generateXYZFilesForHomoLumo)
# mapData(calcualtePointEnergiesOrca)
# mapData(recalculatePointEnergiesOrca)
# mapData(getMetalInformation)
# mapData(getAldehdyeInformation)
# mapData(calculateHomoLumoFromPointEnergiesOrca)
# mapData(combineMultipleResults)
# mapData(testAllFeaturesDone)
# mapData(testSingleFeature)
# mapData(test)

# Creating a dictionary to be used for Emanuele Master Thesis

featuresToBeUsed = ['metalSize', 'ringSize', 'substituentVolume', 'carbonCarbonylPartialCharge', 'amineClass', 'numRotatableBonds', 'amineDihedralAngle']
compoundHasTablePicklePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/compoundHashTable.pickle'
masterCompoundHashTablePicklePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/masterCompoundHashTable.pickle'

if not os.path.exists(masterCompoundHashTablePicklePath):
    
    #The new compound hash table to be used in masters thesis.
    masterCompoundHashTable = {}
    with open(compoundHasTablePicklePath, 'rb') as f:
        compoundHashTable = pickle.load(f)
    
    #iterating through items in compound hashtable and updating the master thesis hash table.
    for compoundKey, compoundValue in compoundHashTable.items():
        data = compoundValue[0]
        masterCompoundHashTable[compoundKey] = {}
        for featureName, featureValue in data.items():
            if featureName in featuresToBeUsed:
                masterCompoundHashTable[compoundKey][featureName] = featureValue

    exportToPickle(compoundHashTable=masterCompoundHashTable, location=masterCompoundHashTablePicklePath)

    for item in masterCompoundHashTable.items():
        print(item)
    

#Iterating through reactions to create the featureDictionary.pickle

featureDictionary = {}
featureDictionaryPicklePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/featureDictionary.pickle'

if not os.path.exists(featureDictionaryPicklePath):
    #Getting the pickle file with all reactions taken
    sampleSpacePath = strCWD + '/ReactionCombinationsWorkflow/GeneratedPickles/SampleSpace.pickle'
    with open(sampleSpacePath, 'rb') as f:
        sampleSpace = pickle.load(f)
    
    print(sampleSpace.takenSamplesSpace)


from playsound import playsound
path = 'C:/Users/emanuele/Desktop/PersonalUse/Programming/doneSound.wav'
# playsound(path)

# C:\Users\emanuele\Desktop\Orca\orca  C:\Users\emanuele\Desktop\PersonalUse\Programming\PythonProjects\UnderstandingOrca\ReruningFailedOptimizations\EnergyOriginalTest\63433.inp > C:\Users\emanuele\Desktop\PersonalUse\Programming\PythonProjects\UnderstandingOrca\ReruningFailedOptimizations\EnergyOriginalTest\63433New.inp
