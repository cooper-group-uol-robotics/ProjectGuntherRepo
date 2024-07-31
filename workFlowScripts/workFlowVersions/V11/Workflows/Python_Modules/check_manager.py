"""
The goal of this module is to add a safety net to the workflow. Both the python script and the chemspeed platforms are quite stupid. 'Inteligence' has to be programmaticly added to avoid stupid mistakes. Stupid mistake include: transfering 40mL of solvent in a 20mL vial. Simple human errors (be it forgetfullnesss or basic human mistakes).

To do so the module is strucutred as follows:
- A Checkmanager class. This is repsonsible for the addition of checks, running checks and prevting the workflow to proceed if the checks are fialed.
- Check class: this is a parent class for all different types of checks.
- Check daugher class: these are more specific classes of checkes. The two daughter classes used in this project are: a VisualBoolCheck (as simple reminder to the chemist), and CsvMassCheck (ensures measured reagent masses are not to far from requried masses -> ensure reagents are not quickly burnt through).

"""

import pandas as pd
import math

class Check():
    """A check class to be used within a CheckManager class."""
   
    def __init__(self, errorMessage):
        self.errorMessage = errorMessage                                                                                            #This is the error message to print if check is not ok (False)

    def runCheck(self):
        """Runs the check and returns true is check passed else returns false"""
        
        pass                                                                                                                        #This is just a placeholder. The function varies based on the different daughter classes.

class VisualBoolCheck(Check):
    """A bool (0 or 1) check which can only be done by a human. This is more of a reminder."""
    
    def __init__(self, errorMessage, inputMessage):
        super().__init__(errorMessage)
        self.inputMessage = inputMessage                                                                                            #This is the input message shown in a conventional python input() function. 
    
    def takeUserInput(self):
        """Takes the user's input and checks that its valid (either a 1 or 0)."""
        
        validInput = False                                                                                                          #A flag is used, so that the input is taken untill a valid user input (either 1 or 0) has been added.
        while validInput is not True:
            userInput = input(self.inputMessage)
            if userInput == '1' or userInput == '0':                                                                                #Validation of the input (its either 0 or 1)
                self.userInput = int(userInput)
                validInput = True
            else:
                print('Input not recognised, please input either 1 or 0')
                
    def runCheck(self):
        """Runs a check and returns True if all Ok and Flase if not"""
        
        self.takeUserInput()                                                                                                        #Taking the users inputs
        if self.userInput == 1:                                                                                                     #Simple binary check.
            return True
        
        else:
            print(self.errorMessage)
            return False

class CsvMassCheck(Check):
    """A check that compares the ratio between the needed mass and the measured mass falls between a specific bound"""
    def __init__(self, errorMessage, upperMassBound:float, lowerMassBound:float, csvPath:str):
        super().__init__(errorMessage)
        self.upperMassBound = upperMassBound                                                                                        #This is the max measured mass / actual mass ratio.
        self.lowerMassBound = lowerMassBound                                                                                        #This is the min measured mass / actual mass ratio.
        self.csvPath = csvPath                                                                                                      #This is the path to the stock space cvs (in the main script, this will be taken from the USERSELECTION class).

    def getCsv(self):
        """Imports a csv as a pandas dataframe and saves the measured and needed masses."""
        
        df = pd.read_csv(self.csvPath)
        self.massNeeded = df['Mass to measure (in grams)'].tolist()
        self.massMeasured = df['Actual mass measured'].tolist()

    def runCheck(self):
        """Runs the check and returns True if all ok and False if not"""
        
        self.getCsv()                                                                                                               #Getting the needed and measured masses.
        outOfRange = False                                                                                                          #This is a flag, which can be changed based on different (not necessarly related) events. This determines if a value is considered in or out of range.

        if len(self.massMeasured) != len(self.massNeeded):                                                                          #Checking that actual inputs have been added to the csv.
            outOfRange = True

        for numerator, denominator in zip(self.massMeasured, self.massNeeded):                                                      #The numerator is the mass measured, the denominator is the mass needed
            
            if math.isnan(numerator) == True:                                                                                       #Checking if values have been added to the csv. This is an internal check to see if a chemist has inputted masses.
                outOfRange = True
            
            if denominator != 0:                                                                                                    #Fiilters through mathematical errors (division by zero).
                if numerator / denominator >= self.upperMassBound or numerator / denominator <= self.lowerMassBound:                #Checking the numerator:denominator ratio is in the right range (see self.upperMassBound, and self.lowerMassBound).
                    outOfRange = True
    
        if outOfRange == True:                                                                                                      #Checking flag and returning False if any value is not in the defined ratio range.
            print(self.errorMessage)
            return False
        else:
            return True

class CheckManager():
    """Organises check list, and runs through check lists before a batch is run."""
    
    checkList = []
    
    def addCheck(self, check:Check):
        """Add a single check to the CheckManager"""
        
        self.checkList.append(check)
    
    def addChecks(self, new_checkList:list):
        """Adds multiple checks (inputted as a list) to the Check Manager"""
        self.checkList += self.checkList + new_checkList
    
    def runcheckList(self):
        """Runs through the checks in the check list. Returns True if all checks are Ok. Returns False if not"""
        
        falseCheckPresent = False                                                                                                   #This is a flag which determins if all checks are good or not.
        for check in self.checkList:                                                                                                #Iterating through checks, if any return false, the flag turns True.
            if check.runCheck() == False:
                falseCheckPresent = True 
        
        if falseCheckPresent == True:                                                                                               #If any of the checks return False, the function returns False.
            return False
        
        else:
            return True