"""This script generates a figure for each reaction which includes: Title, subtitle, chemdraw of reagents in reaction, NMR and MS fail or pass, NMR statring reagents, NMR compound, MS spectra with intensity threshold.
Logical order of script:
1) Get file location for starting materials NMR
2) Get file locations for reaction NMR and LCMS data
3) Run through all reactions and compile their spectra along with the decision maker outcome.
"""

import os
import importlib.util
import sys
import pickle


rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])

#Importing the chemicals used in the combination workflow.
combinationParametersPath = strCWD + '/ReactionCombinationsWorkflow/MainScripts/workflowParameters.py'
spec = importlib.util.spec_from_file_location('combinationParameters', combinationParametersPath)
combinationParameters = importlib.util.module_from_spec(spec)
sys.modules['combinationParameters'] = combinationParameters
spec.loader.exec_module(combinationParameters)

#Importing scriptclasses.
scriptClassesPath = strCWD + '/PythonModules/scriptClasses.py'
spec = importlib.util.spec_from_file_location('scriptClasses', scriptClassesPath)
scriptClasses = importlib.util.module_from_spec(spec)
sys.modules['scriptClasses'] = scriptClasses
spec.loader.exec_module(scriptClasses)

#Importing automatedLatexGeneration.
automatedLatexGenerationPath = strCWD + '/PythonModules/automatedLatexGeneration.py'
spec = importlib.util.spec_from_file_location('automatedLatexGeneration', automatedLatexGenerationPath)
automatedLatexGeneration = importlib.util.module_from_spec(spec)
sys.modules['automatedLatexGeneration'] = automatedLatexGeneration
spec.loader.exec_module(automatedLatexGeneration)
import automatedLatexGeneration as alg


#Importing the reaction space
sampleSpaceLocation = strCWD + '/ReactionCombinationsWorkflow/GeneratedPickles/SampleSpace.pickle'
with open(sampleSpaceLocation, 'rb') as f:
    sampleSpace = pickle.load(f)


# A dictionary to store the starting material reagents, and their NMR spectra locations. 
# Dictionary is in the form:
# reagent {'nmrSpectraPng', 'nmrSpectraSvg', 'structurePng', 'structureSvg'}
reagentFigurePaths = {}

chemicalsInWholeSpace = combinationParameters.chemicalsInWholeSpace
chemicalsToRemove = combinationParameters.chemicalsToRemove

chemicalsToIterate = [reagent for reagent in chemicalsInWholeSpace if reagent not in chemicalsToRemove]

reagentSpectraPath = strCWD + '/Data/StartingMaterials/ArchiveData'
reagentStructurePath = strCWD + '/DataAnalysisWorkflow/FigureGeneration/chemicalDrawings'

#Iterating through reagents.
for reagent in chemicalsToIterate:
    #For each reagent we want its NMR spectra and structure image.
    
    #Getting the nmr spectra file locations.
    nmrSpectraName = 'reagentAnalysis-'

    if reagent.ID < 10:
        reagentId = '0' + str(reagent.ID)
    else:
        reagentId = str(reagent.ID)
    
    nmrSpectraName = nmrSpectraName + reagentId

    nmrSpectraPng = reagentSpectraPath + '/' + nmrSpectraName + '.png'
    nmrSpectraSvg = reagentSpectraPath + '/' + nmrSpectraName + '.svg'
    structurePng = reagentStructurePath + '/' + reagent.name + '.png'
    structureSvg = reagentStructurePath + '/' + reagent.name + '.svg'
    
    #A dictionary with all the paths for a reagent.
    pathDictionary = {}

    #Checking that the paths exist before adding them to the dictionary.
    if os.path.exists(nmrSpectraPng):
        pathDictionary['nmrSpectraPng'] = nmrSpectraPng
    
    if os.path.exists(nmrSpectraSvg):
        pathDictionary['nmrSpectraSvg'] = nmrSpectraSvg
    
    if os.path.exists(structurePng):
        pathDictionary['structurePng'] = structurePng

    if os.path.exists(structureSvg):
        pathDictionary['structureSvg'] = structureSvg

    reagentFigurePaths[reagent.name] = pathDictionary

#Getting the nmr, mass spec paths for each reaction.

def getParsedBatchFile(ArchiveFolder):
    """Returns the name of a file based on the reaction ID."""
    
    #getting a list of files in a directory
    images = os.listdir(ArchiveFolder)

    #seperating images into ms and Nmr images
    nmrFiles = {}
    msFiles = {}

    for imageFile in images:
        #Checking if the file is of an NMR spectra
        if '-' in imageFile:
            #Checking if the file does not belong to the strandard reaction NMR.
            if '01' in imageFile:
                if '.svg' in imageFile:
                    nmrFiles['standardReactionSvg'] = imageFile
                elif '.png' in imageFile:
                    nmrFiles['standardReactionPng'] = imageFile
            
            else:
                #Getting the reaction number of a specfic nmr spectra
                batchStr, nmrSampleStr = imageFile.split('-')
                batchNumber = batchStr[5:]
                nmrSampleNumber = nmrSampleStr[:-4]
                batchSize = combinationParameters.batchSize
                reactionNumber = (int(batchNumber))*(batchSize-1) + (int(nmrSampleNumber)-1)
                
                #Checking if the image is in a Svg or Png format.
                if '.svg' in imageFile:
                    nmrKey = str(reactionNumber) + 'Svg'
                    nmrFiles[nmrKey] = imageFile
                elif '.png' in imageFile:
                    nmrKey = str(reactionNumber) + 'Png'
                    nmrFiles[nmrKey] = imageFile
        
        #The file is of a Ms spectra.
        else:
            reactionNumber = imageFile[:-4]
            #Checking if the spectra belongs to the standard reaction.
            if 'batch' in imageFile:
                if '.svg' in imageFile:
                    msFiles['standardReactionSvg'] = imageFile
                else:
                    msFiles['standardReactionPng'] = imageFile

            else:    
                if '.svg' in imageFile:
                    msKey = reactionNumber + 'Svg'
                    msFiles[msKey] = imageFile
                else:
                    msKey = reactionNumber + 'Png'
                    msFiles[msKey] = imageFile
    
    return nmrFiles, msFiles
    




























# from pylatex import NoEscape

# geometryOptions = {
#     "margin": "2.54cm",
# }

# doc = alg.ReactionDataDocument(geometry_options=geometryOptions)

# doc = alg.generateReactionScheme(document = doc,
#                                  aldehdyeFigure = None,
#                                  amineFigure = None,
#                                  metalFigure = None,
#                                  reactionID = 60,
#                                  reactionLable = 0,
#                                  aldehydeID = 7, 
#                                  amineID = 14, 
#                                  metal = 'Yittrium (III)',
#                                 aldehydeRatio = 2, 
#                                 amineRatio = 1,
#                                 metalRatio = 1)

# # doc = alg.generateDecisionTableForDmLabeling(document = doc,
# #                                 reactionId = 30,
# #                                 reactionDecision=1,
# #                                 nmrDecision=1,
# #                                 nmrCriteria1Bool=1,
# #                                 nmrCriteria1Details=4,
# #                                 nmrCriteria2Bool=1,
# #                                 nmrCriteria2Details=4,
# #                                 msDecision=1,
# #                                 msCriteria1Bool=1,
# #                                 msCriteria1Details=70,
# #                                 msCriteria2Bool=1,
# #                                 msCriteria2Details=80,
# #                                 msCriteria3Bool=0,
# #                                 msCriteria3Details=4)

# doc = alg.generateNmrFigure(document = doc, 
#                             reactionID = 24, 
#                             aldehdyeNmr = None, 
#                             amineNmr = None, 
#                             reactionNmr = None)

# doc = alg.generateMsFigure(document = doc,
#                            reactionID = 24,
#                            reactionMs = None)

# doc = alg.generateDecisionTableForMasterThesis(document = doc,
#                                                reactionId = 342,
#                                                humanNmrClass = 1,
#                                                humanMsClass = 2,
#                                                decisionMakerMsBool = 1,
#                                                msCriteria1And2Bool = 1,
#                                                msCriteria3Bool = 1,
#                                                msCriteria1and2Decisions = 1,
#                                                msCriteria3Decisions = 1
#                                                )



# # pdfPath = strCWD + '/DataAnalysisWorkflow/FigureGeneration/test'
# # doc.generate_pdf(pdfPath, clean_tex=False)




























# labelPath = 'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/backup/ChemspeedPlatformAllVersions/V12/Workflows/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/lables.pickle'
# with open(labelPath, 'rb') as f:
#         labelsDictionary = pickle.load(f)

# print(labelsDictionary['188'])








#Importing human MS and NMR labels.
humanLabelsPath = 'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/backup/ChemspeedPlatformAllVersions/V12/Workflows/DataAnalysisWorkflow/DataSetGeneration/pickleFiles/humanLabeling/humanLable.pickle'
with open(humanLabelsPath, 'rb') as f:
    humanLabels = pickle.load(f)

def retrieveReactionObject(reactionNumber):
    """Returns a reaction object based on the reaction number"""

    #Getting the sample space.
    sampleSpacePath = strCWD + '/ReactionCombinationsWorkflow/GeneratedPickles/SampleSpace.pickle'
    with open(sampleSpacePath, 'rb') as f:
        sampleSpace = pickle.load(f)

    reactionList = sampleSpace.ReactionSpace.reactionSpace

    if 'batch' in reactionNumber:
        reactionNumber = combinationParameters.standardReactionIdx + 1

    for reaction in reactionList:
        if str(reaction.unique_identifier) == str(reactionNumber):
            return reaction
        
def retrieveReagentObject(reactionObject, reagentClass):
    """Gets path to reagent (Diamine, Monoaldehdye, Metal) figure"""

    for reagent in reactionObject.reagents:
        if reagent.__class__.__name__ == reagentClass:
            return reagent

def retrieveReagentFigure(reagentObject):
    """Returns the path to the reagent chemical structure."""
    chemicalDrawingsPath = strCWD + '/DataAnalysisWorkflow/FigureGeneration/chemicalDrawings'
    reagentFigurePath = chemicalDrawingsPath + '/' + reagentObject.name + '.png'

    if os.path.exists(reagentFigurePath):
        return reagentFigurePath
    else:
        print(reagentFigurePath)
    
def retrievePaperReagentId(reagentObject):
    """Returns the reagent ID used in the paper"""
    
    shortenMetalName = {
        'Iron(II) tetrafluoroborate hexahydrate': 'Iron(II)', 
        'Zinc tetrafluoroborate': 'Zinc(II)',
        'Yittrium(III) trifluoromethanesulfonate': 'Yittrium(III)',
        'Tetrakis(acetonitrile)copper(I) tetrafluoroborate': 'Copper(I)',
        'Silver tetrafluoroborate': 'Silver(I)'
        }
    
    #A hash table that maps the reagents index to their numbers used in the paper.
    reagentFigureIndex = {
        1: None,
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
        32: 10
        }
    if int(reagentObject.ID) in reagentFigureIndex.keys():
        if reagentFigureIndex[reagentObject.ID] == None and reagentObject.name in shortenMetalName.keys():
            return shortenMetalName[reagentObject.name]
        return reagentFigureIndex[reagentObject.ID]

def retrieveReagentRatio(reactionObject, reagentClass):
    """Returns the equivilance of the reagent (Diamine, Monoaldehdye, Metal) assumed to take in the reaction."""

    ratioData = {
        'Metal': combinationParameters.metalConcentration  / combinationParameters.metalConcentration, 
        'Diamine': combinationParameters.diamineConcentration / combinationParameters.metalConcentration, 
        'Monoaldehdye': combinationParameters.monoaldehdyeConcentration / combinationParameters.metalConcentration,
    }

    return ratioData[reagentClass]

def retrieveReactionNMR(batch, reactionId):
    """Returns the path to the reaction NMR"""
    nmrFigurePath = strCWD + '/Data/Reactions/' + batch + '/ArchiveData/NMR' + reactionId + '.png'
    if os.path.exists(nmrFigurePath):
        return nmrFigurePath
    else:
        print(nmrFigurePath)
        
def retrieveReactionMS(batch, reactionId):
    """Returns the path to the reaction NMR"""
    nmrFigurePath = strCWD + '/Data/Reactions/' + batch + '/ArchiveData/MS' + reactionId + '.png'
    if os.path.exists(nmrFigurePath):
        return nmrFigurePath
    else:
        print(nmrFigurePath)

def retrieveReagentNMR(reactionObject):
    """Retruns the reagent NMR path"""
    reagentNmrFolderPath = strCWD + '/Data/StartingMaterials/ArchiveData/NMRreagentAnalysis-'
    reagentId = reactionObject.ID
    if reagentId > 9:
        reagentNmrPath = reagentNmrFolderPath + str(reagentId) + '.png'
    else:
        reagentNmrPath = reagentNmrFolderPath + '0' + str(reagentId) + '.png'
    
    if os.path.exists(reagentNmrPath):
        return reagentNmrPath
    else:
        print(reagentNmrPath)

def generateFullDocument():
    """Generates the complete SI document"""

    from pylatex import NoEscape

    geometryOptions = {
        "margin": "2.54cm",
    }

    doc = alg.ReactionDataDocument(geometry_options=geometryOptions)
    doc.append(NoEscape(r'\tableofcontents'))

    #Populating datadictoinary with appropiate information

    print(humanLabels['batch0'][2].keys())
    for batch, batchData in humanLabels.items():
        if batch != 'lackingMsSamples':
            for sample, sampleData in batchData.items():
                if 'batch' not in sampleData['reactionId']:
                    #Information we need to build an automated figure.
                    reactionId = sampleData['reactionId']
                    humanNmrClass = int(sampleData['humanNmrLabel']),           #The classification of the NMR spectra
                    humanNmrClass = humanNmrClass[0]
                    humanMsClass = int(sampleData['humanMsLabel']),            #The classification of the MS spectra    
                    humanMsClass = humanMsClass[0]
                    decisionMakerMsBool = int(sampleData['MsDecision']['label']),     #The outcome of MS decision maker.
                    decisionMakerMsBool = decisionMakerMsBool[0]
                    
                    msCriteria1And2Bool = int(sampleData['MsDecision']['criteria1and2_pass']),         #The outcome of decision maker criteria 1 and 2.
                    msCriteria1And2Bool = msCriteria1And2Bool[0]
                    msCriteria3Bool = int(sampleData['MsDecision']['criteria3_pass']),         #The outcome of decision maker criteria 3.
                    msCriteria3Bool = msCriteria3Bool[0]
                    
                    msCriteria1And2Decisions = int(sampleData['MsDecision']['criteria1and2_number_of_hits']),    #Information of criteria 1 and 2.

                    msCriteria1And2Decisions = msCriteria1And2Decisions[0]
                    msCriteria3Decisions = int(sampleData['MsDecision']['criteria3_number_of_ions_hits'])     #Information of criteria 3.
                    

                    if str(humanNmrClass) == '1' and str(humanMsClass) == '2':
                        reactionLable = 1           #The outcome of the reaction
                    else:
                        reactionLable = 0

                    reactionObject = retrieveReactionObject(reactionId)
                    amineObject = retrieveReagentObject(reactionObject=reactionObject, reagentClass='Diamine')
                    aldehdyeObject = retrieveReagentObject(reactionObject=reactionObject, reagentClass='Monoaldehdye')
                    metalObject = retrieveReagentObject(reactionObject=reactionObject, reagentClass='Metal')

                    aldehdyeFigure = retrieveReagentFigure(aldehdyeObject),          #Path to aldhdye chemdraw svg
                    aldehdyeFigure = aldehdyeFigure[0]
                    
                    amineFigure = retrieveReagentFigure(amineObject),             #Path to amine chemdraw svg
                    amineFigure = amineFigure[0]

                    metalFigure = retrieveReagentFigure(metalObject),             #Path to metal chemdraw svg
                    metalFigure = metalFigure[0]

                    aldehydeID = retrievePaperReagentId(aldehdyeObject),              #The reagent Id of the aldehdye (id used for paper)
                    aldehydeID = aldehydeID[0]

                    amineID = retrievePaperReagentId(amineObject),                 #The reagent Id of the amine (id use for paper)
                    amineID = amineID[0]

                    metalID = retrievePaperReagentId(metalObject),                   #The name of the metal used 
                    metalID = metalID[0]

                    aldehydeRatio = retrieveReagentRatio(reactionObject, 'Monoaldehdye'),           #The equivilance of the aldhdye in the reaction
                    aldehydeRatio = aldehydeRatio[0]

                    amineRatio = retrieveReagentRatio(reactionObject, 'Diamine'),              #The equivilance of the amine in the reaction
                    amineRatio = amineRatio[0]

                    metalRatio = retrieveReagentRatio(reactionObject, 'Metal')               #The equivilance of the metal in the reaction (this is what changes)

                    aldehdyeNmr = retrieveReagentNMR(aldehdyeObject),             #The path to the aldehdye NMR figure
                    aldehdyeNmr = aldehdyeNmr[0]

                    amineNmr = retrieveReagentNMR(amineObject),                #The path to the amine NMR figure
                    amineNmr = amineNmr[0]

                    reactionNmr = retrieveReactionNMR(batch, reactionId)              #The path to the reaction  NMR figure

                    reactionMs = retrieveReactionMS(batch, reactionId)               #The path to the MS figure

                    latexSectionCode1 = r'\section*' + '{' + 'Reaction ' + reactionId + '}'
                    latexSectionCode2 = r'\addcontentsline{toc}{section}{\protect\numberline{}' + 'Reaction ' + reactionId + '}'
                    doc.append(NoEscape(latexSectionCode1))
                    doc.append(NoEscape(latexSectionCode2))

                    doc = alg.generateReactionScheme(
                        document = doc,
                        aldehdyeFigure = aldehdyeFigure,
                        amineFigure = amineFigure,
                        metalFigure = metalFigure,
                        reactionID = reactionId,
                        reactionLable = reactionLable,
                        aldehydeID = aldehydeID, 
                        amineID = amineID,
                        metal = metalID,
                        aldehydeRatio = aldehydeRatio, 
                        amineRatio = amineRatio,
                        metalRatio = metalRatio)
                    
                    doc = alg.generateDecisionTableForMasterThesis(
                        document = doc,
                        reactionId = reactionId,
                        humanNmrClass = humanNmrClass,
                        humanMsClass = humanMsClass,
                        decisionMakerMsBool = decisionMakerMsBool,
                        msCriteria1And2Bool = msCriteria1And2Bool,
                        msCriteria3Bool = msCriteria3Bool,
                        msCriteria1and2Decisions = msCriteria1And2Decisions,
                        msCriteria3Decisions = msCriteria3Decisions
                        )
                    
                    doc = alg.generateNmrFigure(
                        document = doc, 
                        reactionID = reactionId, 
                        aldehdyeNmr = aldehdyeNmr, 
                        amineNmr = amineNmr, 
                        reactionNmr = reactionNmr)
                    
                    doc = alg.generateMsFigure(
                        document = doc,
                        reactionID = reactionId,
                        reactionMs = reactionMs)

    pdfPath = strCWD + '/DataAnalysisWorkflow/FigureGeneration/test'
    doc.generate_pdf(pdfPath, clean_tex=False)

def generatePartialDocument(maxIteration):
    """Generates a small document for tests."""
    from pylatex import NoEscape

    geometryOptions = {
        "margin": "2.54cm",
    }

    doc = alg.ReactionDataDocument(geometry_options=geometryOptions)
    doc.append(NoEscape(r'\tableofcontents'))

    #Populating datadictoinary with appropiate information
    iterationCount = 0
    print(humanLabels['batch0'][2].keys())
    for batch, batchData in humanLabels.items():
        if batch != 'lackingMsSamples':
            for sample, sampleData in batchData.items():
                if iterationCount < maxIteration:
                    iterationCount += 1
                    if 'batch' not in sampleData['reactionId']:
                        print('')
                        print(sampleData['reactionId']) 
                        print(sampleData['MsDecision'])
                        #Information we need to build an automated figure.
                        reactionId = sampleData['reactionId']
                        humanNmrClass = int(sampleData['humanNmrLabel']),           #The classification of the NMR spectra
                        humanNmrClass = humanNmrClass[0]
                        humanMsClass = int(sampleData['humanMsLabel']),            #The classification of the MS spectra    
                        humanMsClass = humanMsClass[0]
                        decisionMakerMsBool = int(sampleData['MsDecision']['label']),     #The outcome of MS decision maker.
                        decisionMakerMsBool = decisionMakerMsBool[0]
                        
                        msCriteria1And2Bool = int(sampleData['MsDecision']['criteria1and2_pass']),         #The outcome of decision maker criteria 1 and 2.
                        msCriteria1And2Bool = msCriteria1And2Bool[0]
                        msCriteria3Bool = int(sampleData['MsDecision']['criteria3_pass']),         #The outcome of decision maker criteria 3.
                        msCriteria3Bool = msCriteria3Bool[0]
                        
                        msCriteria1And2Decisions = int(sampleData['MsDecision']['criteria1and2_number_of_hits']),    #Information of criteria 1 and 2.

                        msCriteria1And2Decisions = msCriteria1And2Decisions[0]
                        msCriteria3Decisions = int(sampleData['MsDecision']['criteria3_number_of_ions_hits'])     #Information of criteria 3.
                        

                        if str(humanNmrClass) == '1' and str(humanMsClass) == '2':
                            reactionLable = 1           #The outcome of the reaction
                        else:
                            reactionLable = 0

                        reactionObject = retrieveReactionObject(reactionId)
                        amineObject = retrieveReagentObject(reactionObject=reactionObject, reagentClass='Diamine')
                        aldehdyeObject = retrieveReagentObject(reactionObject=reactionObject, reagentClass='Monoaldehdye')
                        metalObject = retrieveReagentObject(reactionObject=reactionObject, reagentClass='Metal')

                        aldehdyeFigure = retrieveReagentFigure(aldehdyeObject),          #Path to aldhdye chemdraw svg
                        aldehdyeFigure = aldehdyeFigure[0]
                        
                        amineFigure = retrieveReagentFigure(amineObject),             #Path to amine chemdraw svg
                        amineFigure = amineFigure[0]

                        metalFigure = retrieveReagentFigure(metalObject),             #Path to metal chemdraw svg
                        metalFigure = metalFigure[0]

                        aldehydeID = retrievePaperReagentId(aldehdyeObject),              #The reagent Id of the aldehdye (id used for paper)
                        aldehydeID = aldehydeID[0]

                        amineID = retrievePaperReagentId(amineObject),                 #The reagent Id of the amine (id use for paper)
                        amineID = amineID[0]

                        metalID = retrievePaperReagentId(metalObject),                   #The name of the metal used 
                        metalID = metalID[0]

                        aldehydeRatio = retrieveReagentRatio(reactionObject, 'Monoaldehdye'),           #The equivilance of the aldhdye in the reaction
                        aldehydeRatio = aldehydeRatio[0]

                        amineRatio = retrieveReagentRatio(reactionObject, 'Diamine'),              #The equivilance of the amine in the reaction
                        amineRatio = amineRatio[0]

                        metalRatio = retrieveReagentRatio(reactionObject, 'Metal')               #The equivilance of the metal in the reaction (this is what changes)

                        aldehdyeNmr = retrieveReagentNMR(aldehdyeObject),             #The path to the aldehdye NMR figure
                        aldehdyeNmr = aldehdyeNmr[0]

                        amineNmr = retrieveReagentNMR(amineObject),                #The path to the amine NMR figure
                        amineNmr = amineNmr[0]

                        reactionNmr = retrieveReactionNMR(batch, reactionId)              #The path to the reaction  NMR figure

                        reactionMs = retrieveReactionMS(batch, reactionId)               #The path to the MS figure

                        latexSectionCode1 = r'\section*' + '{' + 'Reaction ' + reactionId + '}'
                        latexSectionCode2 = r'\addcontentsline{toc}{section}{\protect\numberline{}' + 'Reaction ' + reactionId + '}'
                        doc.append(NoEscape(latexSectionCode1))
                        doc.append(NoEscape(latexSectionCode2))

                        doc = alg.generateReactionScheme(
                            document = doc,
                            aldehdyeFigure = aldehdyeFigure,
                            amineFigure = amineFigure,
                            metalFigure = metalFigure,
                            reactionID = reactionId,
                            reactionLable = reactionLable,
                            aldehydeID = aldehydeID, 
                            amineID = amineID,
                            metal = metalID,
                            aldehydeRatio = aldehydeRatio, 
                            amineRatio = amineRatio,
                            metalRatio = metalRatio)
                        
                        doc = alg.generateDecisionTableForMasterThesis(
                            document = doc,
                            reactionId = reactionId,
                            humanNmrClass = humanNmrClass,
                            humanMsClass = humanMsClass,
                            decisionMakerMsBool = decisionMakerMsBool,
                            msCriteria1And2Bool = msCriteria1And2Bool,
                            msCriteria3Bool = msCriteria3Bool,
                            msCriteria1and2Decisions = msCriteria1And2Decisions,
                            msCriteria3Decisions = msCriteria3Decisions
                            )
                        
                        doc = alg.generateNmrFigure(
                            document = doc, 
                            reactionID = reactionId, 
                            aldehdyeNmr = aldehdyeNmr, 
                            amineNmr = amineNmr, 
                            reactionNmr = reactionNmr)
                        
                        doc = alg.generateMsFigure(
                            document = doc,
                            reactionID = reactionId,
                            reactionMs = reactionMs)

    pdfPath = strCWD + '/DataAnalysisWorkflow/FigureGeneration/test'
    doc.generate_pdf(pdfPath, clean_tex=False)

# generatePartialDocument(10)
generateFullDocument()