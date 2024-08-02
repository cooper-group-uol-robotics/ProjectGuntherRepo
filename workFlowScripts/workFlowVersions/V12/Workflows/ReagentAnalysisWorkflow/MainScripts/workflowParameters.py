"""
This python file handles all user tunable parameters in this workflow. The only things thats missing is the ability for the user to define chemical subclasses without having to pythonicaly type out a python classes for them.
"""

import os
import importlib.util
import sys

#importing check_manager module.
rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])
checkManagerPath = strCWD + '/Python_Modules/check_manager.py'
spec = importlib.util.spec_from_file_location('cm', checkManagerPath)
cm = importlib.util.module_from_spec(spec)
sys.modules['cm'] = cm
spec.loader.exec_module(cm)

#The parameters of the analysis of reagents is the same as for the combination experiment. 
#The only difference is that we want the NMR of the pure reagents. 
#We have to therefore, calculate the concentration of a reagent in a combination sample.

rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])
combinationParametersPath = strCWD + '/Reaction_Combinations_workflow/Main_Scripts/workflowParameters.py'
spec = importlib.util.spec_from_file_location('combinationParameters', combinationParametersPath)
combinationParameters = importlib.util.module_from_spec(spec)
sys.modules['combinationParameters'] = combinationParameters
spec.loader.exec_module(combinationParameters)

#paths of various CSVs and JSONs.

generatedCsvPath =  strCWD + '/Reagent_Analysis_Workflow/Generated_CSVs/'                                                                                   #The path where the chemist will look at for experiment information.
generatedPicklePath = strCWD + '/Reagent_Analysis_Workflow/Generated_pickles/'                                                                              #The path where any generated python objects will be saved. (For the reagent analysis workflow this is not used).
generatedJsonPath = strCWD + '/Reagent_Analysis_Workflow/Generated_NMR_JSONs/'                                                                              #The path where the NMR JSON will be saved.
generatedMsCsvPath = strCWD + '/Reagent_Analysis_Workflow/Generated_MS_CSV/'                                                                                #The path where the MS csv will be saved.
logsPath = strCWD + '/Reagent_Analysis_Workflow/Logs/'


#Concentrations used in experiment.

metalConcentration = combinationParameters.metalConcentration                                                                                               #The concentration (mM) of the metal in the stock vials, as if it had a coordination number of 6 (the script calcualtes the volume based on the 6:actual coordination number ratio -> see script_classes.py).
diamineConcentration = combinationParameters.diamineConcentration                                                                                           #The concentration (mM) of the metal in the stock vials.
monoaldehdyeConcentration = combinationParameters.monoaldehdyeConcentration                                                                                 #The concentration (mM) of the monoaldehyde in the stock vials.

#Volumes used in workflow.

minTransferVolume = combinationParameters.minTransferVolume                                                                                                 #This is the volume, in microlitre, in the stock vials that Gunther can not physicaly aspirate.
bufferVolume = combinationParameters.bufferVolume                                                                                                           #This is the buffer volume, as Gunther does not perfectly aspirate X microlitres of sample.
mosquitoSampleVolume = combinationParameters.mosquitoSampleVolume                                                                                           #This is the volume, in microlitres, of a reaction sample in a mosquito rack well (for later use in the cystalography workflow).
nmrSampleVolume = combinationParameters.nmrSampleVolume                                                                                                     #This is the volume, in microlitres, of a reaction sample in a NMR tube.
msSampleVolume = combinationParameters.msSampleVolume                                                                                                       #This is the volume, in microlitres, of a reaction sample in a MS vial.                                                                    
reactionVolume = combinationParameters.reactionVolume                                                                                                       #This is the volume, in microlitres, a reaction sample must have for all the needed analysis.

reactionVolumeTransferVolumeRatio = combinationParameters.reactionVolumeTransferVolumeRatio                                                                 #This is a ratio between the transfer volume of a reagent and the total volume in a reaction. Implies -> change in final volume = change in transfer volume (this ratio can be changed, but currently using 1500/200 as it gives good NMR results). 
reactionVialTransferVolume = combinationParameters.reactionVialTransferVolume                                                                               #The volume in microlitres to transfer from stock vials to sample vials (this could be added as an attribute to the chemical class, but not necessary for this analysis).

#Information on Batch and sample parameters.

subTypeInReactionTuple = combinationParameters.subTypeInReactionTuple                                                                                       #This is a tuple showing the number of chemical subtypes to include in a reaction. The length of the vector changes depending on the number of chemical subtypes in the whole chemical space. For my current project: (Metal=1, Diamine=1, Monoaldehdye=1). There is a method that allows you to show the index and the chemical subtype (see ReactionSpace.showSubtypesIndex() ).    
batchSize = combinationParameters.batchSize                                                                                                                 #This is the number of reactions (combinations), the chemspeed platform can handle.
standardReactionIdx = combinationParameters.standardReactionIdx                                                                                             #This is the index where the standard reaction is found in the reaction space (used in ReactionSpace.addStandardReaction() method).

#NMR and LCMS Experiment parameters.

parameters = combinationParameters.parameters                                                                                                               #This is the type of NMR experiment to be run.
numScans = combinationParameters.numScans                                                                                                                   #This is the number of scans the NMR experiment should carry out.
ppThershold = combinationParameters.ppThershold                                                                                                             #This is a setting for the MULTISUPPDC_f program.
fieldPresat = combinationParameters.fieldPresat                                                                                                             #This is a setting for the MULTISUPPDC_f program.
solvent = combinationParameters.solvent                                                                                                                     #Solvent used for NMR smaple.
msInjectionVolume = combinationParameters.msInjectionVolume                                                                                                 #This is the injection volume (microlitre) for the UV-Vis / MS machine. 

#Email Addresses.

emailPrinter = combinationParameters.emailPrinter                                                                                                           #This is the email adress to print things.
emailGunther = combinationParameters.emailGunther                                                                                                           #This is the email adress which all workflow machines have acess to. Email is how the workflow is coordinated.

#Chemical Space definition.

chemicalsInWholeSpace = combinationParameters.chemicalsInWholeSpace                                                                                         #The different chemicals the swing platform can handle.
chemicalsToRemove = combinationParameters.chemicalsToRemove                                                                                                 #The chemicals that should not be part of the combination calcualtion.

#Safety checks to preform during workflow.

safetyChecks = [
    cm.VisualBoolCheck('Please add reagent vials in the right place and run get_batch_spaces_csvs() again.', 'Have the reagents vials been added in the right zone? (1=Yes, 0=No): ' ),
    cm.VisualBoolCheck('Please top up CH2Cl2 vial and added it in the right place and run get_batch_spaces_csvs() again.', 'Has the CH2Cl2 vial been added and topped up? (1=Yes, 0=No): ' ),
    cm.VisualBoolCheck('Please top up CHCN3 and run get_batch_spaces_csvs() again.', 'Is there enough CHCN3 left in the resevoir? (1=Yes, 0=No): '),
    cm.VisualBoolCheck('Please empty special waste and run get_batch_spaces_csvs() again.', 'Is the special waste empty enough for one run? (1=Yes, 0=No): '),
    cm.VisualBoolCheck('Please add NMR tubes and make sure they\'re in the right place and run get_batch_spaces_csvs() again.', 'Have all NMR tubes been added, and are the two green stickers aligned? (1=Yes, 0=No): '),
    cm.VisualBoolCheck('Please add MS vials and run get_batch_spaces_csvs() again.', 'Have all the MS vials been added? (1=Yes, 0=No): '),
    cm.VisualBoolCheck('Please add measured masses into the csv and run get_batch_spaces_csvs() again.', 'Have all the measured masses been added to the reagent_mass_to_measure csv? (1=Yes, 0=No): '),
    cm.VisualBoolCheck('Please add the Mosquito rack and run get_batch_spaces_csvs() again.', 'Has the mosquito plate been added to the workflow? (1=Yes, 0=No): '),
]
