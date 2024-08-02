"""
Structure of the programme:
- Subdivided into 3 main compnents:
    1) Generation of Reaction space (as pickle file and csv).
    2) Generation of batch reaction space (pickle + csv file).
    3) Generation of stock solution space (pickle + csv file).

The time line (pseudo logic is as follows):
 - Addition of chemicals Gunther is able to explore into a chemical space.
 - Removal of chemicals not used in the combinaiton calculations.
 - Subdivide the space depending on the chemcial subclass (for this project: metal, diamine, monoaldhdye).
 - Generation of the reaction space (calculation of all possible combiantions).
 - Sorting of reaction space based on reagent price and reagents (this is to minise the number of unique reagents a chemist has to measure in a batch).
 - Saving of reacation space (for logging purposes).
 - Taking a batch space (these are combinations / reactions to be taken).
 - Calculating the mass of reagents needed (This depends on the reagents present in the reactoin of the batch space).
 - Generation of stock and sample space chemspeed scripts (The stock space handles the volumes of solvents to make up the stock solutions, the sample space handles the volumes of reagents to transfer to make combinations defined in the batch space).

All parameters are handled in the 'workflowParameters.py'.
All datahandleing and processing is handled by the 'scriptClasses.py'
All safety checks are handled by the 'checkManager.py'
The 'main.py' just manages the instantiation of different classes and calling of methods at the appropiate timings.

""" 

import pickle
import sys
sys.path.append('PythonModules')
import scriptClasses as sc
import checkManager as cm
import os


#Updating the USERSELECTION class depending on the use selected parameters in 'workflowParameters.py'.

rawCWD = os.getcwd()
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])
path = strCWD + '/ReactionCombinationsWorkflow/MainScripts/workflowParameters.py'
sc.USERSELECTION.udpateParameters(path)
print(f'the file location is {sc.USERSELECTION.generatedCsvPath}')

def instantiateSpaces():
    """Generates the first instance of the different spaces."""

    #creating the whole chemical space. 

    wholeSpace = sc.WholeChemicalSpace(sc.USERSELECTION.chemicalsInWholeSpace)

    #saving the whole space to a pickle file. 
    
    wholeSpace.saveToPickle()

    #Taking a subset of the whole chemical space.

    intrestSpace = sc.SubsetChemicalSpace(WholeChemicalSpace=wholeSpace)

    #These chemicals are removed as they are insoluble in both CH3CN and CCl2H2. Or they are not relavent to the chemistry being currently studied (not part of the combinations).
    
    intrestSpace.removeChemicalsFromSpace(sc.USERSELECTION.chemicalsToRemove)
    intrestSpace.divideSpaceBySubtype()

    #Calculating combinations.

    subtypeInReactionTuple = sc.USERSELECTION.subTypeInReactionTuple                                                                                            #Getting the subtype tuple from workflowparameters.
    reactionSpace = sc.ReactionSpace(subsetSpace=intrestSpace, wholeSpace=wholeSpace)                                                                           #Making the reaction space.
    #reactionSpace.showSubtypesIndex()                                                                                                                          #shows user what each index in the SubtypeInReactionTuple coresponds to.
    reactionSpace.calcSubTypeCombinations(noSubtypeInReaction=subtypeInReactionTuple)                                                                           #Calculating the combinations based on the chemical subtype.
    #reactionSpace.calcImineCombinations()                                                                                                                      #Due to the structure of the programme, multiple different combination spaces are allowed in a reaction space. This is also why pricing is order post combination calcualtions. In this case the seconday combination sapce are all the posssible imines.
    reactionSpace.orderChemicalPrices()                                                                                                                         #Ordering the reagents based on price from lowest to highest. This is required for the sorting algorthim in the next step.
    reactionSpace.orderReactionPrices()                                                                                                                         #Orders the reactions based on price and reagents. As mentioned before this is to minise the number of reagents a chemist has to take in a combination.
    reactionSpace.generateReactionSpace()                                                                                                                       #Translates the combinations to reactions (i.e. turns abstract combinations to reaction python classes).                                                                                                                       #
    reactionSpace.duplicateSpace()
    print(f'The size of the chemical space is {len(reactionSpace.reactionSpace)} reactions')                                                                    #Prints the size of the reaction space.

    #Saving reaction space to a human readable csv.
    
    reactionSpace.saveToCsv()

    #Saving reaction space as a pickle.

    reactionSpace.saveToPickle()

    #Creating the SampleSpace.

    sampleSpace = sc.SampleSpace()
    sampleSpace.importReactionSpace()
    sampleSpace.duplicatereactionSpace()
    sampleSpace.addStandardReactionIdx(standardReactionIdx=sc.USERSELECTION.standardReactionIdx)
    sampleSpace.generateSampleSpace(batchSize=sc.USERSELECTION.batchSize)

    #Saving the sampleSpace as pickle.

    sampleSpace.saveToPickle()

    #Creating the BatchSpace.

    batchSpace = sc.BatchSpace(batchSize=sc.USERSELECTION.batchSize)
    batchSpace.importSampleSpace()
    batchSpace.importWholeChemicalSpace()
    batchSpace.saveToPickle()
    print('')
    print('SPACES HAVE BEEN INSTANTIATED')                                                                                                                       #Makes it more clear to the user when the instantiateSpaces function has been called.

def takeNewBatch():
    """Takes a new batch space, and generates masses for a chemist to measure."""

    #Loading the batch pickle.

    pathBatchSpace = sc.USERSELECTION.generatedPicklePath + 'batchSpace.pickle'                                                                                            #Reading the batch space for each batch. 
    fileBatchSpace = open(pathBatchSpace, 'rb')
    batchSpace = pickle.load(fileBatchSpace)
    fileBatchSpace.close()

    #If the previous sample space has not been taken, skip the process of stock generation. 

    if batchSpace.stockSpaceFlag():

        #Resting sample and stock space flags.
        
        batchSpace.setSampleFlagToFalse()
        batchSpace.setStockFlagToTrue()
        
        #Changing the batch number.

        batchSpace.changeBatchNumber()

        #Instantiation of spaces in batch space.

        batchSpace.importSampleSpace()
        batchSpace.importWholeChemicalSpace()

        #Getting the sample space.

        batchSpace.getBatchSpace()

        #Saving the sample space.

        batchSpace.exportSampleSpace()

        #Generating masses to measure.

        batchSpace.calcStockMasses()
        batchSpace.saveCalcStockMassesToCSv()

        # batchSpace.sendStockSpaceToEmail()                                                                                                                           #Sends the stock space to be printed off. Makes it more easy for a chemist to look at masses, measure them out and keep note of them.
        batchSpace.exportSampleSpace()
        batchSpace.saveToPickle()
        print('')
        print('STOCK SPACE CSV GENERATED')                                                                                                                           #Makes it more clear to the user when the takeNewBatch function has been called


checkManager1 = cm.CheckManager()
checkManager1.addChecks(sc.USERSELECTION.safetyChecks)

checkManager2 = cm.CheckManager()
checkManager2.addChecks([cm.VisualBoolCheck('Exiting', 'Are you sure you want to retake the batches, are you sure you are not running this for a second time? (1=Yes, 0=No): ' )])

def getBatchSpacesCsvs():
    """Saves the sample space and stock spaces as gunther readable csvs."""
    
    flag = checkManager1.runcheckList()                                                                                                                          #Going through the check list to see that everything is ok.

    if flag == True:             

        #loading the batch pickle.

        path = sc.USERSELECTION.generatedPicklePath + 'batchSpace.pickle'                                                                                        #Reading the batch space for each batch. 
        file = open(path, 'rb')
        batchSpace = pickle.load(file)
        file.close() 

        #Checking if the previous stock space has been taken.

        if batchSpace.sampleSpaceFlag()==True:

            #Updating stock and sample space flags.
            batchSpace.setSampleFlagToTrue()
            batchSpace.setStockFlagToFalse()    

            #Instantiation of spaces in batch space.

            batchSpace.importSampleSpace()
            batchSpace.importWholeChemicalSpace()

            #Reading the masses measured and calculating the stock volumes needed.
            
            batchSpace.getMassMeasured()                                         
            batchSpace.getStockSpace()

            #Saving the batch (stock and sample) spaces to csv.

            batchSpace.saveStockSpaceToCsv()                                                                                                                         #CSV for chemspeed to read. Gives information on the volume of solvents to add to make up stock solutions.                                  
            batchSpace.saveBatchSpaceToCsv()                                                                                                                        #CSV for chemspeed to read. Gives information of the transfer volumes to make up specfic reaction (combinations) for a batch.

            #Generating and saving the NMR json.
            
            batchSpace.saveNmrJson()

            #Generating and saving the MS CSV.
            
            batchSpace.saveMsCsv()

            #Sending the generated NMR JSON and MS CSV via email.
            
            # batchSpace.sendNmrJasonAndMsCsvToEmail()

            #Saving batch spaces as a pickle.
            batchSpace.exportSampleSpace()
            batchSpace.saveToPickle()
            
            print('')
            print('BATCH SPACE CSVS GENERATED')                                                                                                                     #Makes it more clear to the user when the getBatchSpacesCsvs function has been called

def retakeBatchs(batches:list):
    """A function that allows for failed batches to be retaken based on batch number"""
    
    #Checking that the function has been called once purposfuly
    
    flag = checkManager2.runcheckList()

    if flag == True:
        
        path = sc.USERSELECTION.generatedPicklePath + 'batchSpace.pickle'                                                                                            #Reading the batch space for each batch. 
        file = open(path, 'rb')
        batchSpace = pickle.load(file)
        file.close()

        #Instantiation of spaces in batch space.

        batchSpace.importSampleSpace()
        batchSpace.importWholeChemicalSpace()

        #Adding the batches to retake.
        
        batchSpace.retakeBatches(batches)

        #Saving spaces as a pickle.

        batchSpace.exportSampleSpace()
        batchSpace.saveToPickle()

        print('Failed Batches added back on batches to take.')
        
def retakeReactions(reactionsIDXs:list):
    """A function that allows for failed batches to be retaken based on batch number"""
    
    #Checking that the function has been called once purposfuly
    
    flag = checkManager2.runcheckList()

    if flag:
        
        path = sc.USERSELECTION.generatedPicklePath + 'batchSpace.pickle'                                                                                            #Reading the batch space for each batch. 
        file = open(path, 'rb')
        batchSpace = pickle.load(file)
        file.close()

        #Instantiation of spaces in batch space.

        batchSpace.importSampleSpace()
        batchSpace.importWholeChemicalSpace()

        #Adding the batches to retake.
        
        batchSpace.retakeReactions(reactionsIDXs)

        #Saving spaces as a pickle.

        batchSpace.exportSampleSpace()
        batchSpace.saveToPickle()

        print('Failed Reactions added back on reactions to take.')



#To run a workflow: run instantiateSpaces() only once. Then in alternation run takeNewBatch() then getBatchSpacesCsvs(). When runnning any function, ensure the other two functions are commented out. To retake batches based on their index add the indexes into batchesToRetake variable and run retakeBatchs() in isolation. retakeBatchs() can be run at any point during the workflow.  To retake reactions based on their unique identifiers add the reaction identifiers into reactionToRetake variable and run retakeReactions() in isolation. retakeReactions() can be run at any point during the workflow.  

# instantiateSpaces()

# takeNewBatch()
# getBatchSpacesCsvs()
        
reactionToRetake = [1,2,3,4]
batchesToRetake = []

# retakeReactions(reactionToRetake)
# retakeBatchs(batchesToRetake)


#ifnterpreter path C:\Users\emanuele\AppData\Local\miniconda3\envs\mlTools