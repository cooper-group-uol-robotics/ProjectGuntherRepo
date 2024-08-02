
from pylatex import Document, Tabular, NoEscape, MultiColumn
from pylatex.base_classes.containers import Container
import os

rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])


class ReactionDataDocument(Document):
    """A document with the appropiate formating to be used in Emanuele's master's thesis"""
    def __init__(self, default_filepath="default_filepath", *, documentclass="article", document_options=None, fontenc="T1", inputenc="utf8", font_size="normalsize", lmodern=True, textcomp=True, microtype=None, page_numbers=True, indent=None, geometry_options=None, data=None):
        super().__init__(default_filepath, documentclass=documentclass, document_options=document_options, fontenc=fontenc, inputenc=inputenc, font_size=font_size, lmodern=lmodern, textcomp=textcomp, microtype=microtype, page_numbers=page_numbers, indent=indent, geometry_options=geometry_options, data=data)


        #Importing relevant libraries.
        self.preamble.append(NoEscape(r'\usepackage{graphicx}'))
        self.preamble.append(NoEscape(r'\usepackage{caption}'))
        self.preamble.append(NoEscape(r'\usepackage{newfloat}'))
        self.preamble.append(NoEscape(r'\usepackage{caption}'))
        self.preamble.append(NoEscape(r'\usepackage{float}'))
        self.preamble.append(NoEscape(r'\usepackage{etoolbox}'))

        #Justifying lables to the left
        self.preamble.append(NoEscape(r'\captionsetup{justification=raggedright,singlelinecheck=false}'))

        #Making text in a table small
        self.preamble.append(NoEscape(r'\AtBeginEnvironment{tabular}{\tiny}'))

        #Adding a 'scheme' label
        self.preamble.append(NoEscape(r'\DeclareFloatingEnvironment[fileext=lop]{scheme}'))

        #Adding a 'Decision Table' label
        self.preamble.append(NoEscape(r'\DeclareFloatingEnvironment[fileext=lop]{Decision Table}'))

        #Adding a 'NMR spectra' label
        self.preamble.append(NoEscape(r'\DeclareFloatingEnvironment[fileext=lop]{NMR Spectra}'))

        #Adding a 'MS spectra' label
        self.preamble.append(NoEscape(r'\DeclareFloatingEnvironment[fileext=lop]{MS Spectra}'))



def generateDecisionTableForDmLabeling(document: ReactionDataDocument, reactionId: str, reactionDecision: int, nmrDecision: int, nmrCriteria1Bool: int, nmrCriteria1Details: int, nmrCriteria2Bool, nmrCriteria2Details: int, msDecision: int, msCriteria1Bool: int, msCriteria1Details: int, msCriteria2Bool: int, msCriteria2Details: int, msCriteria3Bool: int, msCriteria3Details: int):
    """Generates a Latex table with decision maker decisions at a reaction, spectra, and criteria level. Returns a document class with the new Latex table and its lable."""
    
    #Classifing decisions as pass or failed bassed on their binary value

    #Reaction Decision
    if str(reactionDecision) == '0':
        reactionDecision = 'Failed'
    else:
        reactionDecision = 'Pass'
    
    #NMR Decision
    if str(nmrDecision) == '0':
        nmrDecision = 'Failed'
    else:
        nmrDecision = 'Pass'
    
    #NMR criteria 1 decision.
    if str(nmrCriteria1Bool) == '0':
        nmrCriteria1Bool = 'Failed'
    else:
        nmrCriteria1Bool = 'Pass'

    #NMR criteria 2 decision.
    if str(nmrCriteria2Bool) == '0':
        nmrCriteria2Bool = 'Failed'
    else:
        nmrCriteria2Bool = 'Pass'

    #MS decision.
    if str(msDecision) == '0':
        msDecision = 'Failed'
    else:
        msDecision = 'Pass'

    #MS criteria 1 decision.
    if str(msCriteria1Bool) == '0':
        msCriteria1Bool = 'Failed'
    else:
        msCriteria1Bool = 'Pass'

    #MS criteria 2 decision.
    if str(msCriteria2Bool) == '0':
        msCriteria2Bool = 'Failed'
    else:
        msCriteria2Bool = 'Pass'

    #MS critieria 3 decision
    if str(msCriteria3Bool) == '0':
        msCriteria3Bool = 'Failed'
    else:
        msCriteria3Bool = 'Pass'
        
    #Making the decision maker output table.
    decisionTable = Tabular('|c|c|c|c|')
    decisionTable.add_hline()


    decisionTable.add_row('', '', 'Criteria 1', 'Difference between the number of')
    decisionTable.add_row('', 'NMR Decision:', nmrCriteria1Bool, f'peaks in reaction and reagent NMRs: {nmrCriteria1Details}')
    decisionTable.add_hline(3)
    decisionTable.add_row('', nmrDecision, 'Criteria 2', 'Percentage of shifted peaks in reaction NMR:')
    decisionTable.add_row('', '', nmrCriteria2Bool, nmrCriteria2Details)
    decisionTable.add_hline(2)

    #Adding the ms decision.
    decisionTable.add_row('Reaction Decision:', '', 'Criteria 1', 'Number of predicted peaks found in MS spectra:')
    decisionTable.add_row(reactionDecision, '', msCriteria1Bool, msCriteria1Details)
    decisionTable.add_hline(3)
    decisionTable.add_row('', 'MS Decision:', 'Criteria 2', 'Number of hits with appropriate intensity:')
    decisionTable.add_row('', msDecision, msCriteria2Bool, msCriteria2Details)
    decisionTable.add_hline(3)
    decisionTable.add_row('', '', 'Criteria 3', 'Number of counter-ions found:')
    decisionTable.add_row('', '', msCriteria3Bool, msCriteria3Details)
    decisionTable.add_hline()

    #Adding the Decision table to the document along with its label.
    Label = '\\' + 'caption' + '{''Decision maker outcomes for the \\textsuperscript' + '{' + '1' +'}' 'H NMR spectroscopy and ULPC-MS spectrometry of reaction ' + str(reactionId) + '.' + ' Decision motivations are also given, based on NMR and MS criteria.' + '}'
    document.append(NoEscape(r'\begin{Decision Table}[H]'))
    document.append(decisionTable)
    document.append(NoEscape(Label))
    document.append(NoEscape(r'\end{Decision Table}'))

    return document

def generateDecisionTableForMasterThesis(document:ReactionDataDocument, reactionId:str, humanNmrClass: int, humanMsClass: int, decisionMakerMsBool: int, msCriteria1And2Bool: int, msCriteria3Bool: int, msCriteria1and2Decisions: int, msCriteria3Decisions: int):
    """Generates a table of MS and NMR outcome depending on human lables."""
    
    #Converting Numerical values to text.

    if str(decisionMakerMsBool) == '0':
        decisionMakerMsBool = 'Failed'
    elif str(decisionMakerMsBool) == '1':
        decisionMakerMsBool = 'Pass'
    else:
        decisionMakerMsBool = 'ERROR'

    if str(msCriteria1And2Bool) == '0':
        msCriteria1And2Bool = 'Failed'
    elif str(msCriteria1And2Bool) == '1':
        msCriteria1And2Bool = 'Pass'
    else:
        msCriteria1And2Bool = 'ERROR'

    if str(msCriteria3Bool) == '0':
        msCriteria3Bool = 'Failed'
    elif str(msCriteria3Bool) == '1':
        msCriteria3Bool = 'Pass'
    else:
        msCriteria3Bool = 'ERROR'
    
    humanMsBool = None #Bool if human pass or fial MS
    if str(humanMsClass) == '0':
        humanMsBool = 'Failed'
    elif str(humanMsClass) == '1':
        humanMsBool = 'Failed'
    elif str(humanMsClass) == '2':
        humanMsBool = 'Pass'
    else:
        humanMsBool = 'Error'
    
    if str(humanMsClass) == '0':
        humanMsClass = 'Reaction failed.'
    elif str(humanMsClass) == '1':
        humanMsClass = 'Reaction occurred, unknown product.'
    elif str(humanMsClass) == '2':
        humanMsClass = 'Reaction occurred, supramolecular product.'
    else:
        humanMsClass = 'Error'

    humanNmrBool = None #Bool if human pass or fial NMR
    if str(humanNmrClass) == '1':
        humanNmrBool = 'Pass'
    elif str(humanNmrClass) == '0':
        humanNmrBool = 'Failed'
    elif str(humanNmrClass) == '2':
        humanNmrBool = 'Failed'
    else:
        humanNmrBool = 'ERROR'
    
    if str(humanNmrClass) == '0':
        humanNmrClass = 'No reaction occured.'
    elif str(humanNmrClass) == '1':
        humanNmrClass = 'Single discrete species formed.'
    elif str(humanNmrClass) == '2':
        humanNmrClass = 'Oligomers formed.'
    elif str(humanNmrClass) == '3':
        humanNmrClass = 'Paramagnetic species formed.'
    else:
        humanNmrClass == 'ERROR'

    humanReactionDecision = None #Bool if both NMR and MS human decision pass
    if str(humanNmrBool) == 'Pass' and str(humanMsBool) == 'Pass':
        humanReactionDecision = 'Pass'
    else:
        humanReactionDecision = 'Failed'


    #Making the decision maker output table.
    decisionTable = Tabular('|c|c|c|c|')
    decisionTable.add_hline()

    #Adding the Human decision.

    #Human NMR decision.
    decisionTable.add_row('', 'Human NMR Decision:', MultiColumn(2, align='|c|', data='NMR Spectra Category:'))
    decisionTable.add_row('Human Reaction Decision:', humanNmrBool, MultiColumn(2, align='|c|', data=humanNmrClass))
    decisionTable.add_hline(start=2)

    #Human MS decision.
    decisionTable.add_row(humanReactionDecision, 'Human MS Decision:', MultiColumn (2, align='|c|', data='MS Spectra Category:'))
    decisionTable.add_row('', humanMsBool, MultiColumn(2, align='|c|', data=humanMsClass))
    decisionTable.add_hline()

    #Adding Decision maker decision.

    #Decision maker NMR decision.
    decisionTable.add_row('', '', MultiColumn(2, align='|c|', data='NMR Criteria 1:'))
    decisionTable.add_row('', 'Decision Maker NMR Decision:', MultiColumn(2, align='|c|', data='N/A'))
    decisionTable.add_hline(3,4)
    decisionTable.add_row('', 'N/A', MultiColumn(2, align='|c|', data='NMR Criteria 2:'))
    decisionTable.add_row('Decision Maker Reaction Decision:', '', MultiColumn(2, align='|c|', data='N/A'))
    decisionTable.add_hline(2)

    #Decision maker Ms decision.
    decisionTable.add_row('N/A', '', 'MS Criteria 1 and 2:', 'Number of predicted peaks found in')
    decisionTable.add_row('', 'Decision Maker MS Decision:', msCriteria1And2Bool, 'MS spectra with appropriate intensity:')
    decisionTable.add_row('', decisionMakerMsBool, '', msCriteria1and2Decisions)
    decisionTable.add_hline(3)
    decisionTable.add_row('', '', 'MS Criteria 3:', 'Number of counter-ions found:')
    decisionTable.add_row('', '', msCriteria3Bool, msCriteria3Decisions)
    decisionTable.add_hline()



    # #Human NMR decision.
    # decisionTable.add_row('', 'Human NMR Decision:',' Spectra Category:', '')
    # decisionTable.add_row('Human Reaction Decision', humanNmrBool, humanNmrClass, '')
    
    # #Human MS decision.
    # decisionTable.add_row(humanReactionDecision, 'Human MS Decision:', 'Spectra Category:', '')
    # decisionTable.add_row('', humanMsBool, humanMsClass, '')
    
    # #Adding Decision maker decision.

    # #Decision maker NMR decision.
    # decisionTable.add_row('', '', 'Criteria 1:', '')
    # decisionTable.add_row('', 'Decision Maker NMR Decision:', 'N/A', '')
    # decisionTable.add_row('', 'N/A', 'Criteria 2:', '')
    # decisionTable.add_row('Decision Maker Reaction Decision', '', 'N/A', '')
    
    # #Decision maker Ms decision.
    # decisionTable.add_row('N/A', '', 'MS Criteria 1 and 2', 'Number of predicted peaks found in')
    # decisionTable.add_row('', 'Decision Maker MS Decision', msCriteria1And2Bool, 'MS spectra with appropriate intensity:')
    # decisionTable.add_row('', decisionMakerMsBool, '', msCriteria1and2Decisions)
    # decisionTable.add_row('', '', 'MS Criteria 3:', 'Number of counter-ions found:')
    # decisionTable.add_row('', '', msCriteria3Bool, msCriteria3Decisions)



 

    # #Adding the Human NMR decision. 
    # decisionTable.add_row('', 'Human NMR Decision:',' Spectra Category:')
    # decisionTable.add_row('Human Reaction Decision:', humanNmrBool, humanNmrClass)
    # decisionTable.add_hline(2)
    
    # #Adding the Human MS decision.
    # decisionTable.add_row(humanReactionDecision, 'Human MS Decision:', 'Spectra Category:')
    # decisionTable.add_row('', humanMsBool, humanMsClass)
    # decisionTable.add_hline()
    
    # #Adding the decision Maker Ms decision.
    # decisionTable.add_row('', 'MS Criteria 1 and 2 :', 'Number of predicted peaks found in')
    # decisionTable.add_row('Decision Maker Reaction Decision:', msCriteria1And2Bool, 'MS spectra with appropriate intensity:')
    # decisionTable.add_row('Not recorded', '', msCriteria1and2Decisions)
    # decisionTable.add_hline(2)
    # decisionTable.add_row('', 'MS Criteria 3:', 'Number of counter-ions found:')
    # decisionTable.add_row('', msCriteria3Bool, msCriteria3Decisions)
    # decisionTable.add_hline(2)
    # decisionTable.add_hline()

    #Adding the Decision table to the document along with its label.
    Label = '\\' + 'caption' + '{''Human labled and Decsision maker labled outcomes for the \\textsuperscript' + '{' + '1' +'}' 'H NMR spectroscopy and ULPC-MS spectrometry of reaction ' + str(reactionId) + '.' + ' Decision motivations are also given.' + '}'
    document.append(NoEscape(r'\begin{Decision Table}[H]'))
    document.append(decisionTable)
    document.append(NoEscape(Label))
    document.append(NoEscape(r'\end{Decision Table}'))

    return document


def generateReactionScheme(document: ReactionDataDocument, aldehdyeFigure: str, amineFigure: str, metalFigure: str, reactionID: str, reactionLable: str, aldehydeID: int, amineID: int, metal: str, aldehydeRatio: int, amineRatio: int, metalRatio: int):
    """Generates the reaction scheme used for the reaction. This is just an image of the three reagents used, along if they form a supramolecular structure or not."""
    
    #Checking if the reaction label is 1 or 0.
    if str(reactionLable) == '1':
        #Path to success self assembly picture
        reactionOutcome = strCWD + '/DataAnalysisWorkflow/FigureGeneration/imagesForFigures/selfassemblySuccessful.png'
    else:
        #Path to failed self assembly picture
        reactionOutcome = strCWD + '/DataAnalysisWorkflow/FigureGeneration/imagesForFigures/selfassemblyFailed.png'

    #The label for the scheme.
    label = '\\' + 'caption' + '{' + 'Self-assembly of components ' + str(aldehydeID) + ', ' + str(amineID) + ', ' + 'with ' + str(metal) + ' in a ' + str(aldehydeRatio) + ':' + str(amineRatio) + ':' + str(metalRatio) + ' molar ratio in CH$_3$CN at 60\\textdegree C for 40h. These are the reagents (starting materials) for reaction ' + str(reactionID) + '.' + '}'
    
    #Creating a minipage with the images of the reagents

    #This is such a hack but I low key dont care.
    line1 = r'\begin{scheme}[H]'
    line2 = r'\begin{minipage}{0.5\textwidth}'
    line3 = r'\includegraphics[width=0.4\textwidth]' + '{' + aldehdyeFigure + '}' #%This is the path to the aldehdye image.
    line4 = r'\includegraphics[width=0.4\textwidth]' + '{' + amineFigure + '}' #%This is the path to the amine image.
    line5 = r'\includegraphics[width=0.1\textwidth]' + '{' + metalFigure + '}' #%This is the path to the metal image.
    line6 = r'\end{minipage}'
    line7 = r'\begin{minipage}{0.5\textwidth}' #The section with sucessful or not MS.
    line8 = r'\begin{center}'
    line9 = r'\includegraphics[width=0.7\textwidth]' + '{' + reactionOutcome + '}' #Path to image of sucessful or not self assembly.
    line10 = r'\end{center}'
    line11 = r'\end{minipage}'
    line12 = label
    line13 = r'\end{scheme}'
    
    lineToAdd = (line1, line2, line3, line4, line5, line6, line7, line8, line9, line10, line11, line12, line13)
    for latexLine in lineToAdd:
        document.append(NoEscape(latexLine))
  
    return document


def generateNmrFigure(document: ReactionDataDocument, reactionID: str, aldehdyeNmr: str, amineNmr: str, reactionNmr: str):
    """Generating the stacked NMR spectra for the amine, aldehyde, and reaction NMR. This is then added to the document along with a caption."""
    
    label = '\\' + 'caption' + '{' + 'The stacked \\textsuperscript' + '{' + '1' +'}' 'H NMR spectra of the aldehyde (top), amine (middle), and reaction sample (bottom) for reaction ' + str(reactionID) + '.' + '}' 
    
    line1 = r'\begin{NMR Spectra}[H]'
    line2 = r'\begin{center}'
    line3 = r'\includegraphics[width=1\textwidth]' + '{' + aldehdyeNmr + '}\\hfill' #%This is the path to the aldehdye nmr image.
    line4 = r'\includegraphics[width=1\textwidth]' + '{' + amineNmr + '}\\hfill' #%This is the path to the amine nmr image.
    line5 = r'\includegraphics[width=1\textwidth]' + '{' + reactionNmr + '}\\hfill' #%This is the path to the metal nmr image.
    line6 = r'\end{center}'
    line7 = label
    line8 = r'\end{NMR Spectra}'
    
    lineToAdd = (line1, line2, line3, line4, line5, line6, line7, line8)
    for latexLine in lineToAdd:
        document.append(NoEscape(latexLine))

    return document

def generateMsFigure(document: ReactionDataDocument, reactionID: str, reactionMs: str):
    """Generates a figure for the ULPC-MS spectra of the combination / reaction. It then adds it to the document with a caption."""

    label = '\\' + 'caption' + '{' + 'The ULPC-MS spectra of reaction ' + str(reactionID) + '. The intensity threshold is also shown.' + '}'
    
    line1 = r'\begin{MS Spectra}[H]'
    line2 = r'\begin{center}'
    line3 = r'\includegraphics[width=1\textwidth]' + '{' + reactionMs + '}\\hfill' #%This is the path to the reaction mass spectra image.
    line4 = r'\end{center}'
    line5 = label
    line6 = r'\end{MS Spectra}'
    
    lineToAdd = (line1, line2, line3, line4, line5, line6)
    for latexLine in lineToAdd:
        document.append(NoEscape(latexLine))

    return document
