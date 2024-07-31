import pandas as pd
import math
import os

#Getting the current working directory.
rawCWD = os.getcwd()
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])

#The solvent used in the reaction.
solvents = ['acetonitrile']

#The precipitants to test out.
precipitants = ['water', 'acetic acid', 'heptane', 'pentane', 'petroluem ether', 'touene', 'cyclohexanol', 'hexane', 'ethyl acetate', 'diethyl ether', 'tetrahydrofuran', 'dichloromethane', 'chloroform', 'methanol', 'acetone', 'DMF', 'DMSO', 'Ethanol', 'propan-2-ol', 'Xylene', 'Cyclopentyl methyl ether']

#The combinations between solvent and precipitant.
solventPrecipitantCombinations = []
for solvent in solvents:
    for precipitant in precipitants:
        solventPrecipitantCombinations.append((solvent, precipitant))

#A dictionary of the information of the reagents in the standard reaction.
reagentInformation = {
    'metal': {
        'Name': 'Iron(II) tetrafluoroborate hexahydrate',
        'ID': 1,
        'molecularWeight': 337.55,
        'stockSolutionConcentration': 60 / 1.5 
    },
    'amine': {
        'Name': '4,4\'-Methylenedianiline',
        'ID': 11,
        'molecularWeight': 198.26,
        'stockSolutionConcentration': 90 / 1.5
    },
    'aldehyde': {
        'Name': '5-Methylpicolinaldehyde',
        'ID': 25,
        'molecularWeight': 121.14,
        'stockSolutionConcentration': 180 / 1.5
    }
}

def calculateRegentMassesRequired(screenNumber: int):
    """Function calculates the stock masses to measure depending on the crystilisation screening test the chemist is doing."""
    
    if screenNumber == 1:
        #The final volume (mL) of reaction sample wanted.
        sampleVolume = 4

        #The buffer volume (mL) for the 20mL vials
        bufferVolume = 1

        #Sample Volume (mL) required for NMR sample
        nmrVolume = 0.6

        #The volume (mL) to account for vapourative loss.
        vapourativeLoss = 2 - bufferVolume - nmrVolume

        #The volumes of starting reagents to transfer to make the standard reaction sample.
        metalVolume = sampleVolume / 3
        aldehydeVolume = sampleVolume / 3
        amineVolume = sampleVolume / 3

        #The final volumes (mL) needed to make up the standard reaction. This is the volume of reagents in the stock solutions.
        reagentInformation['metal']['stockVolume'] = metalVolume + bufferVolume + nmrVolume + vapourativeLoss 
        reagentInformation['aldehyde']['stockVolume'] = aldehydeVolume + bufferVolume + nmrVolume + vapourativeLoss 
        reagentInformation['amine']['stockVolume'] = amineVolume + bufferVolume + nmrVolume + vapourativeLoss
    
    if screenNumber == 2:
        #The volume (mL) of solvent to add in the Vapor Diffusion vial.
        solventDiffusionVialVolume = 1.5
                
        #The volume of precipitant (mL) to add in the Vapor Diffusion vial.
        precipitatnDiffusionVialVolume = 3 

        #The buffer volume (mL) for the 20mL vials
        bufferVolume = 1

        #Sample Volume (mL) required for NMR sample
        nmrVolume = 0.6

        #The volume (mL) to account for vapourative loss.
        vapourativeLoss = 2 - bufferVolume - nmrVolume

        #The volumes of starting reagents to transfer to make the standard reaction sample.
        metalVolume = solventDiffusionVialVolume / 3
        aldehydeVolume = solventDiffusionVialVolume / 3
        amineVolume = solventDiffusionVialVolume / 3

        #The final volumes (mL) needed to make up the standard reaction. This is the volume of reagents in the stock solutions.
        reagentInformation['metal']['stockVolume'] = (metalVolume * len(solventPrecipitantCombinations)) + bufferVolume + nmrVolume + vapourativeLoss 
        reagentInformation['aldehyde']['stockVolume'] = (aldehydeVolume * len(solventPrecipitantCombinations)) + bufferVolume + nmrVolume + vapourativeLoss 
        reagentInformation['amine']['stockVolume'] = (amineVolume * len(solventPrecipitantCombinations)) + bufferVolume + nmrVolume + vapourativeLoss


    #Calculating the reagent masses (grams) to make up the stock solutions.
    #Mass = volume * concentration * molecular weight.
    for reagent in reagentInformation.keys():
        volume = reagentInformation[reagent]['stockVolume'] / 1000
        concentration = reagentInformation[reagent]['stockSolutionConcentration'] /1000
        molecularWeight = reagentInformation[reagent]['molecularWeight']
        mass = volume * concentration * molecularWeight
        reagentInformation[reagent]['massRequired'] = mass
        print(str(reagentInformation[reagent]['Name']) + ' (' + str(reagentInformation[reagent]['ID']) + '): ' + str(mass))

#A dictionary of the reagents with the chemist measured masses.
measuredMasses = {
    'metal': {
        'measuredMass': 0.04500666666666667,
        },
    'amine': {
        'measuredMass': 0.03965199999999999,
        },
    'aldehyde': {
        'measuredMass': 0.048456,
        }
}

def generateChemSpeedCsv():
    """This generates the two csvs required by the chemspeed: a csv with the reagent volumes, a csv with transfer volumes."""

    #Getting the volumes (microLitre) of acetonitrile to make up the stock solutions.
    #Volume = (mass / molecular weight) / concentration.
    for reagent in reagentInformation.keys():
        mass = measuredMasses[reagent]['measuredMass']
        molecularWeight = reagentInformation[reagent]['molecularWeight']
        concentration = reagentInformation[reagent]['stockSolutionConcentration']
        volumeRequired = ((mass/molecularWeight) / (concentration / 1000)) * 1000000
        reagentInformation[reagent]['voumeToMakeUpStockSolutions'] = volumeRequired

    #Creating a csv with the reagent and the volumes required to make up the stock solutions.
    csvDictionary = {
        'Reagent': [],
        'Acetonitrile Volumes (microlitres)': []
    }

    for reagent in reagentInformation.keys():
        reagentName = reagentInformation[reagent]['Name']
        voumeToMakeUpStockSolutions = reagentInformation[reagent]['voumeToMakeUpStockSolutions']
        csvDictionary['Reagent'].append(reagentName)
        csvDictionary['Acetonitrile Volumes (microlitres)'].append(voumeToMakeUpStockSolutions)

    stockVolumesDfPath = strCWD + '/stockVolumes.csv'
    stockVolumesDf = pd.DataFrame(csvDictionary)
    stockVolumesDf.to_csv(stockVolumesDfPath, index=False)

    #Creating a csv with the reagent transfer volumes. This is to transfer reagents from stock solutions to reaction vials
    
    #The volume allows in reaction vials
    reactionVialsVolume = 4000

    #The total volume required for crystal screening.

    #Getting the reagent with the smalest volume
    minimumVolume = 0
    for reagent in reagentInformation.keys():
        if minimumVolume == 0:
            minimumVolume = reagentInformation[reagent]['voumeToMakeUpStockSolutions']
        elif reagentInformation[reagent]['voumeToMakeUpStockSolutions'] < minimumVolume:
            minimumVolume = reagentInformation[reagent]['voumeToMakeUpStockSolutions']

    #Getting the number of reaction vials required to react required volumes of standard reactions.
    totalVolume = minimumVolume * 3 
    numberOfReactionVials = math.ceil(totalVolume / reactionVialsVolume)
    #The csv with the volumes to transfer form the stock solutions to the reaction vials
    transferVolumeCsv = {
        'metal': [],
        'amine': [],
        'aldehdye': []
    }

    transferVolume = minimumVolume / numberOfReactionVials
    aldhdyeTransferAmount = transferVolume
    amineTransferAmount = transferVolume
    metalTransferAmount = transferVolume

    for i in range(0, 18):
        if i < numberOfReactionVials:
            transferVolumeCsv['metal'].append(metalTransferAmount)
            transferVolumeCsv['aldehdye'].append(aldhdyeTransferAmount)
            transferVolumeCsv['amine'].append(amineTransferAmount)
        else:
            transferVolumeCsv['metal'].append(0)
            transferVolumeCsv['aldehdye'].append(0)
            transferVolumeCsv['amine'].append(0)

    #Saving the transfer csv
    transferVolumeCsvPath = strCWD + '/transferVolumes.csv'
    transferVolumeDf = pd.DataFrame(transferVolumeCsv)
    transferVolumeDf.to_csv(transferVolumeCsvPath, index=False)

calculateRegentMassesRequired(screenNumber=1)
generateChemSpeedCsv()
