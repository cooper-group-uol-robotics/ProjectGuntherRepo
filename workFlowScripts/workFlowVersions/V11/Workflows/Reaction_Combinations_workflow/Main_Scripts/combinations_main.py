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
All datahandleing and processing is handled by the 'script_classes.py'
All safety checks are handled by the 'check_manager.py'
The 'main.py' just manages the instantiation of different classes and calling of methods at the appropiate timings.

""" 

import pickle
import sys
sys.path.append('Python_Modules')
import script_classes as sc
import check_manager as cm
import os


#Updating the USERSELECTION class depending on the use selected parameters in 'workflowParameters.py'.

rawCWD = os.getcwd()
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])
path = strCWD + '/Reaction_Combinations_workflow/Main_Scripts/workflowParameters.py'
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
    reactionSpace.addStandardReaction(reactionIdx=sc.USERSELECTION.standardReactionIdx)                                                                         #Adds a standrad reaction (chosen in workflowParameters). Allows the chemist to quickly identify if a global batch conditions are all ok.
    print(f'The size of the chemical space is {len(reactionSpace.reactionSpace)} reactions')                                                                    #Prints the size of the reaction space.

    #Saving reaction space to a human readable csv.
    
    reactionSpace.saveToCsv()

    #Saving reaction space as a pickle.

    reactionSpace.saveToPickle()


    #Creating the batchSpace.

    batchSpace = sc.BatchSpace(batchSize=sc.USERSELECTION.batchSize)
    batchSpace.importReactionSpace()
    batchSpace.importWholeChemicalSpace()
    batchSpace.saveToPickle()
    print('')
    print('SPACES HAVE BEEN INSTANTIATED')                                                                                                                       #Makes it more clear to the user when the instantiateSpaces function has been called.

def takeNewBatch():
    """Takes a new batch space, and generates masses for a chemist to measure."""

    #Loading the batch pickle.

    path = sc.USERSELECTION.generatedPicklePath + 'batchSpace.pickle'                                                                                            #Reading the batch space for each batch. 
    file = open(path, 'rb')
    batchSpace = pickle.load(file)
    file.close() 

    #Changing the batch number.

    batchSpace.changeBatchNumber()
    
    #Instantiation of spaces in batch space.

    batchSpace.importReactionSpace()
    batchSpace.importWholeChemicalSpace()

    #Getting the sample space.
    batchSpace.getSampleSpace()

    #Generating masses to measure.

    batchSpace.calcStockMasses()
    batchSpace.saveCalcStockMassesToCSv()
    batchSpace.sendStockSpaceToEmail()                                                                                                                           #Sends the stock space to be printed off. Makes it more easy for a chemist to look at masses, measure them out and keep note of them.


    batchSpace.saveToPickle()
    print('')
    print('STOCK SPACE CSV GENERATED')                                                                                                                           #Makes it more clear to the user when the takeNewBatch function has been called


checkManager1 = cm.CheckManager()
checkManager1.addChecks(sc.USERSELECTION.safetyChecks)


def getBatchSpacesCsvs():
    """Saves the sample space and stock spaces as gunther readable csvs."""
    
    flag = checkManager1.runcheckList()                                                                                                                          #Going through the check list to see that everything is ok.

    if flag == True:             

        #loading the batch pickle.

        path = sc.USERSELECTION.generatedPicklePath + 'batchSpace.pickle'                                                                                        #Reading the batch space for each batch. 
        file = open(path, 'rb')
        batchSpace = pickle.load(file)
        file.close() 

        #Instantiation of spaces in batch space.

        batchSpace.importReactionSpace()
        batchSpace.importWholeChemicalSpace()

        #Reading the masses measured and calculating the stock volumes needed.
        
        batchSpace.getMassMeasured()                                         
        batchSpace.getStockSpace()

        #Saving the batch (stock and sample) spaces to csv.

        batchSpace.saveStockSpaceToCsv()                                                                                                                         #CSV for chemspeed to read. Gives information on the volume of solvents to add to make up stock solutions.                                  
        batchSpace.saveSampleSpaceToCsv()                                                                                                                        #CSV for chemspeed to read. Gives information of the transfer volumes to make up specfic reaction (combinations) for a batch.

        #Generating and saving the NMR json.
        
        batchSpace.saveNmrJson()

        #Generating and saving the MS CSV.
        
        batchSpace.saveMsCsv()

        #Sending the generated NMR JSON and MS CSV via email.
        
        batchSpace.sendNmrJasonAndMsCsvToEmail()

        #setting the batch flag to true.
        
        batchSpace.setBatchFlagToTrue()                                                                                                                          #The batch space flag is required to ensure that batch numbers only change when both takeNewBatch() and getBatchSpacesCsvs() have been called.

        #Saving batch spaces as a pickle.

        batchSpace.saveToPickle()
        
        print('')
        print('BATCH SPACE CSVS GENERATED')                                                                                                                     #Makes it more clear to the user when the getBatchSpacesCsvs function has been called


#To run a workflow: run instantiateSpaces() only once. Then in alternation run takeNewBatch() then getBatchSpacesCsvs(). When runnning any function, ensure the other two functions are commented out.

# instantiateSpaces()

# takeNewBatch()
getBatchSpacesCsvs()


#interpreter path C:\Users\emanuele\AppData\Local\miniconda3\envs\mlTools