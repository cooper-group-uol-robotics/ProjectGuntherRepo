"""This script is responsible for the generation of labels for each reaction. 
To do so it first optimizes several parameters for decision maker (this is done via baysian optimization). 
Once decision maker is all set up it then labels the reactions as succesful or not. 
It then takes the previously generated chemical space with relevant features and labels then via decision maker.
 """

#Importing libraries
import pickle
import importlib.util
import sys
import json
import shutil
import os
import matplotlib.pyplot as plt 
import numpy as np
import pandas as pd

#Getting the current working directory.
rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])

#Importing scriptclasses
scriptClasses = strCWD + '/PythonModules/scriptClasses.py'
spec = importlib.util.spec_from_file_location('scriptClasses', scriptClasses)
scriptClasses = importlib.util.module_from_spec(spec)
sys.modules['scriptClasses'] = scriptClasses
spec.loader.exec_module(scriptClasses)

import scriptClasses as sc

#Importing combination workflow parameters
rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])
combinationParametersPath = strCWD + '/ReactionCombinationsworkflow/MainScripts/workflowParameters.py'
spec = importlib.util.spec_from_file_location('combinationParameters', combinationParametersPath)
combinationParameters = importlib.util.module_from_spec(spec)
sys.modules['combinationParameters'] = combinationParameters
spec.loader.exec_module(combinationParameters)

#All parameters that can be optimized

parameters = {
    'peak_number': 3, #3
    'shifted_proportion': 0.5, # 0.5
    'metals_mz': [3,1], #[4,2]
    'dtw_threshold': 20, # 20
    'ppm_range_lower': [11, 3], #[11,3]
    'ppm_range_higher': [1.5, 0], #[1.5, 0] 
    'hg_shift': 0.005, #0.005
    'hg_lb': 1.8, #1.2
    'reference_intensity': 200, #200
    'minimum_intensity': 0.005, # 2 / 1 (1 is preferred)
    'sensitivity':5, #1

}

# peak_number: the allowed difference between the number of peaks in the starting materials and reaction NMR
# shifted_proportion: What proportion of peaks needs to have shifted.
# metals_mz: [x, y] if x metals, required at least y m/z peaks.
# dtw_threshold: Distance threshold for dynamic time warp.
# ppm_range: PPM range of interest
# hg_shift: PPM shift to trigget host-guest identification
# hg_lb: Hz exponential multiplication line broadening
# reference_intensity: no real informtion from bruker
# minimum_intensity: the minimum intensity a peak need to be detected by decision maker
# sensitivity: the sensitivity for peak picking


dataLocations = {
    'startingMaterialsJson': strCWD + '/Data/StartingMaterials/reagentPeaks.json',
    'rawNmrData': strCWD + '/Data/RawData/NmrData',
    'rawMsData': strCWD + '/Data/RawData/MsData/Gunther.PRO/Data',
    'reactionData': strCWD + '/Data/Reactions',
    'startingMaterialsData': strCWD + '/Data/StartingMaterials',
    'expectedMsPeaksData': strCWD + '/Data/expectedMassPeaks.json',
}

"""
These are locations to raw, and parsed data to be feed more esaily into decision maker.
"""


def getFilesOrFolders(searchName:str, location:str):
    """Returns a list of files and names containing the search name"""
    results = []
    ls = os.listdir(location)
    for fileOrFolder in ls:
        if searchName.lower() in fileOrFolder.lower():
            results.append(fileOrFolder)
    return results

def parseRawData(parameters, dataLocations):
    """It takes the raw data and divides it into their relevant folders: strating materials, standard reactions, reactions. Also prepares inputfiles for decision maker on a batch basis."""

    def moveFiles(fileorFolderToCopy:str, newLocation:str):
        """Copys files from raw lcoation to new location. """

        #Checking if file or folder already exists
        if not os.path.exists(newLocation):
            #Checking if file or folder
            if os.path.isfile(fileorFolderToCopy):
                shutil.copyfile(fileorFolderToCopy, newLocation)

            elif os.path.isdir(fileorFolderToCopy):
                shutil.copytree(fileorFolderToCopy, newLocation)

    def parseReactionData(dataLocations):
        """Parses the reaction data form both NMR, MS of reaction and standrad reactions"""

        #The path for the workflow parameters (includes the reagents python objects used in the workflow)
        path = strCWD + '/ReactionCombinationsWorkflow/MainScripts/workflowParameters.py'

        #Updates the workflow parameters
        # sc.USERSELECTION.udpateParameters(path)

        sampleSpacePath = strCWD + '/ReactionCombinationsWorkflow/GeneratedPickles/SampleSpace.pickle'
        with open(sampleSpacePath, 'rb') as f:
            sampleSpace = pickle.load(f)

        #parsing reaction data        
        batches = sampleSpace.takenSamplesSpace

        #Iterating through batches
        
        for batchNumber, batch in enumerate(batches):            
            batchFolder = dataLocations['reactionData'] + '/' + 'batch' + str(batchNumber)
            batchNmrFolder = batchFolder + '/NmrData'
            batchMsFolder = batchFolder + '/MsData'
            batchArchiveFolder = batchFolder + '/ArchiveData'

            #Creating Nmr, Ms, and archive data file for the batch.
            folderToMake = (batchNmrFolder, batchMsFolder, batchArchiveFolder)
            for folder in folderToMake:
                if not os.path.exists(folder):
                    os.makedirs(folder)


            #Transfering the appropiate information for NMR data
            rawNmrpath = dataLocations['rawNmrData']
            
            #finding files with batchX in their name.
            batchName = 'batch' + str(batchNumber)
            fileOrFolder = getFilesOrFolders (batchName, rawNmrpath)

            for pathItem in fileOrFolder:
                fullPathItem = rawNmrpath + '/' + pathItem
                #checking if the search result is a file or folder.
                if os.path.isfile(fullPathItem):
                    #If its a file, this is the json file used to run samples, so can be directly coppied over.
                    filePath = rawNmrpath + '/' + pathItem
                    newFilePath = batchFolder + '/' + pathItem
                    moveFiles(filePath, newFilePath)
                    
                elif os.path.isdir(fullPathItem):
                    #This is the folder with the batch and all the reactions, hence the files in this location need to be copied over.
                    rawBatchNmrpath = rawNmrpath + '/' + pathItem
                    nmrFolder = getFilesOrFolders('batch', rawBatchNmrpath)
                    for pathNmr in nmrFolder:
                        nmrFilePath = rawBatchNmrpath + '/' + pathNmr
                        newNmrFilePath = batchNmrFolder + '/' + pathNmr
                        moveFiles(nmrFilePath, newNmrFilePath)
            
            #Transfering the appropiate information for Ms data
            rawMspath = dataLocations['rawMsData']

            #There are two types of files to copy, the standard reaction and the reactions
            for reaction in batch:
                if type(reaction.unique_identifier) != int:
                    standardReactionIdx = combinationParameters.standardReactionIdx
                    standardReactionPath = str(standardReactionIdx) + 'batch' + str(batchNumber) + '.raw'
                    msFilePath = rawMspath + '/' + standardReactionPath
                    newMsFilePath = batchMsFolder + '/' + standardReactionPath
                    moveFiles(msFilePath, newMsFilePath)

                else:
                    reactionPath = str(reaction.unique_identifier) + '.raw'
                    msFilePath = rawMspath + '/' + reactionPath
                    newMsFilePath = batchMsFolder + '/' + reactionPath
                    moveFiles(msFilePath, newMsFilePath)

    def parseStartingMaterialData(dataLocations):
        """Takes starting reagent spectra and places them in the appropiate files for decision maker""" 
        startingMaterialsNmrFolder = dataLocations['startingMaterialsData'] + '/NmrData'
        startingMaterialsMsFolder = dataLocations['startingMaterialsData'] + '/MsData'
        startingMaterialsArchiveFolder = dataLocations['startingMaterialsData'] + '/ArchiveData'
        
        #Creating Nmr, Ms, and Archive data file for the starting materials.
        folderToMake = (startingMaterialsArchiveFolder, startingMaterialsMsFolder, startingMaterialsNmrFolder)
        for folder in folderToMake:
            if not os.path.exists(folder):
                os.makedirs(folder)
        
        #Transfering the appropiate information for NMR data
        rawNmrpath = dataLocations['rawNmrData']

        #Finding the reagent Nmr file
        reagentName = 'reagentAnalysis'
        fileOrFolder = getFilesOrFolders (reagentName, rawNmrpath)

        #Iterating through searches 
        for pathItem in fileOrFolder:
                fullPathItem = rawNmrpath + '/' + pathItem
                #checking if the search result is a file or folder.
                if os.path.isfile(fullPathItem):
                    #If its a file, this is the json file used to run samples, so can be directly coppied over.
                    filePath = rawNmrpath + '/' + pathItem
                    newFilePath = dataLocations['startingMaterialsData'] + '/' + pathItem
                    moveFiles(filePath, newFilePath)
                    
                elif os.path.isdir(fullPathItem):
                    #This is the folder with the batch and all the reactions, hence the files in this location need to be copied over.
                    reagentNmrFiles = getFilesOrFolders(reagentName, rawNmrpath + '/' + pathItem)
                    for nmrPathItem in reagentNmrFiles:
                        nmrFilePath = fullPathItem +  '/' + nmrPathItem
                        newNmrFilePath =  startingMaterialsNmrFolder + '/' + nmrPathItem
                        moveFiles(nmrFilePath, newNmrFilePath)
        
        #Transfering the appropiate information for Ms data
        rawNmrpath = dataLocations['rawMsData']
        reagentName = 'reagent'
        reagentMsFiles = getFilesOrFolders(reagentName, rawNmrpath)
        
        #Iterating through all the MS files and copying them to reagent ms data to be feed to decision maker
        for msFolderPath in reagentMsFiles:
            msPath = rawNmrpath + '/' + msFolderPath
            newMsPath = startingMaterialsMsFolder + '/' + msFolderPath
            moveFiles(msPath, newMsPath)

    def generateBatchJsonMsInput(dataLocations):
        """Takes in a list of reactions, and returns a json with predicted m/z peaks to be inputted into decision maker. This is done on a batch scope."""
        
        #Loading the dictionary containing all the reactions and their predicted m/z peaks
        jsonPath = dataLocations['expectedMsPeaksData']
        with open(jsonPath) as f:
            expectedMassPeaksDictionary = json.load(f)

        #Finding all the generated batch folders
        reactionBatchPaths = dataLocations['reactionData']
        reagentName = 'batch'
        batchs = getFilesOrFolders(reagentName, reactionBatchPaths)
        for batchFolder in batchs:
            msPaths = reactionBatchPaths + '/' + batchFolder + '/' + 'MsData'

            #The input Json for the decision maker (on a batch scope)
            reagentJson = {}

            #iterating through all the successful Ms Reactions
            msFile = getFilesOrFolders('raw', msPaths)
            for msFilePath in msFile:

                #Checking if its the  standard reaction
                if 'batch' in msFilePath:
                    reactionKey = msFilePath[:-4]
                    standardReactionIdx = combinationParameters.standardReactionIdx + 1 
                    expectedPeaks = expectedMassPeaksDictionary[f'{standardReactionIdx}']
                    reagentJson[reactionKey] = expectedPeaks
                else:
                    #Extracting expected peak form main expected peak file.
                    reactionKey = msFilePath[:-4]
                    expectedPeaks = expectedMassPeaksDictionary[reactionKey]
                    reagentJson[f'{reactionKey}'] = expectedPeaks
                        
            #Saving the expected peak for the batch
            reagentJsonPath = reactionBatchPaths + '/' + batchFolder + '/' + 'expectedMsInputFile.json'
            with open(reagentJsonPath, 'w') as f:
                json.dump(reagentJson, f, indent=4)
            
            #deleting the generated Files untill Jeff gives good one.
            # os.remove(reagentJsonPath)

    
    def generateBatchJsonNmrInput(dataLocations):
        """Generates the NMR input Json to be used by decision maker"""
     
        solvent = combinationParameters.solvent
        nmrExperiments = [combinationParameters.parameters]
        
        #Finding all the generated batch folders
        reactionBatchPaths = dataLocations['reactionData']
        reagentName = 'batch'
        batchs = getFilesOrFolders(reagentName, reactionBatchPaths)
        
        #Getting the sample space.
        sampleSpacePath = strCWD + '/ReactionCombinationsWorkflow/GeneratedPickles/SampleSpace.pickle'
        with open(sampleSpacePath, 'rb') as f:
            sampleSpace = pickle.load(f)

        for batchFolder in batchs:
            nmrPaths = reactionBatchPaths + '/' + batchFolder + '/' + 'NmrData'

            #The input Json for the decision maker (on a batch scope)
            reagentJson = {}
            #Iterating through all the successful Ms Reactions.
            nmrFile = getFilesOrFolders('batch', nmrPaths)
            for nmrFilePath in nmrFile:
                #A simple check so the right file is taken
                batch = int(nmrFilePath[5])
                nmrExperimentNumber = int(nmrFilePath[7:])
                nmrReaction = nmrExperimentNumber + batch * combinationParameters.batchSize
                
                #The first reaction is the standard reaction
                if nmrExperimentNumber == 1:
                    nmrReaction = combinationParameters.standardReactionIdx + 1
                
                #getting the reaction object depending on reaction number
                for reaction in sampleSpace.ReactionSpace.reactionSpace:
                    if reaction.unique_identifier == nmrReaction:
                        
                        #iterating through the reagents of the reaction
                        
                        #Creating the sample info dictionary to be mapped to NMR peak list and starting reagents
                        sampleInfo = {}
                        solvents = []
                        acetonitrileFlag = False
                        dichloromethaneFlag = False
                        for reagent in reaction.reagents:
                            if reagent.__class__.__name__ == 'Diamine':
                                sampleInfo['amine'] = reagent.name
                            elif reagent.__class__.__name__ == 'Monoaldehdye':
                                sampleInfo['aldehyde'] = reagent.name
                            elif reagent.__class__.__name__ == 'Metal':
                                sampleInfo['metal'] =  reagent.name
                            
                            dichloromethane, acetonitrile = reagent.solubility
                            if dichloromethane != 0 and dichloromethaneFlag == False:
                                dichloromethaneFlag = True
                                solvents.append('dichloromethane')
                            if acetonitrile != 0 and acetonitrileFlag == False:
                                acetonitrileFlag = True
                                solvents.append('acetonitrile')

                        reagentJson[nmrFilePath] = {
                            "sample_info": sampleInfo,
                            "solvent": solvents,
                            "nmr_experiments": nmrExperiments
                            }
                        
                        acetonitrileFlag = False
                        dichloromethaneFlag = False

            #Saving the nmrInput json for each batch
            nmrJsonPath = nmrPaths = reactionBatchPaths + '/' + batchFolder + '/nmrInputFile.json'
            with open(nmrJsonPath, 'w') as f:
                json.dump(reagentJson, f, indent=4)

    def generateStartingMaterialsNmrInput(dataLocations):
        """The peaks of the strating materials are needed. This generates the NMR input file to do so."""
        
        reagentNmr = dataLocations['startingMaterialsData'] + '/NmrData'
        
        #getting a list of reagents used in the workflow.
        reagentList = combinationParameters.chemicalsInWholeSpace.copy() 
        for chemical in combinationParameters.chemicalsInWholeSpace:
            for chemicalToRemove in combinationParameters.chemicalsToRemove:
                if chemical.name == chemicalToRemove.name:
                    reagentList.remove(chemical)
        
        #The input Json for the decision maker.
        reagentJson = {}
        
        nmrExperiments = [combinationParameters.parameters]
        nmrPathList = getFilesOrFolders('reagentAnalysis', reagentNmr)
        for nmrPath in nmrPathList:
            reagentIdx = int(nmrPath[-2:])
            
            #Getting the solvents of the reagents (these peaks will have to be removed from the spectra)
            solvents = []

            for chemical in reagentList:
                if chemical.ID == reagentIdx:
                    if chemical.__class__.__name__ == 'Diamine':
                        sampleInfo = {'Amine': chemical.name}
                        
                    elif chemical.__class__.__name__ == 'Metal':
                        sampleInfo = {'Metal': chemical.name}

                    elif chemical.__class__.__name__ == 'Monoaldehdye':
                        sampleInfo = {'Aldehdye': chemical.name}

                                                
                    dichloromethane, acetonitrile = chemical.solubility
                    if dichloromethane != 0:
                        solvents.append('dichloromethane')
                    if acetonitrile != 0:
                        solvents.append('acetonitrile')

                    #Adding in information to json
                    reagentJson[nmrPath] = {
                        'sample_info': sampleInfo,
                        'solvent': solvents,
                        'nmr_experiments': nmrExperiments
                    }

                    acetonitrileFlag = False
                    dichloromethaneFlag = False

            
        #Saving the nmrInput json for each batch
        nmrJsonPath = dataLocations['startingMaterialsData'] + '/nmrInputFile.json'
        with open(nmrJsonPath, 'w') as f:
            json.dump(reagentJson, f, indent=4)

    parseReactionData(dataLocations)
    parseStartingMaterialData(dataLocations)
    generateBatchJsonMsInput(dataLocations)
    generateBatchJsonNmrInput(dataLocations)
    generateStartingMaterialsNmrInput(dataLocations)

def generateToml(parameters):
    """Generates a toml file with user defined parameters to be used in decision maker."""

    #TomlFile
    settings_toml = f'''[dry]

    dry = true

    [tcp]

    HOST      = "tcp://172.31.1.17:5558"
    NMR       = "tcp://172.31.1.15:5552"
    CHEMSPEED = "tcp://172.31.1.16:5553"
    LCMS      = "tcp://172.31.1.18:5554"

    [paths]

    LCMS_archive   = "."    # Path to archive from LCMS PC
    LCMS_queue     = "."    # Path to LCMS queue for MassLynx
    LCMS_data      = "DATA/SUPRAMOL-SCREENING/DATA/LCMS"    # Raw LCMS data on LCMS control PC
    LCMS_to_NMR    = "."    # Path to NMR data from LCMS PC
    NMR_data       = "."    # Raw NMR data on NMR control PC
    NMR_archive    = "."    # Path to archive from NMR PC
    CS_csv_supra   = "."    # CSV on ChemSpeed Computer

    [defaults.NMR]

    num_scans    = 64
    pp_threshold = 0.02
    field_presat = 10
    l30          = 2
    parameters   = "MULTISUPPDC_f"
    solvent      = "CH3CN"
    wait_time    = 120
    shim_time    = 1200
    reshim_time  = 14400
    shim_sample  = 1
    rack_layout  = "KUKA"
    owner        = "Filip T. Szczypinski"
    origin       = "AIC Group, University of Liverpool"

    [defaults.MS]
    injection_volume = 0.5
    peak_match_tolerance = 0.4
    tic_peak_params      = {{ "height" = 0.2, "distance" = 50 }}
    ms_peak_params       = {{ "height" = 0.5, "distance" = 10 }}

    [workflows.PREFIX]

    Supramol_Screening   = "SUPRAMOL-SCREENING"
    Supramol_Replication = "SUPRAMOL-REPLICATION"
    Supramol_HostGuest   = "SUPRAMOL-HOST-GUEST"

    [workflows.NMR]

    Supramol_Screening   = "synthesis_bots.workflows.nmr.supramol.screening"
    Supramol_Replication = "synthesis_bots.workflows.nmr.supramol.replication"
    Supramol_HostGuest   = "synthesis_bots.workflows.nmr.supramol.host_guest"

    [workflows.LCMS]

    InsertRack1  = "synthesis_bots.workflows.ms.insert_rack_one"
    InsertRack2  = "synthesis_bots.workflows.ms.insert_rack_two"
    ExtractRack1 = "synthesis_bots.workflows.ms.eject_rack_one"
    ExtractRack2 = "synthesis_bots.workflows.ms.eject_rack_two"
    Supra1       = "synthesis_bots.workflows.ms.supramol.screening"
    Supra2       = "synthesis_bots.workflows.ms.supramol.replication"

    [workflows.decision]

    peak_number = {parameters['peak_number']}
    shifted_proportion = {parameters['shifted_proportion']} # What proportion of peaks needs to have shifted.
    metals_mz =  {parameters['metals_mz']} # [x, y] if x metals, required at least y m/z peaks.
    dtw_threshold = {parameters['dtw_threshold']} # Distance threshold for dynamic time warp.
    ppm_range_lower = {parameters['ppm_range_lower']} # Lower PPM range of interest
    ppm_range_higher = {parameters['ppm_range_higher']} # Upper PPM range of interest    
    hg_shift = {parameters['hg_shift']} # PPM shift to trigget host-guest identification
    hg_lb = {parameters['hg_lb']} # Hz exponential multiplication line broadening

    '''

    tomlLocation = strCWD + '/Data/settings.toml'
    with open(tomlLocation, "w") as f:
        f.write(settings_toml)

def pickPeaks(parameters, experimentName, nmrExperiment, nmrFilePath, saveFig, figureFolderPath=None, displayFigure=False, intensity_region=(10, 6), overwriteExistingFigure=False):
    """Function peaks pickes of the given NMR file path. Return a list of peaks"""
    #Importing synthesis_bots.utils.nmr.processing
    nmrProcessingPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/dependencies/modules/synthesis_bots/utils/nmr/processing.py'
    spec = importlib.util.spec_from_file_location('nmrProcessing', nmrProcessingPath)
    nmrProcessing = importlib.util.module_from_spec(spec)
    sys.modules['nmrProcessing'] = nmrProcessing
    spec.loader.exec_module(nmrProcessing)

    #Importing synthesis_bots.utils.nmr.acquisition
    nmrAcquisitionPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/dependencies/modules/synthesis_bots/utils/nmr/acquisition.py'
    spec = importlib.util.spec_from_file_location('nmrAcquisition', nmrAcquisitionPath)
    nmrAcquisition = importlib.util.module_from_spec(spec)
    sys.modules['nmrAcquisition'] = nmrAcquisition
    spec.loader.exec_module(nmrAcquisition)

    nmr = nmrProcessing.NMRExperiment(nmrAcquisition.FOURIER.open_experiment(nmrFilePath))

    # nmr.process_spectrum(zero_filling="8k", line_broadening=1.2, reference=True)

    minPpm = max(parameters['ppm_range_lower'])
    maxPpm = min(parameters['ppm_range_higher'])

    #aquiring peaks
    peaksPpm = nmr.pick_peaks(
                reference_intensity=parameters['reference_intensity'],
                minimum_intensity=parameters['minimum_intensity'],
                sensitivity=parameters['sensitivity'],
                ppm_range=[minPpm, maxPpm],
            )

    #If the smaple contains dichloromethane, the peak closest to 5.44ppm will be removed http://ccc.chem.pitt.edu/wipf/Web/NMR_Impurities.pdf
    if 'dichloromethane' in nmrExperiment["solvent"]:    
        dcmPeak = 5.44
        closestPeak = min(peaksPpm, key=lambda x:abs(x-dcmPeak))
        peaksPpm.remove(closestPeak)

    
    #Removing values that are not in the wanted ppm_range lowerMinPpm<x<lowermaxPpm and higherMinPpm<x<higherMaxPpm
    lowerMinPpm = max(parameters['ppm_range_lower'])
    lowerMaxPpm = min(parameters['ppm_range_lower'])
    higherMinPpm = max(parameters['ppm_range_higher'])
    higherMaxPpm = min(parameters['ppm_range_higher'])

    filteredPeaksPpm = []
    for peak in peaksPpm:
        if lowerMinPpm >= peak and lowerMaxPpm <= peak:
            filteredPeaksPpm.append(peak)
        elif higherMinPpm >= peak and higherMaxPpm <= peak:
            filteredPeaksPpm.append(peak)

    
    print(filteredPeaksPpm)
    
    #saving the process NMR spectra as images and dx files
    if saveFig:
        #plotting the NMR
        fig, _ = nmr.plot_nmr(region=(minPpm, maxPpm))

        #Saving the nmr in the indicated path
        if os.path.exists(figureFolderPath):
            fig, _ = nmr.plot_nmr(region=(10.5, -0.5), intensity_region=intensity_region)
            pngPath = figureFolderPath + '/NMR' + experimentName + '.png'
            svgPath = figureFolderPath + '/NMR' + experimentName + '.svg'
            dxPath = figureFolderPath + '/NMR' + experimentName + '.dx'
            
            if not overwriteExistingFigure:
                #saving png
                if not os.path.exists(pngPath):
                    fig.savefig(pngPath, dpi=600)
                
                #saving svg.
                if not os.path.exists(svgPath):
                    fig.savefig(svgPath)
                
                #Saving .dx spectra.
                if not os.path.exists(dxPath):
                    nmr.export_jcampdx(export_path = dxPath, export_all=False)
            
            elif overwriteExistingFigure:
                fig.savefig(pngPath, dpi=600)
                fig.savefig(svgPath)
                nmr.export_jcampdx(export_path = dxPath, export_all=False)

        if displayFigure == True:
            plt.show()
            


    return filteredPeaksPpm

def singleNmrDecision(parameters, dataLocations, startingMaterialsSpectra, experimentName, nmrExperiment, nmrFilePath, saveFig, figureFolderPath=None):
    """Takes the NMR peaks, takes the reagent peaks, and compares them. If a criteria is failed, it returns what criteria has failed. If all criteria is good, its successful."""

    def compareLists(reaction_peaks: list[float], reagents_list: list[list[float]],) -> bool:
        """Function compares reaction peaks with reagent peaks. The orginal function was adapted from the original decision maker (different_from_reagents.py)"""
        
        from dependencies.modules.synthesis_bots.utils.constants import SETTINGS
        from itertools import chain

        criteria = SETTINGS["workflows"]["decision"]
        reagents_peaks = list(set(chain(*reagents_list)))
        
        #These will be used to create decision tuple (if criteria 1 passed, the difference between reagent and reaction peaks, if criteria 2 passed, what percentage of peaks shifted position, label).
        criteria1Pass = 0
        criteria1PeakDifference = None
        criteria2Pass = 0
        criteria2PercetangeShifted = None
        label = 0

        # Check if there are too many or too few peaks.
        if (diff := abs(len(reagents_peaks) - len(reaction_peaks))) > criteria["peak_number"]:
            criteria1Pass = 0
            criteria1PeakDifference = diff
        
        else:
            diff = abs(len(reagents_peaks) - len(reaction_peaks))
            criteria1Pass = 1
            criteria1PeakDifference = diff            
        
        # Check if peaks have shifted in values.
        reaction_set = {round(x, 2) for x in reaction_peaks}

        for peak in reagents_peaks:
            reaction_set.discard(round(peak, 2))

        if len(reaction_set) < 0.5 * len(reagents_peaks):
            criteria2Pass = 0
            #checking to see if denominator not 0
            if len(reaction_peaks) == 0:
                criteria2PercetangeShifted = 0
            else:    
                criteria2PercetangeShifted = len(reaction_set) / len(reaction_peaks)              
        
        else:
            criteria2Pass = 1
            #checking to see if denominator not 0
            if len(reaction_peaks) == 0:
                criteria2PercetangeShifted = 0
            else:    
                criteria2PercetangeShifted = len(reaction_set) / len(reaction_peaks)

        #Labelling the reaction as succesful or not based on the two criteria
        if criteria1Pass == 1 and criteria2Pass == 1:
            label  = 1

        #Creating the decision tuple and returning it.
        nmrDecisionDictionary = {
            'criteria1_pass': criteria1Pass,
            'criteria2_pass': criteria2Pass,
            'criteria1_peak_difference': criteria1PeakDifference,
            'criteria2_percentage_shifted': criteria2PercetangeShifted,
            'label': label
        }        
        return nmrDecisionDictionary


    #Getting the Reaction Nmr Peaks
    reactionPeaks = pickPeaks(parameters, experimentName, nmrExperiment, nmrFilePath, saveFig, figureFolderPath)
    
    #Getting the reagent peaks
    metalInReaction = nmrExperiment['sample_info']['metal']
    aldehydeInReaction = nmrExperiment['sample_info']['aldehyde']
    amineInReaction = nmrExperiment['sample_info']['amine']

    startingAldehdyePeaks = startingMaterialsSpectra[aldehydeInReaction]['peaks_ppm']
    staringAminePeaks = startingMaterialsSpectra[amineInReaction]['peaks_ppm']
    stratingMaterialsPeaks = [staringAminePeaks, startingAldehdyePeaks]

    # print(staringAminePeaks)
    # print(startingAldehdyePeaks)
    # print(reactionPeaks)

    nmrDecisionDictionary = compareLists(reactionPeaks, stratingMaterialsPeaks)
    nmrDecisionDictionary['peaks_ppm'] = reactionPeaks
    nmrDecisionDictionary['sample_info'] = {
        "amine": metalInReaction,
        "aldehyde": aldehydeInReaction,
        "metal": metalInReaction,
    }

    return nmrDecisionDictionary

def compareDecisionMakerToHumanLables(parameters, dataLocations, batchPath: str):
    """Decision maker lables the reaction as successful or not. Human and decision maker labels are then compared.
    input: the path to the batch with all spectra data
    output: a list of human and decision maker lables for all reactions in batch"""

    #Importing synthesis_bots.utils.nmr.processing
    nmrProcessingPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/dependencies/modules/synthesis_bots/utils/nmr/processing.py'
    spec = importlib.util.spec_from_file_location('nmrProcessing', nmrProcessingPath)
    nmrProcessing = importlib.util.module_from_spec(spec)
    sys.modules['nmrProcessing'] = nmrProcessing
    spec.loader.exec_module(nmrProcessing)

    #Importing synthesis_bots.utils.nmr.acquisition
    nmrAcquisitionPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/dependencies/modules/synthesis_bots/utils/nmr/acquisition.py'
    spec = importlib.util.spec_from_file_location('nmrAcquisition', nmrAcquisitionPath)
    nmrAcquisition = importlib.util.module_from_spec(spec)
    sys.modules['nmrAcquisition'] = nmrAcquisition
    spec.loader.exec_module(nmrAcquisition)

    #Loading the starting materials nmr peaks
    with open(dataLocations['startingMaterialsJson']) as f:
        startingMaterialsJson = json.load(f)
    
    #Loading the nmr experiments
    nmrExperimentsPath = batchPath + '/nmrInputFile.json'
    with open(nmrExperimentsPath) as f:
        nmrExperiments = json.load(f)

    #Loading the human lables.
    humanLabelsPath = batchPath + '/humanLabel.json'
    with open(humanLabelsPath) as f:
        humanLabels = json.load(f)

    #getting all the NMR spectra of the batch.
    nmrFilesPath = batchPath + '/NmrData'
    decisionMakerLabelJson = {}
    keyword = 'batch'
    nmrDataFolder = getFilesOrFolders(keyword, nmrFilesPath)

    decisionMakerLabelPath =  batchPath + '/decisionMakerLabel.json'
    
    #checking that decision maker labels have not already been generated.

    if not os.path.exists(decisionMakerLabelPath):
        #Iterating through the NMR spectras in the batch, labeling with decision maker, and then comparing with human lables
        for spectra in nmrDataFolder:
            fullSpectraPath = nmrFilesPath + '/' + spectra
            nmr = nmrProcessing.NMRExperiment(nmrAcquisition.FOURIER.open_experiment(fullSpectraPath))
            nmrExperiment = nmrExperiments[f'{spectra}']
            reagentPeaks = pickPeaks(parameters=parameters, 
                                        experimentName=spectra, 
                                        nmrExperiment=nmrExperiment,
                                        nmrFilePath=fullSpectraPath,
                                        saveFig=False)
            
            #Inputting nmr to decision maker
            decisionMakerOutput = singleNmrDecision(parameters, dataLocations, startingMaterialsJson, spectra, nmrExperiments[spectra], fullSpectraPath, saveFig=False)
            
            #Updating the decisionMakerLabel json
            decisionMakerLabelJson[spectra] = decisionMakerOutput
            
        #saving the decisionMakerLabel.json (this just palceholder for now)
        with open(decisionMakerLabelPath, 'w') as f:
            json.dump(decisionMakerLabelJson, f, indent=4)
        
    #Comparing human to decision maker labels
    
    #Loading decision maker labels
    with open(decisionMakerLabelPath) as f:
            decisionMakerLabels = json.load(f)

    #keeping track of error
    errorTrue = 0
    errorTrueSize = 0 
    errorFalse = 0
    errorFalseSize = 0

    #Iterating through spectra to compare labels
    for spectra in nmrDataFolder:
        #Getting the human label
        humanLabel = humanLabels[spectra]['label']
        if humanLabel != 1:
            humanLabel = 0

        #Getting the decision maker label
        decisionMakerLabel = decisionMakerLabels[spectra]['label']

        print(humanLabel, decisionMakerLabel)

        #Getting errors 
        
        #Updating true errors (what the human predicted to be right)
        if humanLabel == 1:
            errorTrueSize += 1 
            if humanLabel != decisionMakerLabel:
                errorTrue += 1

        #Updating False errors (what the human predicted to be false)
        elif humanLabel == 0:
            errorFalseSize += 1
            if humanLabel != decisionMakerLabel:
                errorFalse += 1
                
    SuccessLabelAccuracy = ((errorTrueSize-errorTrue) / errorTrueSize)
    FailedLabelAccuracy = ((errorFalseSize-errorFalse) / errorFalseSize)
        
    print(f'Accuracy prediction for successful labels {SuccessLabelAccuracy}')
    print(f'Accuracy prediction for failed labels {FailedLabelAccuracy}')

def singleMsDecision(parameters:dict, dataLocations:dict, experimentName:str, msExperiment:dict, msFile:str, saveFig:bool, figureFolderPath=None, displayFigure=False):
    """This makes a decision on one ms experiment, and out puts the decision tuple (criteria 1 passed, how criteria 1 passed or failed, criteria 2 passed, how criteria two passed or fialed, the label for this reaction).
    parameters = a dictionary of parameters used for the workflow
    datalocationns = a dictionary of common file locations
    experimentName = the name of the experiement to be saved in the json
    msExperiment = information on the Ms experiment (namly predicted peaks)
    msFile = the location of the Ms spectra to be read
    saveFig = if a figure should be saved or not
    figureFolderPath = where the figure should be saved"""
    
    from datetime import timedelta
    from dependencies.modules.synthesis_bots.workflows.ms.supramol import screening
    from dependencies.modules.lcms_parser import ExpectedResults
    from dependencies.modules.synthesis_bots.utils.ms.plot import plot_ms    
    from dependencies.modules.synthesis_bots.utils.constants import SETTINGS
    from pathlib import Path
    from dependencies.modules.lcms_parser import (
        ExpectedResults,
        MassSpectrumExperimentalHit,
        WatersRawFile,
    )
    def translateMassSpectrumExperimentalHitToDictionary(MassSpectrumExperimentalHit: MassSpectrumExperimentalHit=None):
        """Translates the MassSpectrumExperimentalHit object into a dictionary."""

        #The information we are looking to take
        mz_value = MassSpectrumExperimentalHit.mz_value
        mode = MassSpectrumExperimentalHit.mode
        formula = MassSpectrumExperimentalHit.formula
        charge = MassSpectrumExperimentalHit.charge
        mz_expected = MassSpectrumExperimentalHit.mz_expected
        time = MassSpectrumExperimentalHit.time

        #The dictionary to return.
        hitDictionary = {}

        #Adding information to the hitDictoinary.
        hitDictionary['mz_value'] = mz_value
        hitDictionary['mode'] = mode
        hitDictionary['formula'] = formula
        hitDictionary['charge'] = charge
        hitDictionary['mz_expected'] = mz_expected
        hitDictionary['time'] = time

        return hitDictionary

    def compareMs(
            raw_path: str,
            expected_mz: ExpectedResults,
        ) -> tuple[bool, list[MassSpectrumExperimentalHit]]:
        """Make the decisions. Adapted from original decision maker (expected_mass_metals.py). Returns a decision Tuple """
        
        criteria1and2Pass = 0
        criteria1and2NumberOfHits = 0
        criteria3Pass = 0
        criteria3MetalHits = 0
        label = 0
   
        criteria = SETTINGS["workflows"]["decision"]
        ms_file = WatersRawFile(raw_path)
        hits = ms_file.identify_hits(
            expected_results=expected_mz,
            mode="ES+",
            atol=SETTINGS["defaults"]["MS"]["peak_match_tolerance"],
            tic_peak_params=SETTINGS["defaults"]["MS"]["tic_peak_params"],
            ms_peak_params=SETTINGS["defaults"]["MS"]["ms_peak_params"],
        )

        criteria1and2NumberOfHits = len(hits)
        
        #Checking if any hits have been found between predicted and Ms Spectra.
        if len(hits)>0:
            criteria1and2Pass = 1
        
        #Checking for multiple metals in the hits.

        multiple_metals = {hit.formula: 0 for hit in hits}

        for hit in hits:
            metals_no = int(hit.formula.split("_")[1][1])
            if metals_no >= criteria["metals_mz"][0]:
                multiple_metals[hit.formula] += 1

        pruned_hits = []
        criteria3MetalHits = 0
        for hit in hits:
            metals_no = int(hit.formula.split("_")[1][1])
            if metals_no >= criteria["metals_mz"][0]:
                if multiple_metals[hit.formula] >= criteria["metals_mz"][1]:
                    translatedhit = translateMassSpectrumExperimentalHitToDictionary(hit)
                    pruned_hits.append(translatedhit)
                    criteria3Pass = 1
                    criteria3MetalHits += 1
                else:
                    pass
            else:
                translatedhit = translateMassSpectrumExperimentalHitToDictionary(hit)
                pruned_hits.append(translatedhit)

        if len(pruned_hits) > 0:
            label = 1

        msDecisionDictionary = {
            'criteria1and2_pass': criteria1and2Pass,
            'criteria3_pass': criteria3Pass,
            'criteria1and2_number_of_hits': criteria1and2NumberOfHits,
            'criteria3_number_of_ions_hits': criteria3MetalHits,
            'label': label,
            'mz_peaks': pruned_hits
        }
        return msDecisionDictionary
    
    #Converting the msExperiment to something interpretable by decision maker.
    msExperiment = ExpectedResults.from_dict(msExperiment)
    
    #Comparing expected mass peaks to the spectra.
    msDecisionDictionary = compareMs(msFile, msExperiment)

    #Plot of the MS spectra
    fig, _ = plot_ms(raw_path=(Path(msFile)))

    #Saving the ms spectra in the indicated path
    if saveFig:
        if os.path.exists(figureFolderPath):

            pngPath = figureFolderPath + '/MS' + experimentName + '.png'
            svgPath = figureFolderPath + '/MS' + experimentName + '.svg'
            
            #saving png
            if not os.path.exists(pngPath):
                fig.savefig(pngPath, dpi=600)
            
            #saving svg.
            if not os.path.exists(svgPath):
                fig.savefig(svgPath)

    #Displaying the plot
    if displayFigure:
        plt.show()

    return msDecisionDictionary

def decisionMakerBatchPass(parameters, datalocations, batchPath):
    """Takes in the Ms, NMR spectra of a batch, and labels the reaction as succesfull or not based on decision maker"""

    def getNewNmrName(nmrFileName, batchPath):
        """Returns the ms equivilant of a ms experiement name.
        Typical ms names look like: '23batch3.raw', '105.raw'
        Typical nmr names look like: 'batch2-02', 'batch3-01'"""
        
        batchNumber, nmrSampleNumber = nmrFileName[5:].split("-")
        
        #checking if the reaction is the standard reaction
        if int(nmrSampleNumber) == 1:
            standardReactionNumber = str(combinationParameters.standardReactionIdx) 
            newFileName = standardReactionNumber + 'batch' + batchNumber
        else:
            #Calculting the reaction number
            batchSize = combinationParameters.batchSize
            reactionNumber = (int(batchNumber))*(batchSize-1) + (int(nmrSampleNumber)-1)
            newFileName = reactionNumber
        
        return str(newFileName)
        

    #Firstly taking all NMR and MS decisions on a batch basis
    
    #Taking nmr decisions
        
    #Loading NMR experiments
    nmrExperimentsJsonPath = batchPath + '/nmrInputFile.json'
    with open(nmrExperimentsJsonPath) as f:
        nmrExperimentsJson = json.load(f)

    #Loading starting Materials spectra
    with open(dataLocations['startingMaterialsJson']) as f:
        startingMaterialsPeaks = json.load(f)
    
    #Dictionary with all NMR decisions
    nmrDecisions = {}

    nmrData = batchPath + '/NmrData'
    keyWord = 'batch'
    nmrSpectra = getFilesOrFolders(keyWord, nmrData)

    #Iterating through spectra and putting them through decision maker
    for spectra in nmrSpectra:
        nmrExperimentName = spectra
        nmrExperiment = nmrExperimentsJson[spectra]
        nmrFilePath = nmrData + '/' + spectra
        nmrFigureFolderPath = batchPath + '/ArchiveData'
        
        #Taking decision
        nmrDecision = singleNmrDecision(parameters=parameters, 
                                        dataLocations=dataLocations, 
                                        startingMaterialsSpectra=startingMaterialsPeaks, 
                                        experimentName=nmrExperimentName,
                                        nmrExperiment=nmrExperiment, 
                                        nmrFilePath=nmrFilePath,
                                        figureFolderPath=nmrFigureFolderPath,
                                        saveFig=True)

        #Adding decision to nmrDecisions

        #changing nmrNames to something compatible with msNames
        newNmrExperimentName = getNewNmrName(spectra, batchPath)
        nmrDecisions[newNmrExperimentName] = nmrDecision
    
    #Taking Ms decisions

    #Loading predicted masses
    expectedMsPeaksPath = batchPath + '/expectedMsInputFile.json'
    with open(expectedMsPeaksPath) as f:
        expectedMsPeaks = json.load(f)

    #Dictionary with all Ms decisions
    msDecisions = {}

    msData = batchPath + '/MsData'
    msSpectra = os.listdir(msData)

    #Iterating through spectra and putting them through decision maker.
    for spectra in msSpectra:
        msExperimentName = spectra[:-4]
        msExperiment = expectedMsPeaks[msExperimentName]
        msFile = msData + '/' + spectra
        msFigureFolder = batchPath + '/ArchiveData'
        
        #Taking decision
        msDecision = singleMsDecision(parameters=parameters,
                                    dataLocations=dataLocations,
                                    experimentName=msExperimentName,
                                    msExperiment=msExperiment,
                                    msFile=msFile,
                                    figureFolderPath=msFigureFolder,
                                    saveFig=True)
        
        #Adding decision to msDecision                
        msDecisions[msExperimentName] = msDecision

    #Creating a dictionary with all decisions from both nmr and ms spectra. This is the json to be saved.
    allDecisions = {}
    
    nmrExperiments = nmrDecisions.keys()
    msExperiments = msDecisions.keys()

    #Iterating through nmr and Ms decisions to come up with the label of the reaction    
    for reaction in nmrExperiments:
        
        #Checking that the NMR experiment has a Ms equivilant.
        if reaction in msExperiments:
            reactionLabel = 0
            nmrDecision = nmrDecisions[reaction]
            msDecision = msDecisions[reaction]
            nmrLabel = nmrDecision['label']
            msLabel = msDecision['label']
            
            #getting the label of the reaction
            if nmrLabel == 1 and msLabel == 1:
                reactionLabel = 1 

            #Updating allDecisions
            allDecisions[reaction] = {
                'nmr_decision': nmrDecision,
                'ms_decision': msDecision,
                'reaction_label': reactionLabel
            }
        
        else:
            print(reaction)

    #saving the allDecisions as a json
    allDecisionsPath = batchPath + '/decisions.json'
    with open(allDecisionsPath, 'w') as f:
            json.dump(allDecisions , f, indent=4)

    #saving the nmrDecisions as a json
    nmrDecisionsPath = batchPath + '/nmrdecisions.json'
    with open(nmrDecisionsPath, 'w') as f:
            json.dump(nmrDecisions , f, indent=4)

    #saving the nmrDecisions as a json
    msDecisionsPath = batchPath + '/msdecisions.json'
    with open(msDecisionsPath, 'w') as f:
            json.dump(msDecisions , f, indent=4)

def fullMsDecision(parameters:dict, dataLocations:dict) -> dict[str: int]:
    "Runs through the MS data of all batchs based on the inputted parameters and retruns the decision preformance as a dictionary."
    
    def getReactionID(spectra:str):
        "returns the reaction ID to then be looked up in the expectedMsPeaks dicionary"
        
        spectraName = spectra[:-4]
        if 'batch' in spectraName:
            spectraName = str(combinationParameters.standardReactionIdx + 1)
    
        return spectraName
    
    #Saving toml with parameters
    generateToml(parameters=parameters)

    #Path to files containing batch reaction data.
    dataPath = strCWD + '/Data'
    batchDataPath = dataPath + '/Reactions'
    
    #Loading predicted masses
    expectedMsPeaksPath = dataPath + '/expectedMassPeaks.json'
    with open(expectedMsPeaksPath) as f:
        expectedMsPeaks = json.load(f)
    
    msOptimization = {}

    # A dictionary with hits and decisions for a set of parameters {'numHit': int,'parameters': parameter dictionary, 'msOutCome':MsOutcome dictionary}
    optimizationRun = {}

    #Dictoinary with decision outcomes {'batch': {'spectra': {0,1}}}
    msOutCome = {}
    batchPaths = os.listdir(batchDataPath) 
    numHit = 0
    totalSamples = 0
    for batch in batchPaths:
        msSpectraPath = batchDataPath + '/' + batch + '/MsData' 
        msSpectras = os.listdir(msSpectraPath)
        batchMsOutCome = {}
        for spectra in msSpectras:
            msExperimentName = getReactionID(spectra=spectra)
            msExperiment = expectedMsPeaks[msExperimentName]
            msFile = msSpectraPath + '/' + spectra
            
            msDecision = singleMsDecision(parameters=parameters,
                                          dataLocations=dataLocations,
                                          experimentName=msExperimentName, 
                                          msExperiment=msExperiment,
                                          msFile=msFile,
                                          saveFig=False)
            
            msSpectraLable = msDecision
            if str(msSpectraLable['label']) == str(1):
                numHit += 1
            if 'batch' not in spectra: 
                totalSamples +=1
            batchMsOutCome[spectra] = msSpectraLable
        msOutCome[batch] = batchMsOutCome
    optimizationRun['numHit'] = numHit
    optimizationRun['parameters'] = parameters
    optimizationRun['batchMsOutcome'] = msOutCome
    print(f'The total number of MS smaples is {totalSamples}')
    return optimizationRun

def optimizeMSParameters(dataLocations, parameterID):
    """Iterates through different MS parameters to maximise the number of MS hits by decision maker. Unfortunaly it has to be run manualy, cuase parameters dont change when called by python."""

    parametersList = []

    for metalCount in range(0,11):
        for peakCount in range(0,11):
            parameter = {
                'peak_number': 3, #3
                'shifted_proportion': 0.5, # 0.5
                'metals_mz': [metalCount,peakCount], # [3,2]
                'dtw_threshold': 20, # 20
                'ppm_range_lower': [11, 3], #[11,3]
                'ppm_range_higher': [1.5, 0], #[1.5, 0] 
                'hg_shift': 0.005, #0.005
                'hg_lb': 1.8, #1.2
                'reference_intensity': 200, #200
                'minimum_intensity': 0.005, # 2 / 1 (1 is preferred)
                'sensitivity':5, #1
                }
            parametersList.append(parameter)

    #Opening the previous parameters file
    msParametersOptimizationRunsPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/decisionMakerParameterOptimization/msParametersOptimizationRuns.pickle'
    
    if os.path.exists(msParametersOptimizationRunsPath):
        with open(msParametersOptimizationRunsPath, 'rb') as f:
            parameterOptimization = pickle.load(f)
    else:
        parameterOptimization = {}

    parameter = parametersList[parameterID]
    optimizationRun = fullMsDecision(parameters=parameter, dataLocations=dataLocations)
    optimizationRunName = 'optimization' + str(parameterID)
    parameterOptimization[optimizationRunName] = optimizationRun
    print(parameterID, parameter['metals_mz'], optimizationRun['numHit'])

    with open(msParametersOptimizationRunsPath, 'wb') as pickleFile:
            pickle.dump(parameterOptimization, pickleFile)

def optimizeMSParametersSingleRun(dataLocations, parameterId):
    """Iterates through different MS parameters to maximise the number of MS hits by decision maker."""

    standardParameters = {
    'peak_number': 3, #3
    'shifted_proportion': 0.5, # 0.5
    'metals_mz': [0,2], # [3,2]
    'dtw_threshold': 20, # 20
    'ppm_range_lower': [11, 3], #[11,3]
    'ppm_range_higher': [1.5, 0], #[1.5, 0] 
    'hg_shift': 0.005, #0.005
    'hg_lb': 1.8, #1.2
    'reference_intensity': 200, #200
    'minimum_intensity': 0.005, # 2 / 1 (1 is preferred)
    'sensitivity':5, #1
    }

    parameterOptimization = {}

    #Testing out different parameters
    run = 0
    optimizationRun = fullMsDecision(parameters=standardParameters, dataLocations=dataLocations)
    optimizationRunName = 'optimization' + str(run)
    parameterOptimization[optimizationRunName] = optimizationRun
    print(run, standardParameters['metals_mz'], optimizationRun['numHit'])
    run += 1

    msParametersOptimizationRunsPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/decisionMakerParameterOptimization/msParametersOptimizationSingleRun.pickle'
    with open(msParametersOptimizationRunsPath, 'wb') as pickleFile:
            pickle.dump(parameterOptimization, pickleFile)

def analyseMsParametersData(plot=False):
    """Analysing data from MS parameter optimization."""

    from typing import List
    import pandas as pd
    import numpy as np
    import seaborn as sns
    import matplotlib.pyplot as plt
    import umap
    from sklearn.manifold import TSNE

    #chemicalsInWholeSpace is a list of chemicals the chemspeed platform can handle. chemicalsToRemove are chemicals that are not part of the combination libraries.
    chemicalsInWholeSpace = combinationParameters.chemicalsInWholeSpace                                                                                         
    chemicalsToRemove = combinationParameters.chemicalsToRemove
    reagentSpace = chemicalsInWholeSpace.copy()

    #Removing chemicals that are not part of the combianation libraries (no reactions contain these chemicals).
    for chemical in chemicalsToRemove:
        for wholeChemical in chemicalsInWholeSpace:
            if chemical.name == wholeChemical.name:
                reagentSpace.remove(wholeChemical)

    #Getting the feature reagent hash table.
    featureHashTablePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/compoundHashTableUNEDITED13.pickle'
    with open(featureHashTablePath, 'rb') as f:
            featureHashTable = pickle.load(f)

    #Getting the feature reagent hash table for masters project.
    featureHashTablePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/masterCompoundHashTable.pickle'
    with open(featureHashTablePath, 'rb') as f:
            featureHashTableMaster = pickle.load(f)

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


    def getReaction(reactionID:int):
        """Returns a reaction object based on the reactionId"""
          
        #Getting the reactionSpace
        sampleSpacePath = strCWD + '/ReactionCombinationsWorkflow/GeneratedPickles/SampleSpace.pickle'
        with open(sampleSpacePath, 'rb') as f:
            sampleSpace = pickle.load(f)
        reactionSpace = sampleSpace.ReactionSpace.reactionSpace

        for reaction in reactionSpace:
            if reaction.unique_identifier == reactionID:
                return reaction

    def getRatio(mzPeaks: str):
        """Returns the ratio between metal, aldehdye and amine"""
        molecularFormulaList = [] 
        for peak in mzPeaks:
            formula = peak['formula']
            formulaSplit = formula.split('_')
            noMetal = formulaSplit[1][1:-1]
            noCarbonyl = formulaSplit[3][1:-1]
            noAmine = formulaSplit[5][1:-1]
            ratio = {
                'noMetal': noMetal,
                'noCarbonyl': noCarbonyl,
                'noAmine': noAmine
            }
            molecularFormulaList.append(ratio)
        return molecularFormulaList

    def computeEcfpDescriptors(reagentObject):
        """returns the ECFP descriptors (these are just morgan fingerprints)"""
        return featureHashTable[reagentObject.CAS][0]['morganFingerPrint']

    def categoriseAmineClass(amineClass):
        """Returns the class of the amine as a numerical value"""
        for classification, numerical in zip (["alkyl and aromatic amine", "alkyl amine", "aromatic amine"], [1, 2, 3]):
            if classification == amineClass:
                return numerical
            
    def getRatioInformation(mzPeaks):
        """Gets information on the number of peaks and their ratios. Returns the dictionary with this information."""
        
        msPeakInfo = {
            '2:3:6': 0,
            '4:6:12': 0,
            '10:15:30': 0,
            '6:9:18': 0,
            '8:12:24': 0,
            '2:2:4': 0,
            '4:4:8': 0,
            '6:6:12': 0,
            '10:10:20': 0      
        }

        for ratio in mzPeaks:
            ratioKey = f'{ratio['noMetal']}:{ratio['noAmine']}:{ratio['noCarbonyl']}'
            msPeakInfo[ratioKey] +=1
        
        return msPeakInfo


    msParametersOptimizationRunsPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/decisionMakerParameterOptimization/msParametersOptimizationRuns.pickle'
    with open(msParametersOptimizationRunsPath, 'rb') as f:
        parameterOptimization = pickle.load(f)

    # Getting the number of successfull reactions based on the different paramters for each optimization.

    allCriteriaHits = []
    criteria3Hits = []
    peakParameterList = []
    metalParameterList = []
        
    for optimization in parameterOptimization.keys():
        numAllCriteriaHit = 0    
        numCriteria3Hit = 0
        metalParameter, peakParameter = parameterOptimization[optimization]['parameters']['metals_mz']
        peakParameterList.append(peakParameter)
        metalParameterList.append(metalParameter)
        for batch in parameterOptimization[optimization]['batchMsOutcome'].keys():
            for sample in parameterOptimization[optimization]['batchMsOutcome'][batch]:
                #Excluding an standard reactions
                if 'batch' not in sample:
                    numCriteria3Hit += parameterOptimization[optimization]['batchMsOutcome'][batch][sample]['criteria3_pass']
                    numAllCriteriaHit += parameterOptimization[optimization]['batchMsOutcome'][batch][sample]['label']
        allCriteriaHits.append(numAllCriteriaHit)
        criteria3Hits.append(numCriteria3Hit)

    # Data for the number of reagents in sucessfull and all reactions
    reagentLibrarySucessfull = {}
    reagentLibraryAll = {}
    allData = {
        'descriptors': [],
        'descriptorsMaster': [],
        'descriptorsMasterNormalised': [],
        'metalEcfp': [],
        'aldehydeEcfp': [],
        'amineEcfp': [],
        'metalSize': [],
        'carbonCarbonylPartialCharge': [],
        'ringSize': [],
        'substituentVolume': [],
        'numRotatableBonds': [],
        'amineDihedralAngle': [],
        'amineClass': [],
        'reactionMsLabel': [],
        'reactionMetal': [],
        'reactionAmine': [],
        'reactionAldehdye': [],
        'testMix': [],
        'testMix2': []
    }
    
    sucessfullData = {
        'descriptors': [],
        'descriptorsMaster': [],
        'descriptorsMasterNormalised': [],
        'metalEcfp': [],
        'aldehydeEcfp': [],
        'amineEcfp': [],
        'metalSize': [],
        'carbonCarbonylPartialCharge': [],
        'ringSize': [],
        'substituentVolume': [],
        'numRotatableBonds': [],
        'amineDihedralAngle': [],
        'amineClass': [],
        'reactionMsLabel': [],
        'reactionMetal': [],
        'reactionAmine': [],
        'reactionAldehdye': [],
        'testMix': [],
        'testMix2': []
        }
        
    failedData = {
        'descriptors': [],
        'descriptorsMaster': [],
        'descriptorsMasterNormalised': [],
        'metalEcfp': [],
        'aldehydeEcfp': [],
        'amineEcfp': [],
        'metalSize': [],
        'carbonCarbonylPartialCharge': [],
        'ringSize': [],
        'substituentVolume': [],
        'numRotatableBonds': [],
        'amineDihedralAngle': [],
        'amineClass': [],
        'reactionMsLabel': [],
        'reactionMetal': [],
        'reactionAmine': [],
        'reactionAldehdye': [],
        'testMix': [],
        'testMix2': []
        }
      
    reagentData ={  
        'Reagent':[],
        'ReagentID': [],
        'NumberOfSucessfullReactions': [],
        'NumberOfAllReactions': [],
    }

    uniqueReagentRatios = ['2:2:4', '2:3:6', '4:4:8', '4:6:12', '6:6:12', '6:9:18', '8:12:24', '10:10:20', '10:15:30']

    #Information on reactions and the hits corresponding to differenet metal, ligand ratios.
    #Ratios are in the form metal:amine:aldehdye
    metalLigandRatioDataSuccessful = { 
        'reactionID': [],
        '2:3:6': [],
        '4:6:12': [],
        '10:15:30': [],
        '6:9:18': [],
        '8:12:24': [],
        '2:2:4': [],
        '4:4:8': [],
        '6:6:12': [],
        '10:10:20': [],
        'reactionMetal': [],
        'reactionAmine': [],
        'reactionAldehdye': []
    }

    # Data reperamterised to be able to plot multiple dimensions into one.
    metalLigandRatioPlotSuccessful = {
        'reactionID': [],
        'reagentRatio': [],
        'ratioCount': [],
        'reactionMetal': [],
        'reactionAmine': [],
        'reactionAldehdye': []
    }
    
    #Ratios are in the form metal:amine:aldehdye
    metalLigandRatioDataFailed = { 
        'reactionID': [],
        '2:3:6': [],
        '4:6:12': [],
        '10:15:30': [],
        '6:9:18': [],
        '8:12:24': [],
        '2:2:4': [],
        '4:4:8': [],
        '6:6:12': [],
        '10:10:20': [],
        'reactionMetal': [],
        'reactionAmine': [],
        'reactionAldehdye': []
    }

    # Data reperamterised to be able to plot multiple dimensions into one.
    metalLigandRatioPlotFailed = {
        'reactionID': [],
        'reagentRatio': [],
        'ratioCount': [],
        'reactionMetal': [],
        'reactionAmine': [],
        'reactionAldehdye': []
    }

    def collectData():
        """Takes the data and addes them to the allData and reagentData dictionaries"""
        parametersOfInterest = [0,0]
        numSamples = 0
        for optimization in parameterOptimization.keys():
            if parameterOptimization[optimization]['parameters']['metals_mz'] == parametersOfInterest:
                for batch in parameterOptimization[optimization]['batchMsOutcome'].keys():
                    for sample in parameterOptimization[optimization]['batchMsOutcome'][batch].keys():
                        #Checking that the sample is not the standard reaction.
                        if 'batch' not in sample:
                            numSamples += 1

                            #Getting the reaction object of the sample
                            reactionObject = getReaction(int(sample[:-4]))
                            msDecisionCheck = True if parameterOptimization[optimization]['batchMsOutcome'][batch][sample]['criteria3_pass'] == 1 else False  
                            
                            #Getting reagent information.
                            for reagent in reactionObject.reagents:

                                #getting the ECFP descriptors
                                ecfpDescriptor = computeEcfpDescriptors(reagentObject=reagent)

                                if reagent.__class__.__name__ == 'Metal':
                                    allData['metalEcfp'].append(ecfpDescriptor)
                                    allData['metalSize'].append(featureHashTableMaster[reagent.CAS]['metalSize'])
                                    allData['reactionMetal'].append(reagent.name)
                                    
                                    if msDecisionCheck:
                                        metalLigandRatioDataSuccessful['reactionMetal'].append(reagent.name)                                    
                                    else:
                                        metalLigandRatioDataFailed['reactionMetal'].append(reagent.name)
                                        
                                elif reagent.__class__.__name__ == 'Monoaldehdye':
                                    allData['aldehydeEcfp'].append(ecfpDescriptor)
                                    allData['carbonCarbonylPartialCharge'].append(featureHashTableMaster[reagent.CAS]['carbonCarbonylPartialCharge'])
                                    allData['ringSize'].append(featureHashTableMaster[reagent.CAS]['ringSize'])
                                    allData['substituentVolume'].append(featureHashTableMaster[reagent.CAS]['substituentVolume'])
                                    allData['reactionAldehdye'].append(reagent.name)
                                    
                                    if msDecisionCheck:
                                        metalLigandRatioDataSuccessful['reactionAldehdye'].append(reagent.name)
                                    else:
                                        metalLigandRatioDataFailed['reactionAldehdye'].append(reagent.name)

                                elif reagent.__class__.__name__ == 'Diamine':
                                    allData['amineEcfp'].append(ecfpDescriptor)
                                    allData['numRotatableBonds'].append(featureHashTableMaster[reagent.CAS]['numRotatableBonds'])
                                    allData['amineDihedralAngle'].append(featureHashTableMaster[reagent.CAS]['amineDihedralAngle'])
                                    allData['amineClass'].append(categoriseAmineClass(featureHashTableMaster[reagent.CAS]['amineClass']))
                                    allData['reactionAmine'].append(reagent.name)

                                    if msDecisionCheck:
                                        metalLigandRatioDataSuccessful['reactionAmine'].append(reagent.name)
                                    else:
                                        metalLigandRatioDataFailed['reactionAmine'].append(reagent.name)
                                        

                                #Updating all data
                                if reagent.name in reagentLibraryAll.keys():
                                        reagentLibraryAll[reagent.name] += 1
                                else:
                                    reagentLibraryAll[reagent.name] = 1

                                #Updating sucessfull reaction data.
                                if msDecisionCheck:
                                    if reagent.name in reagentLibrarySucessfull.keys():
                                        reagentLibrarySucessfull[reagent.name] += 1
                                    else:
                                        reagentLibrarySucessfull[reagent.name] = 1
                                
                            if msDecisionCheck:
                                allData['reactionMsLabel'].append(1)
                                
                                #Getting the ratio of metal:carbonyl:amine of the ms peak hit.
                                mzPeaks = parameterOptimization[optimization]['batchMsOutcome'][batch][sample]['mz_peaks']
                                buildingBlockRatio = getRatio(mzPeaks)
                                buildingBlocksData = getRatioInformation(buildingBlockRatio)
                                metalLigandRatioDataSuccessful['reactionID'].append(reactionObject.unique_identifier)            
                                for ratioKey in buildingBlocksData.keys():
                                    metalLigandRatioDataSuccessful[ratioKey].append(buildingBlocksData[ratioKey])

                            else:
                                allData['reactionMsLabel'].append(0)
                                
                                #Getting the ratio of metal:carbonyl:amine of the ms peak hit.
                                mzPeaks = parameterOptimization[optimization]['batchMsOutcome'][batch][sample]['mz_peaks']
                                buildingBlockRatio = getRatio(mzPeaks)
                                buildingBlocksData = getRatioInformation(buildingBlockRatio)
                                metalLigandRatioDataFailed['reactionID'].append(reactionObject.unique_identifier)            
                                for ratioKey in buildingBlocksData.keys():
                                    metalLigandRatioDataFailed[ratioKey].append(buildingBlocksData[ratioKey])

        for reagent in reagentSpace:
            if reagent.name in reagentLibrarySucessfull.keys():
                reagentData['NumberOfSucessfullReactions'].append(reagentLibrarySucessfull[reagent.name])
            else:
                reagentData['NumberOfSucessfullReactions'].append(0)

            if reagent.name in reagentLibraryAll.keys():
                reagentData['NumberOfAllReactions'].append(reagentLibraryAll[reagent.name])
            else:
                reagentData['NumberOfAllReactions'].append(0)
            reagentData['Reagent'].append(reagent.name)
            reagentID = reagentFigureIndex[reagent.ID]
            if type(reagentID) == float:
                reagentData['ReagentID'].append(int(reagentID))
            else:
                reagentData['ReagentID'].append(reagentID)

    def processData():
        """Takes in the features, processes them and addes them to the appropiate descriptors"""

        from sklearn.preprocessing import MinMaxScaler

        # Data to normalise and standardise
        featureToProcess = ['metalSize', 'carbonCarbonylPartialCharge', 'ringSize', 'substituentVolume', 'amineDihedralAngle', 'amineClass', 'numRotatableBonds']
        
        #Normalising and standardising data
        for feature in featureToProcess:

            featureData = allData[feature]
            minium = min(featureData)
            maximum = max(featureData)
            normalisedData = []
            
            for featureInstance in featureData:
                featurePrime = (featureInstance - minium) / (maximum - minium)
                normalisedData.append(featurePrime)

            allData[f'{feature}Processed'] = normalisedData
        
        # Adding appropiate features to the descriptors
        for _ in range(len(allData['reactionMsLabel'])):
            descriptor = allData['metalEcfp'][_] + allData['aldehydeEcfp'][_] + allData['amineEcfp'][_]
            descriptorMaster = [allData['metalSize'][_], 
                                allData['carbonCarbonylPartialCharge'][_], 
                                allData['ringSize'][_],
                                allData['substituentVolume'][_],
                                allData['numRotatableBonds'][_],
                                allData['amineDihedralAngle'][_],
                                allData['amineClass'][_]]
            descriptorMasterNormalised = [allData['metalSizeProcessed'][_], 
                                allData['carbonCarbonylPartialChargeProcessed'][_], 
                                allData['ringSizeProcessed'][_],
                                allData['substituentVolumeProcessed'][_],
                                allData['numRotatableBondsProcessed'][_],
                                allData['amineDihedralAngleProcessed'][_],
                                allData['amineClassProcessed'][_]]
            allData['descriptors'].append(descriptor)
            allData['descriptorsMaster'].append(descriptorMaster)
            allData['descriptorsMasterNormalised'].append(descriptorMasterNormalised)
            allData['testMix'].append(descriptorMasterNormalised + [allData['reactionMsLabel'][_]])
            allData['testMix2'].append(descriptor + [allData['reactionMsLabel'][_]])
            
        #Updating Sucesful and failed data dictionaries.

        for _ in range(len(allData['reactionMsLabel'])):
            if allData['reactionMsLabel'][_] == 1:
                for dataKey in sucessfullData.keys():
                    sucessfullData[dataKey].append(allData[dataKey][_])
            else:
                for dataKey in failedData.keys():
                    failedData[dataKey].append(allData[dataKey][_])

        # Turning categorical values to continous for metal:amine:aldehyde ratios 
        for _ in range(len(metalLigandRatioDataSuccessful['reactionID'])):
            for continiousReagentRatio, reagentRatio in enumerate(uniqueReagentRatios):
                ratioCount = metalLigandRatioDataSuccessful[reagentRatio][_]
                if ratioCount != 0:
                    metalLigandRatioPlotSuccessful['reactionID'].append(str(metalLigandRatioDataSuccessful['reactionID'][_]))
                    metalLigandRatioPlotSuccessful['reagentRatio'].append(continiousReagentRatio)
                    metalLigandRatioPlotSuccessful['ratioCount'].append(ratioCount)
                    metalLigandRatioPlotSuccessful['reactionMetal'].append(metalLigandRatioDataSuccessful['reactionMetal'][_])
                    metalLigandRatioPlotSuccessful['reactionAmine'].append(metalLigandRatioDataSuccessful['reactionAmine'][_])
                    metalLigandRatioPlotSuccessful['reactionAldehdye'].append(metalLigandRatioDataSuccessful['reactionAldehdye'][_])

        for _ in range(len(metalLigandRatioDataFailed['reactionID'])):
            for continiousReagentRatio, reagentRatio in enumerate(uniqueReagentRatios):
                metalLigandRatioPlotFailed['reactionID'].append(str(metalLigandRatioDataFailed['reactionID'][_]))
                metalLigandRatioPlotFailed['reagentRatio'].append(continiousReagentRatio)
                metalLigandRatioPlotFailed['ratioCount'].append(ratioCount)
                metalLigandRatioPlotFailed['reactionMetal'].append(metalLigandRatioDataFailed['reactionMetal'][_])
                metalLigandRatioPlotFailed['reactionAmine'].append(metalLigandRatioDataFailed['reactionAmine'][_])
                metalLigandRatioPlotFailed['reactionAldehdye'].append(metalLigandRatioDataFailed['reactionAldehdye'][_])

    def getVisualData():
        """Plotting data."""

        from rdkit import RDLogger

        def getDimensionReduction(listSpaceName:str, dataDictionary, figureFolderName: str, displayUmap = True, displayTNSE = False, nNeighbors = 5, minDist = 0.4):
            """Get TSNE and UMAP dimension reduction of a space in the form of a list."""
            # Silence non-critical RDKit warnings to minimize unnecessary outputs
            lg = RDLogger.logger()
            lg.setLevel(RDLogger.CRITICAL)

            umap_model = umap.UMAP(metric = "jaccard",
                                n_neighbors = nNeighbors,
                                n_components = 2,
                                low_memory = False,
                                min_dist = minDist)
            X_umap = umap_model.fit_transform(dataDictionary[listSpaceName])
            dataDictionary["UMAP_0"], dataDictionary["UMAP_1"] = X_umap[:,0], X_umap[:,1]

            tsne = TSNE(n_components=2)
            X_tsne = tsne.fit_transform(np.array(dataDictionary[listSpaceName]))
            dataDictionary["TNSE_0"], dataDictionary["TNSE_1"] = X_tsne[:,0], X_tsne[:,1]

            for method in ['UMAP', 'TNSE']:
                
                # Folder to save generated figures
                figureFilePath = f'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/Raw Figures/MainResearchPaper/DecisionMaker/msFilter/reagentDataAnalysis/{figureFolderName}/{listSpaceName}/{method}'
                if not os.path.exists(figureFilePath):
                    os.makedirs(figureFilePath)

                palette = sns.color_palette()

                plt.figure(figsize=(8,8))
                sns.scatterplot(data=dataDictionary,
                                x=f"{method}_0",
                                y=f"{method}_1",
                                hue='reactionMsLabel',
                                alpha=0.5,
                                palette = palette)
                plt.title(f"{method} Embedding of Ms Screening Dataset")
                figurePathSvg = figureFilePath + '/reactionMsLabel.svg'
                figurePathPng = figureFilePath + '/reactionMsLabel.png'
                plt.savefig(figurePathSvg, format='svg')
                plt.savefig(figurePathPng, format='png')
                if method == 'UMAP' and displayUmap == True:
                    plt.show()
                elif method == 'TNSE' and displayTNSE == True:
                    plt.show()

                for feature in ['metalSize', 'carbonCarbonylPartialCharge', 'ringSize', 'substituentVolume', 'numRotatableBonds', 'amineDihedralAngle', 'amineClass']:
                    palette = sns.color_palette("Spectral", as_cmap=True)

                    plt.figure(figsize=(8,8))
                    sns.scatterplot(data=dataDictionary,
                                    x=f"{method}_0",
                                    y=f"{method}_1",
                                    hue=f'{feature}',
                                    alpha=0.5,
                                    palette = palette)
                    plt.title(f"{method} Embedding of Ms Screening Dataset")
                    
                    figurePathSvg = figureFilePath + f'/{feature}.svg'
                    figurePathPng = figureFilePath + f'/{feature}.png'
                    plt.savefig(figurePathSvg, format='svg')
                    plt.savefig(figurePathPng, format='png')
                    if method == 'UMAP' and displayUmap == True:
                        plt.show()
                    elif method == 'TNSE' and displayTNSE == True:
                        plt.show()

                for reagent in ['reactionMetal', 'reactionAmine', 'reactionAldehdye']:
                    palette = sns.color_palette()

                    plt.figure(figsize=(8,8))
                    sns.scatterplot(data=dataDictionary,
                                    x=f"{method}_0",
                                    y=f"{method}_1",
                                    hue=f'{reagent}',
                                    alpha=0.5,
                                    palette = palette)
                    plt.title(f"{method} Embedding of Ms Screening Dataset")
                    figurePathSvg = figureFilePath + f'/{reagent}.svg'
                    figurePathPng = figureFilePath + f'/{reagent}.png'
                    plt.savefig(figurePathSvg, format='svg')
                    plt.savefig(figurePathPng, format='png')
                    if method == 'UMAP' and displayUmap == True:
                        plt.show()
                    elif method == 'TNSE' and displayTNSE == True:
                        plt.show()        

        def getReagentRatioFigure(dataDictionary: dict, figureFolderName, displayFigure = False):
            """Gets plots on data for different metal:amine:aldhdye ratios."""
            
            figureFilePath = f'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/Raw Figures/MainResearchPaper/DecisionMaker/msFilter/reagentDataAnalysis/reagentRatios/{figureFolderName}/'
            if not os.path.exists(figureFilePath):
                os.makedirs(figureFilePath)

            palette = sns.color_palette()
            
            for reagent in ['reactionMetal', 'reactionAmine', 'reactionAldehdye']:
                plt.figure(figsize=(16,8))
                sns.scatterplot(data=dataDictionary,
                                x='reactionID',
                                y='reagentRatio',
                                size='ratioCount',
                                hue=reagent,
                                alpha=0.5,
                                palette = palette).set_yticks([0, 1, 2, 3, 4, 5, 6, 7, 8], uniqueReagentRatios)        
                plt.xlabel("Reaction (in reaction order)")
                plt.ylabel("Reagent ratios (metal:amine:aldehyde)")
                figurePathSvg = figureFilePath + f'/{reagent}Ordered.svg'
                figurePathPng = figureFilePath + f'/{reagent}Ordered.png'
                plt.savefig(figurePathSvg, format='svg')
                plt.savefig(figurePathPng, format='png')
                if displayFigure:
                    plt.show()


                plotDf = pd.DataFrame.from_dict(dataDictionary)
                plotDf = plotDf.sort_values(by= reagent)
                palette = sns.color_palette()
                    
                plt.figure(figsize=(16,8))
                sns.scatterplot(data=plotDf,
                                x='reactionID',
                                y='reagentRatio',
                                size='ratioCount',
                                hue=reagent,
                                alpha=0.5,
                                palette = palette).set_yticks([0, 1, 2, 3, 4, 5, 6, 7, 8], uniqueReagentRatios)        
                plt.xlabel("Reaction (based on reagent groupings)")
                plt.ylabel("Reagent ratios (metal:amine:aldehyde)")
                figurePathSvg = figureFilePath + f'/{reagent}Grouped.svg'
                figurePathPng = figureFilePath + f'/{reagent}Grouped.png'
                plt.savefig(figurePathSvg, format='svg')
                plt.savefig(figurePathPng, format='png')
                if displayFigure:
                    plt.show()
        
        def getReagentData(figureFolderName: str, displayFigure=False):
            """Saves reagent data as a table and as a histograme."""
            
            figureFilePath = f'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/Raw Figures/MainResearchPaper/DecisionMaker/msFilter/reagentDataAnalysis/{figureFolderName}/'
            if not os.path.exists(figureFilePath):
                os.makedirs(figureFilePath)
            
            #Saving reagent data as csv.
            reagentDataCsvPath = figureFilePath + 'reagentTable.csv'
            reagentDataDf = pd.DataFrame.from_dict(reagentData)
            reagentDataDf.to_csv(reagentDataCsvPath)

            #Creating % sucess and saving it as a histogram.
            reagentDataDf['%Success'] = reagentDataDf['NumberOfSucessfullReactions'] / reagentDataDf['NumberOfAllReactions'] * 100
            reagentDataDf = reagentDataDf[reagentDataDf['%Success'].notna()]
            print(reagentDataDf['%Success'])
            palette = sns.color_palette()

            plt.figure(figsize=(16,8))
            sns.barplot(data=reagentDataDf,
                            x='Reagent',
                            y='%Success',
                            alpha=0.5,
                            palette = palette)        
            plt.xlabel("Reagents")
            plt.ylabel("Probility of sucessful reaction if reagent in mixture")
            plt.xticks(rotation=90)
            figurePathSvg = figureFilePath + '/reagentData.svg'
            figurePathPng = figureFilePath + '/reagentData.png'
            plt.savefig(figurePathSvg, format='svg')
            plt.savefig(figurePathPng, format='png')
            if displayFigure:
                plt.show()

        # Captivating more global structure
        # getDimensionReduction(listSpaceName='descriptorsMasterNormalised', dataDictionary=allData, nNeighbors = 30, minDist=0.8, displayUmap=True, displayTNSE=False, figureFolderName='globalStructure')

        # Captivatin more local structure
        # getDimensionReduction(listSpaceName='descriptorsMasterNormalised', dataDictionary=allData, nNeighbors = 5, minDist=0.8, displayUmap=True, displayTNSE=False, figureFolderName='localStructure')
        
        # getReagentRatioFigure(metalLigandRatioPlotSuccessful, figureFolderName='Successful', displotFigure=True)
        # getReagentRatioFigure(metalLigandRatioPlotFailed, figureFolderName='Failed', displotFigure=True)
        
        # getReagentData(figureFolderName='ReagentData', displayFigure=True)


    collectData()
    processData()
    # getVisualData()

def getHumanExpertLables(parameters, dataLocations):
    """Iterates through the reactions, displays the MS + NMR data, takes in the human label for the two and saves it to a pickle."""

    #Importing synthesis_bots.utils.nmr.processing
    nmrProcessingPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/dependencies/modules/synthesis_bots/utils/nmr/processing.py'
    spec = importlib.util.spec_from_file_location('nmrProcessing', nmrProcessingPath)
    nmrProcessing = importlib.util.module_from_spec(spec)
    sys.modules['nmrProcessing'] = nmrProcessing
    spec.loader.exec_module(nmrProcessing)

    #Importing synthesis_bots.utils.nmr.acquisition
    nmrAcquisitionPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/dependencies/modules/synthesis_bots/utils/nmr/acquisition.py'
    spec = importlib.util.spec_from_file_location('nmrAcquisition', nmrAcquisitionPath)
    nmrAcquisition = importlib.util.module_from_spec(spec)
    sys.modules['nmrAcquisition'] = nmrAcquisition
    spec.loader.exec_module(nmrAcquisition)

    def getDictionaryKeyMs(dataLocations, msSample, batchSample):
        """Returns the number of the sample in the batch. This is used as a key."""            

        #Getting the batch and the NmrSample number depending on the reaction number (smaple)
        batchSize = combinationParameters.batchSize-1
        batchNumber = batchSample[5:]
        nmrSampleNumber = None
        if 'batch' in msSample:
            nmrSampleNumber = 1
        else:
            if int(batchNumber) != 0:
                nmrSampleNumber = (int(msSample) % int(batchSize)) + 1
            else:
                nmrSampleNumber = int(msSample) + 1

        return nmrSampleNumber

        # # Translating from MS sample name to NMR sample name.
        # if nmrSampleNumber < 10:
        #     nmrSampleNumber = '0' + str(nmrSampleNumber)
        # else:
        #     nmrSampleNumber = str(nmrSampleNumber)

        # nmrFileName = 'batch' + str(batchNumber) + '-' + nmrSampleNumber 
        # nmrSamplePath = dataLocations['reactionData']+f'/{batchSample}' + '/NmrData' + nmrFileName

        # return nmrSamplePath    

    def getDictionaryKeyNmr(dataLocations, nmrSample):
        """Returns the number of the sample in the batch. This is used as a key."""
        batchNumber, nmrSampleNumber = nmrSample[5:].split("-")
        return int(nmrSampleNumber)
    
    def getMsSample(datalocations, nmrSample, batchSample):
        """Returns the Ms sample file name."""
        batchSize = combinationParameters.batchSize
        standardReactionId = combinationParameters.standardReactionIdx
        batchNumber, nmrSampleNumber = nmrSample[5:].split("-")
        if int(nmrSampleNumber) == 1:
            msSample = str(standardReactionId) + 'batch' + batchNumber + '.raw'
        else:
            reactionNumber = (int(batchNumber))*(batchSize-1) + (int(nmrSampleNumber)-1)
            msSample = str(reactionNumber) + '.raw'

        return msSample 
        
    def getHumanMsInput(msSample):
        """Gets the label for Ms by the human"""
        print('')
        print(f'The reaction is {msSample[:-4]}')
        print(f'0 = fail')
        print(f'1 = Reaction unknown product')
        print(f'2 = Reaction supramolecular product')
        print(f'q = quit')

        inputPass = False
        while not inputPass:
            humanInput = input('What is the human label for Ms: ')
            if humanInput == 'q':
                return 'q'
            elif humanInput == '0' or humanInput == '1' or humanInput == '2':
                inputPass = True
                return humanInput

    def getHumanNmrInput(nmrSample, msSample):
        """Gets the label for NMR by the human."""
        print('')
        print(f'The reaction is {msSample[:-4]}')
        print(f'0 = No reaction, only starting materials')
        print(f'1 = Single discrete structure formed')
        print(f'2 = Oligomers formed')
        print(f'3 = paramagentic species formed')
        print(f'4 = Uninterpritble spectra')

        inputPass = False
        while not inputPass:
            humanInput = input('What is the humal label for Ms: ')
            if humanInput == 'q':
                return 'q'
            elif humanInput == '0' or humanInput == '1' or humanInput == '2' or humanInput == '3' or humanInput == '4':
                inputPass = True
                return humanInput
    
    def savePickle(picklePath, dictionaryObject):
        """Saves a pickle file to the given path"""
        with open(picklePath, 'wb') as f:
            pickle.dump(dictionaryObject, f)
    
    def getReactionID(spectra:str):
        "returns the reaction ID to then be looked up in the expectedMsPeaks dicionary"
        spectraName = spectra[:-4]
        if 'batch' in spectraName:
            spectraName = str(combinationParameters.standardReactionIdx + 1)
    
        return spectraName

    def prettifyMsExperiment(msExperiment):
        """Returns a more human legible and friendly version of the msExperiment."""
        prettyDictionary = {}
        for ratio in msExperiment.keys():
            splitRatio = ratio.split('_')
            metalRatio = splitRatio[1][1:-1]
            amineRatio = splitRatio[5][1:-1]
            carbonylRatio = splitRatio[3][1:-1]
            newRatio = f'{metalRatio}:{amineRatio}:{carbonylRatio}'
            prettyDictionary[newRatio] = []
            for peakNumber, peakValue in msExperiment[ratio].items():
                prettyDictionary[newRatio].append(peakValue)
        
        return prettyDictionary

    def prettifyMsDecision(msDecision):
        """Returns a more human legible and friendly version of the msDecision."""
        prettyDictionary = {}
        prettyDictionary['label'] = msDecision['label']

        for peakHit in msDecision['mz_peaks']:
            peak = peakHit['mz_expected']
            splitRatio = peakHit['formula'].split('_')
            metalRatio = splitRatio[1][1:-1]
            amineRatio = splitRatio[5][1:-1]
            carbonylRatio = splitRatio[3][1:-1]
            newRatio = f'{metalRatio}:{amineRatio}:{carbonylRatio}'
            prettyDictionary[newRatio] = peak

        return prettyDictionary

    def displayPrettyDictionary(prettyDictionary):
        """Displays a generic pretty dictionary."""
        for dictionaryKey, dictionaryValue in prettyDictionary.items():
            print(f'{dictionaryKey}: {dictionaryValue}')



    #The structure of the dictionary is as follows:
    # {
    #     'batch': {
    #         'sample':
    #         {
    #             'MsDecision': int,
    #             'humanMsLabel': int,
    #             'humanNmrLabel': int,
    #             'reactionId': int,
    #         },
    #     },
    #    'lackingMsSamples': [], #These are all NMR smaples that are missing corresponding MS spectra.
    # }

    humanLabelPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/humanLabeling/humanLable.pickle'

    #Getting human labels if exits.
    if not os.path.exists(humanLabelPath):
        humanLabels = {'lackingMsSamples':[]}
    else:
        with open(humanLabelPath, 'rb') as f:
            humanLabels = pickle.load(f)

    try:
        print(humanLabels['batch0'].keys())
    except:
        pass

    #Saving toml with parameters
    generateToml(parameters=parameters)

    #Loading predicted masses
    expectedMsPeaksPath = dataLocations['expectedMsPeaksData']
    with open(expectedMsPeaksPath) as f:
        expectedMsPeaks = json.load(f)
    
    batchFiles = dataLocations['reactionData']
    batchSamples = os.listdir(batchFiles)

    breakFlag = False # If true the loop is exited.
    for batch in batchSamples:
        batchDataPath = dataLocations['reactionData'] + '/' + batch
        batchNmrDataPath = batchDataPath + '/NmrData'
        batchMsDataPath = batchDataPath + '/MsData'
        nmrSampleFiles = getFilesOrFolders('batch', batchNmrDataPath)

        #Loading NMR batch experimens
        nmrExperimentsPath = batchDataPath + '/nmrInputFile.json' 
        with open(nmrExperimentsPath, 'r') as f:
            nmrExperimentsDictionary = json.load(f)

        for nmrSample in nmrSampleFiles:
            if not breakFlag:
                sampleData = {}

                #Ms Sample information
                nmrDictionaryKey = getDictionaryKeyNmr(dataLocations, nmrSample)
                msSample = getMsSample(dataLocations, nmrSample, batch)
                msExperimentName = getReactionID(spectra=msSample)
                msExperiment = expectedMsPeaks[msExperimentName]
                msFile = batchMsDataPath + '/' + msSample
                
                #Nmr Sample information
                nmrFile = batchNmrDataPath + '/' + nmrSample
                nmr = nmrProcessing.NMRExperiment(nmrAcquisition.FOURIER.open_experiment(nmrFile))
                nmrExperiment = nmrExperimentsDictionary[f'{nmrSample}']

                #checking tha the spectra exist
                if os.path.exists(msFile):

                    #Checking that the inputs have not been taken already.
                    sampleTaken = True
                    try:
                        humanLabels[batch][nmrDictionaryKey]
                    except:
                        sampleTaken = False

                    if not sampleTaken: 
                        #Taking MS spectra
                        prettyMsExperiment = prettifyMsExperiment(msExperiment)
                        print('')
                        print('The expected peaks are:')
                        displayPrettyDictionary(prettyMsExperiment)
                        msDecision = singleMsDecision(parameters=parameters,
                                                        dataLocations=dataLocations,
                                                        experimentName=msExperimentName,
                                                        msExperiment=msExperiment,
                                                        msFile= msFile,
                                                        displayFigure=False,
                                                        saveFig=False
                                                        )
                        prettyMsDecision = prettifyMsDecision(msDecision)
                        print('')
                        print('The MS decision outcome is:')
                        displayPrettyDictionary(prettyMsDecision)

                        singleMsDecision(parameters=parameters,
                                                        dataLocations=dataLocations,
                                                        experimentName=msExperimentName,
                                                        msExperiment=msExperiment,
                                                        msFile= msFile,
                                                        displayFigure=True,
                                                        saveFig=False
                                                        )

                        #Taking NMR spectra
                        reagentPeaks = pickPeaks(parameters=parameters, 
                                            experimentName=nmrSample, 
                                            nmrExperiment=nmrExperiment,
                                            nmrFilePath=nmrFile,
                                            saveFig=False)

                        #Taking in human labels
                        humanMsLabel = getHumanMsInput(msSample)
                        if humanMsLabel == 'q':
                            breakFlag = True
                        else:
                            humanNmrLabel = getHumanNmrInput(nmrSample, msSample)
                            if humanNmrLabel == 'q':
                                breakFlag = True
                            else:    
                                #Updating humanLabels information
                                sampleData['MsDecision'] = msDecision
                                sampleData['humanMsLabel'] = humanMsLabel
                                sampleData['humanNmrLabel'] = humanNmrLabel
                                sampleData['reactionId'] = msSample[:-4]

                                if batch in humanLabels.keys():
                                    humanLabels[batch][nmrDictionaryKey] = sampleData
                                else:
                                    humanLabels[batch] = {}
                                    humanLabels[batch][nmrDictionaryKey] = sampleData                                         
                else:
                    humanLabels['lackingMsSamples'].append(msSample)
    
    print('The reactions that do not have corresponding MS spectra are:')
    print(humanLabels['lackingMsSamples'])
    savePickle(humanLabelPath, humanLabels)

def getSingleMsSpectraForPaper(reactionNumber, figurePath):
    """Gets the MS spectra for a reaction and saves if to a rawpicture folder."""
    
    #Loading predicted masses
    expectedMsPeaksPath = dataLocations['expectedMsPeaksData']
    with open(expectedMsPeaksPath) as f:
        expectedMsPeaks = json.load(f)

    msExperiment = expectedMsPeaks[str(reactionNumber)]
    msSample = f'{reactionNumber}.raw'
    msFile = strCWD + '/Data/RawData/MsData/Gunther.PRO/Data/' + msSample
    figureFolderPath = f'{figurePath}/{reactionNumber}/'
    if not os.path.exists(figureFolderPath):
        os.makedirs(figureFolderPath)

    decision = singleMsDecision(
        parameters=parameters,
        dataLocations=dataLocations,
        experimentName=str(reactionNumber),
        msExperiment=msExperiment,
        msFile= msFile,
        displayFigure=True,
        saveFig=True,
        figureFolderPath=figureFolderPath
        )
    print('')
    print(reactionNumber)
    for peakHit in decision['mz_peaks']:
        print(f'{peakHit['formula']}: {peakHit['mz_expected']}')

def analyseHumanLabels():
    """Gets the human label file and analysis the data."""            

    def retrieveReactionObject(reactionNumber):
            """Returns a reaction object based on the reaction number"""

            #Getting the sample space.
            sampleSpacePath = strCWD + '/ReactionCombinationsWorkflow/GeneratedPickles/SampleSpace.pickle'
            with open(sampleSpacePath, 'rb') as f:
                sampleSpace = pickle.load(f)

            reactionList = sampleSpace.ReactionSpace.reactionSpace

            for reaction in reactionList:
                if str(reaction.unique_identifier) == str(reactionNumber):
                    return reaction

    #Getting human label data
    humanLabelPath = 'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/backup/ChemspeedPlatformAllVersions/V12/Workflows/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/humanLabeling/humanLable.pickle'
    with open(humanLabelPath, 'rb') as f:
        humanLabels = pickle.load(f)

    #Getting the feature reagent hash table for masters project.
    featureHashTablePath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/masterCompoundHashTable.pickle'
    with open(featureHashTablePath, 'rb') as f:
            featureHashTableMaster = pickle.load(f)

    def collectData():
        """Gets reaction and reagent data, and adds it to a dictionary. Returns the updated dictionary."""    
        def categoriseAmineClass(amineClass):
            """Returns the class of the amine as a numerical value"""
            
            for classification, numerical in zip (["alkyl and aromatic amine", "alkyl amine", "aromatic amine"], [1, 2, 3]):
                if classification == amineClass:
                    return numerical
                
        reactionData = {
        'metalSize': [],
        'carbonCarbonylPartialCharge': [],
        'ringSize': [],
        'substituentVolume': [],
        'numRotatableBonds': [],
        'amineDihedralAngle': [],
        'amineClass': [],
        'reactionMetal': [],
        'reactionAmine': [],
        'reactionAldehdye': [],
        'MsDecision': [],
        'humanMsLabel': [],
        'humanNmrLabel': [],
        'reactionId': [],
        'reactionMetal': [],
        'reactionAmine': [],
        'reactionAldehdye': []
        }
        
        for batch in humanLabels.keys():
            if batch != 'lackingMsSamples':
                for sampleKey, sampleValue in humanLabels[batch].items():
                    reactionId = sampleValue['reactionId']
                    humanMsLable = sampleValue['humanMsLabel']
                    humanNmrLabel = sampleValue['humanNmrLabel']
                    MsDecision = sampleValue['MsDecision']['label']
                    if 'batch' not in str(reactionId):
                        reactionObject = retrieveReactionObject(reactionId)

                        amine = None
                        aldehdye = None
                        metal = None
                        amineCAS = None
                        aldehdyeCAS = None
                        metal = None 

                        for reagent in reactionObject.reagents:
                            if reagent.__class__.__name__ == 'Diamine':
                                amine = reagent.name
                                amineCAS = reagent.CAS
                            elif reagent.__class__.__name__ == 'Monoaldehdye':
                                aldehdye = reagent.name
                                aldehdyeCAS = reagent.CAS
                            elif reagent.__class__.__name__ == 'Metal':
                                metal = reagent.name
                                metalCAS = reagent.CAS
                        
                        amineClass = categoriseAmineClass(featureHashTableMaster[amineCAS]['amineClass'])

                        reactionData['reactionId'].append(reactionId)
                        reactionData['humanMsLabel'].append(int(humanMsLable))
                        reactionData['humanNmrLabel'].append(int(humanNmrLabel))
                        reactionData['MsDecision'].append(MsDecision)
                        reactionData['reactionAmine'].append(amine)
                        reactionData['reactionAldehdye'].append(aldehdye)
                        reactionData['reactionMetal'].append(metal)
                        reactionData['metalSize'].append(featureHashTableMaster[metalCAS]['metalSize'])
                        reactionData['carbonCarbonylPartialCharge'].append(featureHashTableMaster[aldehdyeCAS]['carbonCarbonylPartialCharge'])
                        reactionData['ringSize'].append(featureHashTableMaster[aldehdyeCAS]['ringSize'])
                        reactionData['substituentVolume'].append(featureHashTableMaster[aldehdyeCAS]['substituentVolume'])
                        reactionData['numRotatableBonds'].append(featureHashTableMaster[amineCAS]['numRotatableBonds'])
                        reactionData['amineDihedralAngle'].append(featureHashTableMaster[amineCAS]['amineDihedralAngle'])
                        reactionData['amineClass'].append(amineClass)

        return reactionData

    def getVisualData(dataDf):
        """Plots different figures of the data to be used in master thesis."""

        import seaborn as sns
        import matplotlib.pyplot as plt

        figureFilePath = 'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/Raw Figures/MainResearchPaper/DecisionMaker/humanLabelling/plots'
        
        def getReagentDistributionPlot(dataDf):
            """Makes a plot showing the different reagents and their probability of success for both MS and human classified reactions."""

            #Plot showing the different reagents and their probability of success.
            probabilityData = {
                'Reagent': ['Iron(II) tetrafluoroborate hexahydrate', 'Silver tetrafluoroborate', 'Yittrium(III) trifluoromethanesulfonate', 'Zinc tetrafluoroborate', '2,2\'-(Ethane-1,2-diyl)dianiline', '2,2\'-(Ethane-1,2-diylbis(oxy))diethanamine', '4,4\'-(9H-AdamantaeFlurene-9,9diyl)dianiline', '4,4\'-Methylenedianiline', '4,4\'-Oxydianiline', 'Naphthalene-1,8-diamine', 'm-Xylylenediamine', '1-Methyl-2-imidazolecarboxaldehyde', '2-Quinolinecarboxaldehyde', '4-Formyl-2-methylthiazole', '5-Methylpicolinaldehyde', '6-Methoxypyridine-2-carbaldehyde', '6-Methylpyridine-2-carboxaldehyde'],
                '%HumanLabel': [31.25, 36.66666667, 3.846153846, 40.625, 31.57894737, 26.66666667, 36.84210526, 40, 40, 0, 26.66666667, 30, 0, 23.07692308, 38.46153846, 31.81818182, 25],
                '%DecisionMakerLabel': [43.75, 43.33333333, 26.92307692, 53.125, 47.36842105, 40, 57.89473684, 55, 53.33333333, 0, 40, 35, 50, 42.30769231, 42.30769231, 45.45454545, 45.83333333],
                'SamplesizeHumanLable': [22, 19, 25, 19, 13, 11, 12, 12, 9, 17, 11, 14, 2, 20, 16, 15, 18],
                'SampleSizeDecisionMakerLabel': [32, 30, 26, 32, 19, 15, 19, 20, 15, 17, 15, 20, 2, 26, 26, 22, 24]  
            }

            X_axis = np.arange(len(probabilityData['Reagent']))
            palette1 = []
            palette2 = []
            for colour in sns.color_palette():
                redness = colour[0]
                greeness = colour[1]
                blueness = colour[2]
                transparency1 = 0.5
                transparency2 = 1
                colour1 = (redness, greeness, blueness, transparency1)
                colour2 = (redness, greeness, blueness, transparency2)
                palette1.append(colour1)
                palette2.append(colour2)

            plt.figure(figsize=(14,8))
            plt.bar(X_axis, probabilityData['%DecisionMakerLabel'], 0.8, label='% Success according to decision maker Label', color=palette1)
            plt.bar(X_axis, probabilityData['%HumanLabel'], 0.7, label='% Success according to human label', color=palette2)

            plt.xlabel("Reagents")
            plt.ylabel("Probility of sucessful reaction if reagent in mixture")
            plt.xticks(rotation=90)
            plt.xticks(X_axis, probabilityData['Reagent'])
            plt.legend()
            figurePathSvg = figureFilePath + '/reagentData.svg'
            figurePathPng = figureFilePath + '/reagentData.png'
            plt.savefig(figurePathSvg, format='svg')
            plt.savefig(figurePathPng, format='png')
            plt.show()

        def getMsMatchingPlot(dataDf):
            """Gets a plot that shows reactions and what human and decision maker have labeled the reaction."""

            def combineHumanDsLabels(humanLabel, dsLabel):
                """Turns the 0,1,2 to a decision maker comparable label"""
                
                humanLabel = humanLabel
                if str(humanLabel) == '0' or str(humanLabel) == '1':
                    humanLabel = 0
                else:
                    humanLabel = 1

                if str(humanLabel) == str(dsLabel):
                    return humanLabel
                elif str(humanLabel) == '1' and str(dsLabel) == '0':
                    return 2/3
                elif str(humanLabel) == '0' and str(dsLabel) == '1':
                    return 1/3
            
            
            dataDf['combinedHumanDsMsdecision'] = dataDf.apply(lambda x: combineHumanDsLabels(x['humanMsLabel'], x['MsDecision']), axis=1)

            print(dataDf.columns)

            for reagentClass in ['reactionMetal', 'reactionAmine', 'reactionAldehdye']:
                dataDf = dataDf.sort_values(by=reagentClass)

                palette = sns.color_palette()
                plt.figure(figsize=(16,8))

                sns.scatterplot(data=dataDf,
                                x='reactionId',
                                y='combinedHumanDsMsdecision',
                                hue=reagentClass,
                                alpha=0.5,
                                palette = palette,
                                color= 'blue'
                                )

                plt.xlabel("Reaction (based on reagent groupings)")
                plt.ylabel("MS spectra label")
                plt.yticks([0, 1/3, 2/3, 1], ['Human and decision maker\nboth agree no supramolecular\nstructure present based on MS alone', 'Decision maker found\nsupramolecular structure but \nhuman disagrees', 'Decision maker found\nno supramolecular structure\nbut human disagrees', 'Human and decision maker\nboth agree that supramolecular\nstructure present based on MS alone'])
                figurePathSvg = figureFilePath + f'/combinedMsDecisions{reagentClass}.svg'
                figurePathPng = figureFilePath + f'/combinedMsDecisions{reagentClass}.png'
                plt.savefig(figurePathSvg, format='svg')
                plt.savefig(figurePathPng, format='png')
                plt.legend()
                plt.show()

            palette = sns.color_palette()
            plt.figure(figsize=(14,8))

            sns.scatterplot(data=dataDf,
                            x='reactionId',
                            y='combinedHumanDsMsdecision',
                            alpha=0.5,
                            palette = palette,
                            color= 'red'
                            )

            plt.xlabel("Reaction (based on reagent groupings)")
            plt.ylabel("MS spectra label")
            plt.yticks([0, 1/3, 2/3, 1], ['Human and decision maker\nboth agree no supramolecular\nstructure present based on MS alone', 'Decision maker found\nsupramolecular structure but \nhuman disagrees', 'Decision maker found\nno supramolecular structure\nbut human disagrees', 'Human and decision maker\nboth agree that supramolecular\nstructure present based on MS alone'])
            figurePathSvg = figureFilePath + f'/combinedMsDecisionsNoReagentClass.svg'
            figurePathPng = figureFilePath + f'/combinedMsDecisionsNoReagentClass.png'
            plt.savefig(figurePathSvg, format='svg')
            plt.savefig(figurePathPng, format='png')
            plt.legend()
            plt.show()

        def getConfusionMatrix(dataDf):
            """Gets the confusion matrix between the MR, NMR human classification, and MS decision maker classification"""
            from sklearn import metrics
            import matplotlib.pyplot as plt

            def mapHumanNmrLabel(nmrLabel):
                """maps multiple classification to binary"""
                if str(nmrLabel) != '1':
                    return 0
                else:
                    return 1

            def mapHumanMsLabel(msLabel):
                """maps multiple classification to binary"""
                if str(msLabel) != '2':
                    return 0
                
                else:
                    return 1
            
            figureFilePath = 'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/Raw Figures/MainResearchPaper/DecisionMaker/humanLabelling/plots'

            dataDf['humanMsLabelBinary'] = dataDf['humanMsLabel'].apply(mapHumanMsLabel)
            dataDf['humanNmrLabelBinary'] = dataDf['humanNmrLabel'].apply(mapHumanNmrLabel)


            possibleCombinations = [('humanMsLabelBinary', 'MsDecision'), ('humanNmrLabelBinary', 'MsDecision'), ('humanMsLabelBinary', 'humanNmrLabelBinary')]
            labelNames = [('Human MS Label', 'Decision Maker MS Label'), ('Human NMR Label', 'Decision Maker MS Label'), ('Human MS Label', 'Human NMR Label')]
            
            for _, combination in enumerate(possibleCombinations):
                pseudoGroundTruth, comparisonSet = combination
                yLabelText, xLabelText = labelNames[_]
                

                palette = sns.color_palette()
                confusionMatrix = metrics.confusion_matrix(dataDf[pseudoGroundTruth], dataDf[comparisonSet])
                cm_display = sns.heatmap(confusionMatrix, annot=True)
                cm_display.plot()
                plt.xlabel(xLabelText)
                plt.ylabel(yLabelText)
                # plt.show()
                figurePathSvg = figureFilePath + f'/{pseudoGroundTruth}_{comparisonSet}_confusionMatrix.svg'
                figurePathPng = figureFilePath + f'/{pseudoGroundTruth}_{comparisonSet}_confusionMatrix.png'
                plt.savefig(figurePathSvg, format='svg')
                plt.savefig(figurePathPng, format='png')
                plt.show()
                
                truePositive = confusionMatrix[0][0]
                falseNegative = confusionMatrix[0][1]
                falsePositive = confusionMatrix[1][0]
                trueNegative = confusionMatrix[1][1]
                sensitivity = truePositive / (truePositive + falseNegative)
                specificity = trueNegative / (trueNegative + falsePositive)
                accuracy = metrics.accuracy_score(dataDf[pseudoGroundTruth], dataDf[comparisonSet]) 
                recall = metrics.recall_score(dataDf[pseudoGroundTruth], dataDf[comparisonSet]) 
                precision = metrics.precision_score(dataDf[pseudoGroundTruth], dataDf[comparisonSet]) 

                print(combination)
                print('sensitivity', sensitivity)
                print('specificity', specificity)
                print('accuracy', accuracy)
                print('recall', recall)
                print('precision', precision)
                print()

        # getReagentDistributionPlot(dataDf=dataDf)
        # getMsMatchingPlot(dataDf=dataDf)
        getConfusionMatrix(dataDf=dataDf)
            
    def getPromisingReactions(dataDf):
        promisingReactions = []
        reagents = []
        #Finding promsing reactions (where both MS and NMR show good candidacy)
        for _, sample in enumerate(dataDf['reactionId']):
            if str(dataDf['humanMsLabel'][_]) == '2' and str(dataDf['humanNmrLabel'][_]) == '1':
                reactionObject = retrieveReactionObject(sample)
                reactionId = reactionObject.unique_identifier

                reagentList = reactionObject.reagents

                metal = None
                amine = None
                aldehdye = None
                for reagent in reagentList:
                    if reagent.__class__.__name__ == 'Diamine':
                        amine = reagent.name
                    elif reagent.__class__.__name__ == 'Monoaldehdye':
                        aldehdye = reagent.name
                    elif reagent.__class__.__name__ == 'Metal':
                        metal = reagent.name 

                promisingReactions.append(reactionId)
                reagents.append((metal, amine, aldehdye))
        tableToSave = {
            'reactionNumber': [],
            'metal': [],
            'amine': [],
            'aldehdye': []
        }
        for reactoinReagents, reaction in zip(reagents, promisingReactions):
            tableToSave['reactionNumber'].append(reaction)
            tableToSave['metal'].append(reactoinReagents[0])
            tableToSave['amine'].append(reactoinReagents[1])
            tableToSave['aldehdye'].append(reactoinReagents[2])

        csvPath = 'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/Raw Figures/MainResearchPaper/DecisionMaker/humanLabelling/successfulReactions.csv'
        dfToSave = pd.DataFrame.from_dict(tableToSave).to_csv(csvPath)
    data = collectData()
    dataDf = pd.DataFrame.from_dict(data)
    getVisualData(dataDf=dataDf)
    # getPromisingReactions(dataDf)

def getMsAndNmrFigures(parameters, dataLocations):
    """Iterating through the reactions to get their NMR and MS spectra and to save for automated figure generation."""
    
    def getDictionaryKeyNmr(dataLocations, nmrSample):
        """Returns the number of the sample in the batch. This is used as a key."""
        batchNumber, nmrSampleNumber = nmrSample[5:].split("-")
        return int(nmrSampleNumber)

    def getMsSample(datalocations, nmrSample, batchSample):
        """Returns the Ms sample file name."""
        batchSize = combinationParameters.batchSize
        standardReactionId = combinationParameters.standardReactionIdx
        batchNumber, nmrSampleNumber = nmrSample[5:].split("-")
        if int(nmrSampleNumber) == 1:
            msSample = str(standardReactionId) + 'batch' + batchNumber + '.raw'
        else:
            reactionNumber = (int(batchNumber))*(batchSize-1) + (int(nmrSampleNumber)-1)
            msSample = str(reactionNumber) + '.raw'

        return msSample 
    
    def getReactionID(spectra:str):
        "returns the reaction ID to then be looked up in the expectedMsPeaks dicionary"
        spectraName = spectra[:-4]
        if 'batch' in spectraName:
            spectraName = str(combinationParameters.standardReactionIdx + 1)
    
        return spectraName

    
    #Importing synthesis_bots.utils.nmr.processing
    nmrProcessingPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/dependencies/modules/synthesis_bots/utils/nmr/processing.py'
    spec = importlib.util.spec_from_file_location('nmrProcessing', nmrProcessingPath)
    nmrProcessing = importlib.util.module_from_spec(spec)
    sys.modules['nmrProcessing'] = nmrProcessing
    spec.loader.exec_module(nmrProcessing)

    #Importing synthesis_bots.utils.nmr.acquisition
    nmrAcquisitionPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/dependencies/modules/synthesis_bots/utils/nmr/acquisition.py'
    spec = importlib.util.spec_from_file_location('nmrAcquisition', nmrAcquisitionPath)
    nmrAcquisition = importlib.util.module_from_spec(spec)
    sys.modules['nmrAcquisition'] = nmrAcquisition
    spec.loader.exec_module(nmrAcquisition)

    #Saving toml with parameters
    generateToml(parameters=parameters)

    #Loading predicted masses
    expectedMsPeaksPath = dataLocations['expectedMsPeaksData']
    with open(expectedMsPeaksPath) as f:
        expectedMsPeaks = json.load(f)
    
    batchFiles = dataLocations['reactionData']
    batchSamples = os.listdir(batchFiles)

    for batch in batchSamples:
        batchDataPath = dataLocations['reactionData'] + '/' + batch
        batchNmrDataPath = batchDataPath + '/NmrData'
        batchMsDataPath = batchDataPath + '/MsData'
        nmrSampleFiles = getFilesOrFolders('batch', batchNmrDataPath)
        batchFigureFolderPath = batchDataPath + '/ArchiveData'

        #Loading NMR batch experimens
        nmrExperimentsPath = batchDataPath + '/nmrInputFile.json' 
        with open(nmrExperimentsPath, 'r') as f:
            nmrExperimentsDictionary = json.load(f)

        for nmrSample in nmrSampleFiles:
    
            #Ms Sample information
            nmrDictionaryKey = getDictionaryKeyNmr(dataLocations, nmrSample)
            msSample = getMsSample(dataLocations, nmrSample, batch)
            print(msSample)
            msExperimentName = getReactionID(spectra=msSample)
            msExperiment = expectedMsPeaks[msExperimentName]
            msFile = batchMsDataPath + '/' + msSample
            
            #Nmr Sample information
            nmrFile = batchNmrDataPath + '/' + nmrSample
            nmr = nmrProcessing.NMRExperiment(nmrAcquisition.FOURIER.open_experiment(nmrFile))
            nmrExperiment = nmrExperimentsDictionary[f'{nmrSample}']

            #checking tha the spectra exist
            if os.path.exists(msFile):
                msFileFigurePath = batchFigureFolderPath + '/MS' + msExperimentName + '.png'
                if not os.path.exists(msFileFigurePath): 
                    #Taking MS spectra
                    singleMsDecision(parameters=parameters,
                                    dataLocations=dataLocations,
                                    experimentName=msExperimentName,
                                    msExperiment=msExperiment,
                                    msFile= msFile,
                                    displayFigure=False,
                                    saveFig=True,
                                    figureFolderPath = batchFigureFolderPath
                                    )

                    #Taking NMR spectra
                    reagentPeaks = pickPeaks(parameters=parameters, 
                                            experimentName=msExperimentName, 
                                            nmrExperiment=nmrExperiment,
                                            nmrFilePath=nmrFile,
                                            saveFig=True,
                                            figureFolderPath = batchFigureFolderPath
                                            )

def optimizeReagentNmrFigure(parameters, dataLocations):
    """Makes the NMR figures as pretty as possible"""

    startingMaterialFilePath = dataLocations['startingMaterialsData']

    #Saving toml with parameters
    generateToml(parameters=parameters)

    nmrExperimentsJsonPath = startingMaterialFilePath + '/nmrInputFile.json'
    with open(nmrExperimentsJsonPath) as f:
        nmrExperiments = json.load(f)


    startingMaterialNmrFilePath  = startingMaterialFilePath + '/NmrData'

    startingMaterialNmrFile = getFilesOrFolders('reagentAnalysis', startingMaterialNmrFilePath)

    intensityData = {
        'reagentAnalysis-09': (3, 4),
        'reagentAnalysis-10': (3, 4),
        'reagentAnalysis-13': (1, 1.75)
    }

    for spectra in startingMaterialNmrFile:
        if spectra in nmrExperiments.keys():
            experimentName = spectra
            nmrExperiment = nmrExperiments[spectra]
            nmrFilePath = startingMaterialNmrFilePath + '/' + spectra
            figureFolderPath = startingMaterialFilePath + '/ArchiveData'
            print(spectra)

            if spectra in intensityData.keys():
                pickPeaks(parameters=parameters, 
                            experimentName=experimentName, 
                            nmrExperiment=nmrExperiment, 
                            nmrFilePath=nmrFilePath, 
                            saveFig=True, 
                            figureFolderPath=figureFolderPath, 
                            displayFigure=True,
                            intensity_region=intensityData[spectra],
                            overwriteExistingFigure=True)
            else:
                pickPeaks(parameters=parameters, 
                            experimentName=experimentName, 
                            nmrExperiment=nmrExperiment, 
                            nmrFilePath=nmrFilePath, 
                            saveFig=True, 
                            figureFolderPath=figureFolderPath, 
                            displayFigure=False,
                            overwriteExistingFigure=True)

# Processing raw data. This includes dividing it into relevant folders, and generating json input files for decision maker.

# parseRawData(parameters, dataLocations)

# Parameters have to be saved as a toml before anything else can be done.

# generateToml(parameters)
# nmrPickStartingMaterialsPeaks(parameters, dataLocations)

batchPath = 'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/backup/ChemspeedPlatformAllVersions/V12/Workflows/Data/Reactions/batch1' 
# LCMS Parameters are first optimized to get the greates number of positive hits. 
#This information is then used to help chemist manualy classify reactions. 
#Both human and LCMS labels are then used to optimize NMR parameters

# optimizeMSParametersSingleRun(dataLocations=dataLocations)
# optimizeMSParameters(dataLocations=dataLocations, parameterID=0)
# analyseMsParametersData()


# The second step is to manualy classifiy the reaction based on NMR and MS decisions.

# getHumanExpertLables(parameters=parameters, dataLocations=dataLocations)

# msFigurePath = 'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/Raw Figures/MainResearchPaper/humanLabeling/PossibleMsLabels'
# msReactions = [26]
# for reactionNumber in msReactions:
#     getSingleMsSpectraForPaper(reactionNumber, msFigurePath)

# nmrFigurePath = 'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/Raw Figures/MainResearchPaper/humanLabeling/PossibleNmrLables/msSpectra'
# nmrReactions = [34, 47, 51, 52, 52]
# for reactionNumber in nmrReactions:
#     getSingleMsSpectraForPaper(reactionNumber, nmrFigurePath)

# msParameterOptimization.

# analyseHumanLabels()

# optimizeReagentNmrFigure(parameters=parameters, dataLocations=dataLocations)


# compareDecisionMakerToHumanLables(parameters, dataLocathl/ions, batchPath)
# decisionMakerBatchPass(parameters, dataLocations, batchPath)





# getMsAndNmrFigures(parameters=parameters, dataLocations=dataLocations)