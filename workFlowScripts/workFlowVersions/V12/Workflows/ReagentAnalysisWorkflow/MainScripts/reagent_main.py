"""
This script is responsible for analysis of just the reagents used in a workflow.

Structure of the programme:
- Subdivided into 2 main functions:
    1) calculateRequiredMasses()
    2) calculateRequiredVolume()

The time line (psuedo logic) ias the following:
 - Define the concentration of the different chemical subtypes.
 - Calculate the concentrations of the reagents in the chemical vials (and hence in the analysis samples).
 - Calculate the masses to measure to hit that concentation for a volume in a vial.
 - Generate a csv with the reagents and the masses need to measure.
 - Once the chemist has inputted the masses they have measured, calculate the volume of CH2Cl2 and CH3CN to make up to the final concentration.
 - Generate a csv for the chemspeed with the volumes required.
 - Generate a json for the NMR analysis of the reagents (and send them via email).
 - Generate a csv for the MS analysis of the reagents (and send them via email).

All parameters are handled in the 'workflowParameters.py'.
All safety checks are handled by the 'check_manager.py'
The 'main.py' just manages the instantiation of different classes and unlike the combination workflow it also handles the calcualtion of volumes and masses.

"""

import pandas as pd
import os
import json
import sys 
sys.path.append('Python_Modules')
import script_classes as sc
import check_manager as cm


#Updating the USERSELECTION class depending on the use selected parameters in 'workflowParameters.py'.

rawCWD = os.getcwd()
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])
workFlowParametersPath = strCWD + '/Reagent_Analysis_Workflow/Main_Scripts/workflowParameters.py'
sc.USERSELECTION.udpateParameters(workFlowParametersPath)
print(f'the file location is {sc.USERSELECTION.generatedCsvPath}')

#c1v1 = c2v2

V1 = sc.USERSELECTION.reactionVialTransferVolume/1000000                                                                                                #The volume of reagent added to a reaction vial (in litres)
V2 = sc.USERSELECTION.reactionVolume/1000000                                                                                                            #The final volume of the reaction vial (in litres)


#Getting the concentrations in the reaction vials and hence in the NMR Samples.

metalConcentrationInReactionVial = sc.USERSELECTION.metalConcentration/1000 * V1 / V2                                                                   #Concentration (M) of the metal in the reaction vial
dialdehydeConcentrationInReactionVial =  sc.USERSELECTION.dialdehdyeConcentration/1000 * V1 / V2                                                        #Concentration (M) of the dialdhdye in the reaction vial
diamineConcentratoinInReactionVial = sc.USERSELECTION.diamineConcentration/1000 * V1 / V2                                                               #Concentration (M) of the dimaine in the reaction vial 
monoaldehdyeConcentrationInReactionVial = sc.USERSELECTION.monoaldehdyeConcentration/1000 * V1 / V2                                                     #Concentration (M) of the monoamine in the reaction vial 

#The list of reagents in order (copy pasted from main workflow).

reagents = sc.USERSELECTION.chemicalsInWholeSpace                                                                                                       #The reagents the chemspeed platform can handle.
chemicalsToRemove = sc.USERSELECTION.chemicalsToRemove                                                                                                  #The reagents that should not be included in the combination experiment.

#A dict to be converted to a data frame.

reagentSpace = {
    'Chemical_index': [],                                                                                                                               #The numerical identy of the  reagent -> the identiy matches with the vial location on the chemspeed.
    'Chemical': [],                                                                                                                                     #A list of the reaegent names.
    'Mass to measure (in grams)': [],                                                                                                                   #A list of the required masses to reach the final concentration in the reaction vials (NMR tubes).
    'Actual mass measured': []                                                                                                                          #A list of masses measured by the chemist.
}                                                                                               

def _calculateMassesToMeasure():
    """Calculates the required masses to hit the required concentrations for analysis"""
    for chemicalIdx, chemical in enumerate(reagents):
        #concentration = moles / volume
        #moles = mass / molecular weight
        #concentration = (mass / molecular weight) / volume
        
        #Getting final concentrations depending on the chemical subtype.
        
        if  'Metal' == chemical.__class__.__name__:
            finalConcentration = metalConcentrationInReactionVial                                                                                       #This is the newly calculated metal concenrtation in the NMR samples.

        if 'Dialdehyde' == chemical.__class__.__name__:
            finalConcentration = dialdehydeConcentrationInReactionVial                                                                                  #This is the newly calculated dialdehyde concentration in the NMR smaples.

        if 'Diamine' == chemical.__class__.__name__:
            finalConcentration = diamineConcentratoinInReactionVial                                                                                     #This is the newly calculated diamine concentation in the NMR samples.

        if 'Monoaldehdye'== chemical.__class__.__name__:
            finalConcentration = monoaldehdyeConcentrationInReactionVial                                                                                #This is the newly calcualted monoaldehyde concentration in the NMR samples.

        #Removing chemicals not part of the combination space.
        
        for removalChemical in chemicalsToRemove:
            if chemical.name == removalChemical.name:                                                                                                   #Comparision is based on reagent name.
                finalConcentration = 0

        #Calculating the required masses.
                
        mass = (finalConcentration * V2) * chemical.molecularWeight                                                                                     #mass = (concentration * volume) * molecular weight.         Concentration has to be converted to M.         Volume has to be converted to litres.
        
        #Updating the dictionary to be saved as a csv.

        reagentSpace['Mass to measure (in grams)'].append(mass)                                                                                         #These are various columns in the generated csv.
        reagentSpace['Chemical'].append(chemical.name)
        reagentSpace['Chemical_index'].append(chemicalIdx+1)

    reagentSpace['Actual mass measured'] = [None if mass != 0 else 0 for mass in reagentSpace['Mass to measure (in grams)']]                            #Adding an empty space if the reagent mass must be taken. Adding a 0 if not.

    #Reading the dictionary as a dataframe and saving it as a csv and pickle

    df = pd.DataFrame.from_dict(reagentSpace).set_index('Chemical_index')                                                                               
    csvPath = sc.USERSELECTION.generatedCsvPath + 'reagentMassToMeasure.csv'
    df.to_csv(csvPath)

def _sendCsvViaEmail():
    """Sends the generated csv via email to then be printed by the chemist."""
    csvPath = sc.USERSELECTION.generatedCsvPath + 'reagentMassToMeasure.csv'
    sc.sendDocumentToEmail(documentPath=[csvPath], emailAdress=sc.USERSELECTION.emailPrinter, emailSubject='Reagent Analysis Masses to Measure', successMessage='Reagent CSV successfully sent', failedMessage='Email sending failed, manualy send reagent masses')         #This is a user made function (see script_classes.py).

def calculateRequiredMasses():
    """Generates a csv with masses to measure and sends them to be printed off"""
    _calculateMassesToMeasure()                                                                                                                         #Functions are underscored, as they should not be directly called byt the user. Having a function to call two different functions looks useless. This was done just to further abstract the functions. 
    _sendCsvViaEmail()
    
#Setting up the check manager.

checkManger = cm.CheckManager()                                                                                                                         #This is a simple check list to ensure the setup is all good.
checkManger.addChecks(sc.USERSELECTION.safetyChecks)

def _generateChemSpeedCsv():
    """Generates the Chemspeed readable csv to make up stock solutions with the right concentrations for analysis"""

    flag =  checkManger.runcheckList()                                                                                                                  #Running the check list (see check_manager.py).

    if flag == True:
        
        #loading the user's measured masses.
        
        csvPath1 = sc.USERSELECTION.generatedCsvPath + 'reagentMassToMeasure.csv'
        csvPath2 = sc.USERSELECTION.logsPath + 'reagentMassToMeasure.csv'
        df = pd.read_csv(csvPath1, index_col=0)

        CH3CNVolumeInitial = []                                                                                                                          #Volumes are divided into two different parts 1) Generation of the pseudo stock solution 2) Generation of the pseudo reactoin vial (see Reaction_Combinatinos_workflow for a better understanding). The initial volumes are used for the 'pseudo stock solution'.
        CH2Cl2VolumeInitial = []
        CH3CNVolumeFinal = []                                                                                                                            #This is the volume to reach the final volume in a reaction vial (i.e. making up the 'pseudo reaction vial').
        for chemicalIdx, chemical in enumerate(reagents):                                                                                                #Getting the concentration of the chemical subtypes.
            if  'Metal' == chemical.__class__.__name__:                                                                                                  #This is messy, if you have to create a different combination, you have to not only add new classes, but you have to update this section and the next too. 
                finalConcentration = metalConcentrationInReactionVial                                                                                    #This is the newly calculated metal concentration in the NMR samples.

            if 'Dialdehyde' == chemical.__class__.__name__:
                finalConcentration = dialdehydeConcentrationInReactionVial                                                                               #This is the newly calculated dialdhdye concentration in the NMR samples.

            if 'Diamine' == chemical.__class__.__name__:
                finalConcentration = diamineConcentratoinInReactionVial                                                                                  #This is the newly calculated diamine concentration in the NMR samples.

            if 'Monoaldehdye'== chemical.__class__.__name__:
                finalConcentration = monoaldehdyeConcentrationInReactionVial                                                                             #This is the newly calculated monoaldhdye concentration in the NMR samples.

            massMeasured = df.iloc[chemicalIdx, 2]                                                                                                      #Obtaining the chemist's measured mass for the reagent.
            molecularWeight = chemical.molecularWeight
            
            #calculating the required mass.

            if finalConcentration != 0:                                                                                                                 #Getting rid of the math x/0 error.
                #volume = (mass / molecular weight) / concentration
                finalVolume = (massMeasured / molecularWeight / finalConcentration)                                                                     #Calculating the final volume required.
                
                solubilityCCl2H2, solubilityCH3CN = chemical.solubility            
                if solubilityCCl2H2 == 0 and solubilityCH3CN == 0:                                                                                      #Some chemicals my be insoluble in both solvents -> solubility tuple = (0,0).
                        CH2Cl2VolumeInitial.append(0)
                        CH3CNVolumeInitial.append(0)
                        CH3CNVolumeFinal.append(0) 

                else:
                    volumeCCl2H2Initial = (solubilityCCl2H2/(solubilityCCl2H2+solubilityCH3CN))*V1                                                      #The final CH2Cl2 volume depends on the solubility ratio of the chemical in CH3CN: CH2Cl2 in the transfer volume (in the combination workflow, the chemical is first made into a stock solution and then topped up with CH3CN in the reaction vial).
                    volumeCH3CNInitial = (solubilityCH3CN/(solubilityCH3CN+solubilityCCl2H2))*V1                                                        #This is the initial reagent conditions. In the combination workflow this is equivalent to making up the stock solutions.
                    volumeCH3CNFinal = finalVolume - (volumeCH3CNInitial + volumeCCl2H2Initial)                                                         #Calculating the volume of acetonitrle in a pseuod reaction vial (in the combination workflow this is equivilant as topping up the reaction / combination vial).


                    CH2Cl2VolumeInitial.append(volumeCCl2H2Initial*1000000)                                                                             #Updating the various volumes / 1000000 to convert to microlitres.
                    CH3CNVolumeInitial.append(volumeCH3CNInitial*1000000)
                    CH3CNVolumeFinal.append(volumeCH3CNFinal*1000000)

            else:                                                                                                                                       #This is used to remove any potential math errors (x/0)
                CH2Cl2VolumeInitial.append(0)
                CH3CNVolumeInitial.append(0)
                CH3CNVolumeFinal.append(0)
        
        df['CH3CN_initial'] = CH3CNVolumeInitial                                                                                                        #Setting the calculated lists as df columns
        df['CCl2H2_initial'] = CH2Cl2VolumeInitial
        df['CH3CN_final'] = CH3CNVolumeFinal

        df.to_csv(csvPath1)                                                                                                                             #Saving the dataframe as a csv in generated csv folder.
        df.to_csv(csvPath2)                                                                                                                             #Saving the dataframe as a csv in the logs folder.
        print('')
        print('REAGENT SPACE SUCCESFULY GENERATED')
        

def _generateNmrJson():
    """Generates the json to be used by the NMR autosampler."""

    jsonPath = sc.USERSELECTION.generatedJsonPath + 'reagentAnalysis.json' 
    jsonToSave = {}

    for reagentIdx, reagent in enumerate(reagents):                                                                                                     #Iterating through the reagents and adding a new MNR sample for each.  
        jsonToSave[f'{reagentIdx+1}'] = {
        "sample_info": reagent.name,
        "solvent": sc.USERSELECTION.solvent,                                                                                                            #The major solvent in the experiment (see USERSELECTION class in script_classes.py).
        "nmr_experiments": [
                    {
                        "parameters": sc.USERSELECTION.parameters,                                                                                      #Different parameters that control how the NMR spectra is taken. These are Bruker specific.
                        "num_scans": sc.USERSELECTION.numScans,
                        "pp_threshold": sc.USERSELECTION.ppThershold,
                        "field_presat": sc.USERSELECTION.fieldPresat
                    }
                ]
        }
    
    with open(jsonPath, 'w', newline="\n") as jsonOutput:                                                                                               #Saving the genrated NMR dictionary as a json to be sent and read by the NMR autosampler.  
        json.dump(jsonToSave, jsonOutput, indent=4)

def _generateMsCsv():
    """Generates the csv to be used by the LCMS autosampler."""
    
    csvPath = sc.USERSELECTION.generatedMsCsvPath + 'reagentAnalysis.csv'

    csvDictionary = {                                                                                                                                   #The dictionary to be saved as a csv.                                                                              
            'INDEX': [],                                                                                                                                #An index for the autosampler is reqruired.
            'fileName': [],                                                                                                                             #This is the file name for the samples UV and MS spectra.
            'FILE_TEXT': [],                                                                                                                            #IDK what this does, I think it just makes the sample spectra more human interpretable.
            'MS_FILE': [],                                                                                                                              #This is the name of the file used for MS protols (i.e. injection speeds, M/Z range).
            'MS_TUNE_FILE': [],                                                                                                                         #Similar to the MS_file its a file name. The file is generated by the Water's LCMS machine when a user wants to run the same spectra over different samples.
            'INLET_FILE': [],                                                                                                                           #Agian this is similar to the two previous.
            'SAMPLE_LOCATION': [],                                                                                                                      #This is the location of the sample in the LCMS rack. In this case, the reaction order in the batch space is the same as the the sample location indx. 
            'INJ_VOL': []                                                                                                                               #This is the injection volume for MS / UV-Vis.
            }

    #Adding sample info for each reagent -> 1 row = 1 reagent.

    for reagentIdx, reagent in enumerate(reagents):                                                                                                     #Iterating through the reagents and adding a new table row for each.
        textVar = 'reagent' + str(reagentIdx+1)
        csvDictionary['INDEX'].append(reagentIdx + 1)
        csvDictionary['fileName'].append(textVar)
        csvDictionary['FILE_TEXT'].append(textVar)                                                                                                      #The file name is the reagent numerical id (the index of the reagent in the list).
        csvDictionary['MS_FILE'].append('SupraChemCage')
        csvDictionary['MS_TUNE_FILE'].append('SupraChemCage')
        csvDictionary['INLET_FILE'].append('SupraChemCage')
        csvDictionary['SAMPLE_LOCATION'].append(f'1:{reagentIdx+1}')
        csvDictionary['INJ_VOL'].append(sc.USERSELECTION.msInjectionVolume)
    
    df = pd.DataFrame.from_dict(csvDictionary)                                                                                                          #Reading the dictionary as a dataframe to then save it as a csv.
    df.to_csv(csvPath, index=False)
    

def _sendFilesViaEmail():
    """Sends the NMR JSON and MS csv via email"""

    MsCsvPath = sc.USERSELECTION.generatedMsCsvPath + 'reagentAnalysis.csv'
    NmrJsonPath = sc.USERSELECTION.generatedJsonPath + 'reagentAnalysis.json'
    sc.sendDocumentToEmail(documentPath = [MsCsvPath, NmrJsonPath], emailAdress=sc.USERSELECTION.emailGunther, emailSubject='Reagent Analysis NMR json and MS CVS', successMessage='Json and CSV successfully sent', failedMessage='Email sending failed, manualy send MS CSV and NMR JSON manually')

    

def calculateRequiredVolume():
    """calculatest the required volumes of solvents to make up the sample and sends NMR JSON and MS csv to email."""
    _generateChemSpeedCsv()
    _generateMsCsv()
    _generateNmrJson()
    _sendFilesViaEmail()


#To run the workflow run one function at a time. After the calculateRequiredMasses() is run measured masses must be inputted into the csv before the next function can be run.

#calculateRequiredMasses()
#calculateRequiredVolume()
