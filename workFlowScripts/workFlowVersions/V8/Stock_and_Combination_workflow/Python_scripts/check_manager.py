import pandas as pd
import math

class Check():
    """A check class to be used within a Check_manager class"""
    def __init__(self, error_message):
        self.error_message = error_message                                                         #This is the error message to print if check is not ok (False)

    def run_check(self):
        """Runs the check and returns true is check passed else returns false"""
        pass                                                                                       #This is just a placeholder. The function varies based on the different daughter classes.

class Visual_Bool_Check(Check):
    """A bool (0 or 1) check which can only be done by a human"""
    def __init__(self, error_message, input_message):
        super().__init__(error_message)
        self.input_message = input_message                                                         #This is the input message shown in a conventional python input() function
    
    def take_user_input(self):
        """Takes the user's input and checks that its valid"""
        try:
            user_input = int(input(self.input_message))
            if user_input == 1 or user_input == 0:                                                  #validation of the input (its either 0 or 1)
                self.user_input = user_input
            else:
                raise
        except:
            print('Input not recognised, please input either 1 or 0')                               #excpetion is raised if input is not 0, 1
            self.take_user_input()

    def run_check(self):
        """Runs a check and returns True is all Ok and Flase if not"""
        self.take_user_input()                                                                       #Taking the users inputs
        if self.user_input == 1:                                                                     #Simple binary check
            return True
        
        else:
            print(self.error_message)
            return False

class CSV_Mass_Check(Check):
    """A check that compares the ratio between the needed mass and the measured mass falls between a specific bound"""
    def __init__(self, error_message, upper_mass_bound:float, lower_mass_bound:float, csv_path:str):
        super().__init__(error_message)
        self.upper_mass_bound = upper_mass_bound                                                       #This is the max measured mass / actual mass ratio
        self.lower_mass_bound = lower_mass_bound                                                       #This is the min measured mass / actual mass ratio
        self.csv_path = csv_path                                                                       #This is the path to the stock space cvs (this will be taken from the USER_SELECTION class)

    def get_csv(self):
        """Imports a csv as a pandas dataframe and save the actual and needed masses"""
        df = pd.read_csv(self.csv_path)
        self.mass_needed = df['Mass to measure (in grams)'].tolist()
        self.mass_measured = df['Actual mass measured'].tolist()

    def run_check(self):
        """Runs the check and returns True if all ok and False if not"""
        self.get_csv()                                                                                                              #Getting the needed and actual masses
        out_of_range = False                                                                                                        #This is a flag  

        if len(self.mass_measured) != len(self.mass_needed):                                                                        #Checking that actual inputs have been added to the csv
            out_of_range = True

        for numerator, denominator in zip(self.mass_measured, self.mass_needed):                                                    #The numerator is the mass measured, the denominator is the mass needed
            
            if math.isnan(numerator) == True:                                                                                       #Checking if values have been added to the csv
                out_of_range = True
            
            if denominator != 0:
                if numerator / denominator >= self.upper_mass_bound or numerator / denominator <= self.lower_mass_bound:            #Checking the ratio is in the defined parameters
                    out_of_range = True
    
        if out_of_range == True:                                                                                                    #Checking flag and returning False if any value is not in the defined ratio range.
            print(self.error_message)
            return False
        else:
            return True

class Check_Manager():
    """Organises check list, and runs through check lists before a batch is run"""
    check_list = []
    
    def add_check(self, check:Check):
        """Add a single check to the Check_Manager"""
        self.check_list.append(check)
    
    def add_checks(self, new_check_list:list):
        """Adds multiple checks (inputted as a list) to the Check Manager"""
        self.check_list += self.check_list + new_check_list
    
    def run_check_list(self):
        """Runs through the checks in the check list. Returns True if all checks are Ok. Returns False if not"""
        
        false_check_present = False                                                             #This is a flag
        for check in self.check_list:                                                           #Iterating through checks if any return false the flag turn True
            if check.run_check() == False:
                false_check_present = True 
        
        if false_check_present == True:                                                          #If any of the checks return False, the function returns False
            return False
        
        else:
            return True