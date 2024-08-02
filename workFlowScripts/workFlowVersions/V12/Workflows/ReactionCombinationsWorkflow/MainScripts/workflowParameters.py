"""
This python file handles all user tunable parameters in this workflow. The only things thats missing is the ability for the user to define chemical subclasses without having to pythonicaly type out a python classes for them.
"""

import os
import importlib.util
import sys

#importing scriptClasses module.
rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])
scriptClassesPath = strCWD + '/PythonModules/scriptClasses.py'
spec = importlib.util.spec_from_file_location('sc', scriptClassesPath)
sc = importlib.util.module_from_spec(spec)
sys.modules['sc'] = sc
spec.loader.exec_module(sc)

#importing checkManager module.
rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])
checkManagerPath = strCWD + '/PythonModules/checkManager.py'
spec = importlib.util.spec_from_file_location('cm', checkManagerPath)
cm = importlib.util.module_from_spec(spec)
sys.modules['cm'] = cm
spec.loader.exec_module(cm)

#Paths of various CSVs and JSONs.

rawCWD = os.getcwd()
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])
generatedCsvPath =  strCWD + '/ReactionCombinationsWorkflow/GeneratedCSVs/'                                                                          #The path where the chemist will look at for experiment information.
generatedPicklePath = strCWD + '/ReactionCombinationsWorkflow/GeneratedPickles/'                                                                     #The path where any generated python objects will be saved. (For the reagent analysis workflow this is not used).
generatedJsonPath = strCWD + '/ReactionCombinationsWorkflow/GeneratedNmrJSONs/'                                                                     #The path where the NMR JSON will be saved.
generatedMsCsvPath = strCWD + '/ReactionCombinationsWorkflow/GeneratedMsCSV/'                                                                       #The path where the MS csv will be saved.
logsPath = strCWD + '/ReactionCombinationsWorkflow/Logs/'                                                                                             #The path where the logs will be saved.

#Concentrations used in experiment.

metalConcentration = 20 * 1.5                                                                                                                           #The concentration (mM) of the metal in the stock vials, as if it had a coordination number of 6 (the script calcualtes the volume based on the 6:actual coordination number ratio -> see script_classes.py).
dialdehdyeConcentration = 0 * 1.5                                                                                                                       #The concentration (mM) of the dialdhyde in the stock vials.
diamineConcentration = 30 * 1.5                                                                                                                         #The concentration (mM) of the dimaine in the stock vials.
monoaldehdyeConcentration = 60 * 1.5                                                                                                                    #The concentration (mM) of the monoadldehyde in the stock vials.

#Volumes used in workflow.

minTransferVolume = 900                                                                                                                                 #This is the volume, in microlitre, in the stock vials that Gunther can not physicaly aspirate.
bufferVolume = 500                                                                                                                                      #This is the buffer volume, as Gunther does not perfectly aspirate X microlitres of sample.
mosquitoSampleVolume = 0                                                                                                                                #This is the volume, in microlitres, of a reaction sample in a mosquito rack well (for later use in the cystalography workflow).
nmrSampleVolume = 600                                                                                                                                   #This is the volume, in microlitres, of a reaction sample in a NMR tube.
msSampleVolume = 50                                                                                                                                     #This is the volume, in microlitres, of a reaction sample in a MS vial.                                                                    
reactionVolume = minTransferVolume + bufferVolume + mosquitoSampleVolume + nmrSampleVolume + msSampleVolume                                             #This is the volume, in microlitres, a reaction sample must have for all the needed analysis

reactionVolumeTransferVolumeRatio = 1500/200                                                                                                            #This is a ratio between the transfer volume of a reagent and the total volume in a reaction. Implies -> change in final volume = change in transfer volume (this ratio can be changed, but currently using 1500/200 as it gives good NMR results). 
reactionVialTransferVolume = reactionVolume / reactionVolumeTransferVolumeRatio                                                                         #The volume in microlitres to transfer from stock vials to sample vials (again, this could be added as an attribute to the chemical class, but it does give up flexibility).

#Information on Batch and samples parameters.

subTypeInReactionTuple = (1,1,1)                                                                                                                        #This is a vector showing the number of chemical subtypes to include in a reaction. The length of the vector changes depending on the number of chemical subtypes in the whole chemical space. In this case its (Metal=1, Diamine=1, Monoaldehdye=1). There is a method that allows you to show the index and the chemical subtype (see ReactionSpace.showSubtypesIndex() ).    
batchSize = 48                                                                                                                                          #This is the number of reactions (combinations), the chemspeed platform can handle.
standardReactionIdx = 23                                                                                                                                #This is the index of where the standard reaction is found in the reaction space (uused in ReactionSpace.addStandardReaction() method).

#NMR and LCMS Experiment parameters.

parameters = 'MULTISUPPDC_f'                                                                                                                            #This is the type of NMR experiment to be run.
numScans = 64                                                                                                                                           #This is the number of scans the NMR experiment should carry out.
ppThershold = 0.008                                                                                                                                     #This is a setting for the MULTISUPPDC_f program.
fieldPresat = 10                                                                                                                                        #This is a setting for the MULTISUPPDC_f program.
solvent = 'CH3CN'                                                                                                                                       #Main Solvent used for NMR smaples.
msInjectionVolume = 1                                                                                                                                   #This is the injection volume (microlitre) for the LCMS sample. 

#Email Addresses.

emailPrinter = 'printbw1@liverpool.ac.uk'                                                                                                               #This is the email adress to print things (such as the stock space).
emailGunther = 'chemspeedgunther@gmail.com'                                                                                                             #This is the email adress which all workflow machines have acess to. Email is how the workflow is coordinated.

#Chemical Space definition. These are the different reagents that the chemspeedplatform is capable of handling.

chemicalsInWholeSpace = [                                                                                                                                                                           
        sc.Metal(name='Iron(II) tetrafluoroborate hexahydrate', CAS='13877-16-2', molecularWeight=337.55, solubility=(0,1), price=6, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= metalConcentration, noCoordinationSites=(6), newChemical=True),
        sc.Metal(name='Zinc tetrafluoroborate', CAS='27860-83-9', molecularWeight=239, solubility=(0,1), price=1.348,  volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=metalConcentration, noCoordinationSites=(6), newChemical=True),
        sc.Metal(name='Yittrium(III) trifluoromethanesulfonate', CAS='52093-30-8', molecularWeight=536.11, solubility=(0,1), price=17.2,  volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=metalConcentration, noCoordinationSites=(6), newChemical=True), #yttrim has coordination numbers between 6-9 (in our experiment well just assume 6)
        sc.Metal(name='Tetrakis(acetonitrile)copper(I) tetrafluoroborate', CAS='15418-29-8', molecularWeight=314.56, solubility=(0,1), price=33,  volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=metalConcentration, noCoordinationSites=(4), newChemical=True), #copper has coordination number 4
        sc.Metal(name='Silver tetrafluoroborate', CAS='14104-20-2', molecularWeight=194.67, solubility=(0,1), price=28.3,  volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=metalConcentration, noCoordinationSites=(4,6), newChemical=True), #silver has coordiantion numebrs 4, 5, or 6 (in our experiment well just assume 4 and 5)
        sc.Dialdehyde(name='1,10-Phenanthroline-2,9-dicarbaldehyde', CAS='57709-62-3', molecularWeight=236.23, solubility=(0,1), price=165, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=dialdehdyeConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=True),
        sc.Dialdehyde(name='Pyridine-2,6-dicarbaldehyde', CAS='5431-44-7', molecularWeight=135.122, solubility=(0,1), price=59, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=dialdehdyeConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=True),
        sc.Diamine(name='2,2\'-(Ethane-1,2-diyl)dianiline', CAS='34124-14-6', molecularWeight=212.297, solubility=(0,1), price=16, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= diamineConcentration, noCoordinationSites= 2, noImineReactionSites=2, newChemical=True),
        sc.Diamine(name='2,2\'-(Ethane-1,2-diylbis(oxy))diethanamine', CAS='929-59-9', molecularWeight=148.21, solubility=(3,1), price=0.64, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= diamineConcentration, noCoordinationSites = 2, noImineReactionSites=2, newChemical=True),
        sc.Diamine(name= '2,2\'-Oxydiethanamine', CAS='2752-17-2', molecularWeight=104.15, solubility=(0,1), price=40, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= diamineConcentration, noCoordinationSites= 2, noImineReactionSites=2, newChemical=True),
        #sc.Diamine(name='1,4-Phenylenedimethanamine', CAS='539-48-0', molecularWeight=136.194, solubility=(1,0), price=4, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= DIAMINE_CONCENTRATION,, noCoordinationSites= 2, noImineReactionSites=2, newChemical=True), to be replaced
        sc.Diamine(name='4,4\'-Methylenedianiline', CAS='101-77-9', molecularWeight=198.26, solubility=(0,1), price=0.506, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=diamineConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=True),
        sc.Diamine(name='m-Xylylenediamine', CAS='1477-55-0', molecularWeight=136.19, solubility=(0,1), price=13, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=diamineConcentration, noCoordinationSites= 2, noImineReactionSites=2, newChemical=True),
        sc.Diamine(name='Adamantane-1,3-diamine', CAS='10303-95-4', molecularWeight=166.27, solubility=(1,0), price=140, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=diamineConcentration, noCoordinationSites= 2, noImineReactionSites=2, newChemical=True),
        sc.Diamine(name='4,4\'-(9H-AdamantaeFlurene-9,9diyl)dianiline', CAS='15499-84-0', molecularWeight=348.44, solubility=(0,1), price=10, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=diamineConcentration, noCoordinationSites= 2, noImineReactionSites=2, newChemical=True),
        sc.Diamine(name='(S)-4,5,6,7-Tetrahydro-benzothiazole-2,6-diamine', CAS='106092-09-5', molecularWeight=169.25, solubility=(0,0), price=2.2, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=diamineConcentration, noCoordinationSites= 2, noImineReactionSites=2, newChemical=True), #commented out because non existant in lab stock
        sc.Diamine(name='[2,2\'-Bipyridine]-4,4\'-diamine', CAS='18511-69-8', molecularWeight=186.22, solubility=(0,0), price=99, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=diamineConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=True), #commented out because non existant in lab stock
        sc.Diamine(name='Naphthalene-1,8-diamine', CAS='479-27-6', molecularWeight=158.2, solubility=(0,1), price=10, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= diamineConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=True), 
        sc.Diamine(name='4,4\'-Oxydianiline', CAS='101-80-4', molecularWeight=200.24, solubility=(0,1), price=0.742, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= diamineConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=True),
        sc.Diamine(name='6-Methyl-1,3,5-triazine-2,4-diamine', CAS='542-02-9', molecularWeight=125.13, solubility=(0,0), price=0.1, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= diamineConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=True), #commented out because non existant in lab stock
        sc.Diamine(name='(R)-(+)-1,1\'-Binaphthyl-2,2\'-diamine', CAS='18741-85-0', molecularWeight=284.35, solubility=(1,0), price=132, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=diamineConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=True),
        sc.Monoaldehdye(name='6-Methylpyridine-2-carboxaldehyde', CAS='1122-72-1', molecularWeight=121.14, solubility=(0,1), price=4, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True),
        sc.Monoaldehdye(name='6-Phenylpicolinaldehyde', CAS='157402-44-3', molecularWeight=183.21, solubility=(0,1), price=206, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True),
        sc.Monoaldehdye(name='[2,2\'-Bipyridine]-6-carbaldehyde', CAS='134296-07-4', molecularWeight=184.19, solubility=(0,1), price=258, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True),
        sc.Monoaldehdye(name='2-Quinolinecarboxaldehyde', CAS='5470-96-2', molecularWeight=157.17, solubility=(1,0), price=30.8, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True),
        sc.Monoaldehdye(name='5-Methylpicolinaldehyde', CAS='4985-92-6', molecularWeight=121.14, solubility=(0,1), price=12, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True),
        sc.Monoaldehdye(name='8-methoxyquinoline-2-carbaldehyde', CAS='103854-64-4', molecularWeight=187.19, solubility=(0,1), price=116, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True),
        sc.Monoaldehdye(name='[1,8]Naphthyridine-2-carbaldehyde', CAS='64379-45-9', molecularWeight=158.16, solubility=(1,2), price=258, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True),
        sc.Monoaldehdye(name='4-Formyl-2-methylthiazole', CAS='20949-84-2', molecularWeight=127.16, solubility=(0,1), price=28, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True),
        sc.Monoaldehdye(name='6-Methoxypyridine-2-carbaldehyde', CAS='54221-96-4', molecularWeight=137.14, solubility=(0,1), price=10, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1,newChemical=True),
        sc.Monoaldehdye(name='1-Methyl-2-imidazolecarboxaldehyde', CAS='13750-81-7', molecularWeight=110.11, solubility=(0,1), price=16, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True),
        sc.Monoaldehdye(name='1-Methyl-1H-benzimidazole-2-carbaldehyde', CAS='3012-80-4', molecularWeight=160.177, solubility=(0,1), price=54, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True),
        sc.Monoaldehdye(name='4-Methyl-1,3-thiazole-2-carbaldehyde', CAS='13750-68-0', molecularWeight=127.16, solubility=(0,1), price=51, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=monoaldehdyeConcentration, noCoordinationSites=1, noImineReactionSites=1, newChemical=True)
        ]

#Chemicals to remove are the chemicals that should not be considered when calculating the possible combinations.

chemicalsToRemove = [    
        sc.Diamine(name='(S)-4,5,6,7-Tetrahydro-benzothiazole-2,6-diamine', CAS='106092-09-5', molecularWeight=169.25, solubility=(0,0), price=2.2, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= diamineConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=False),
        sc.Diamine(name='[2,2\'-Bipyridine]-4,4\'-diamine', CAS='18511-69-8', molecularWeight=186.22, solubility=(0,0), price=99, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= dialdehdyeConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=False),
        sc.Diamine(name='6-Methyl-1,3,5-triazine-2,4-diamine', CAS='542-02-9', molecularWeight=125.13, solubility=(0,0), price=0.1, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial= diamineConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=False),
        sc.Dialdehyde(name='1,10-Phenanthroline-2,9-dicarbaldehyde', CAS='57709-62-3', molecularWeight=236.23, solubility=(0,1), price=165, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=dialdehdyeConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=False),
        sc.Dialdehyde(name='Pyridine-2,6-dicarbaldehyde', CAS='5431-44-7', molecularWeight=135.122, solubility=(0,1), price=59, volumeInReactionVial=reactionVialTransferVolume, concentrationInStockVial=dialdehdyeConcentration, noCoordinationSites=2, noImineReactionSites=2, newChemical=False),
    ]

#Safety checks to preform during workflow. These are simple checks to ensure the workflow is appropiatly set up.

safetyChecks = [
    # cm.VisualBoolCheck('Please top up CH2Cl2 vial and added it in the right place and run getBatchSpacesCsvs() again.', 'Has the CH2Cl2 vial been added and topped up? (1=Yes, 0=No): ' ),
    # cm.VisualBoolCheck('Please top up CHCN3 and run getBatchSpacesCsvs() again.', 'Is there enough CHCN3 left in the resevoir? (1=Yes, 0=No): '),
    # cm.VisualBoolCheck('Please empty special waste and run getBatchSpacesCsvs() again.', 'Is the special waste empty enough for one run? (1=Yes, 0=No): '),
    # cm.VisualBoolCheck('Please add reaction vials and make sure they\'re in the right place and run getBatchSpacesCsvs() again.', 'Have all 48 reaction vials been added in the right places? (1=Yes, 0=No): '),
    # cm.VisualBoolCheck('Please add NMR tubes and make sure they\'re in the right place and run getBatchSpacesCsvs() again.', 'Have all NMR tubes been added, and are the two green stickers aligned? (1=Yes, 0=No): '),
    # cm.VisualBoolCheck('Please add MS vials and run getBatchSpacesCsvs() again.', 'Have all the MS vials been added? (1=Yes, 0=No): '),
    # cm.VisualBoolCheck('Please add measured masses into the csv and run getBatchSpacesCsvs() again.', 'Have all the measured masses been added to the stock_space csv? (1=Yes, 0=No): '),
    # cm.VisualBoolCheck('Please add stock vials in the right locations and run getBatchSpacesCsvs() again.', 'Have the stock vials been added in the right locations? (1=Yes, 0=No): '),
    # cm.VisualBoolCheck('Please add splits to the speta and run getBatchSpacesCsvs() again.', 'Have the speta been pierced? (1=Yes, 0=No): '),
    # cm.CsvMassCheck('Please check your input masses are in the appropiate range OR check there are no empty values and run getBatchSpacesCsvs() again.', 1.5, 0.5, generatedCsvPath + 'stockSpace.csv')
]

