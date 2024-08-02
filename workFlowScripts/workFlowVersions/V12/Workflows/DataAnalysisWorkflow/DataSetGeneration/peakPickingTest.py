# from DataAnalysisWorkflow.DataSetGeneration.dependencies.modules.synthesis_bots.utils.nmr.processing import NMRExperiment
# from DataAnalysisWorkflow.DataSetGeneration.dependencies.modules.synthesis_bots.utils.nmr.acquisition import FOURIER

import os
import importlib.util
import sys

rawCWD = os.getcwd()                                                                                                                                        #Code snippet taken from stack overflow: https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
strCWD = ''.join([letter if letter != '\\' else '/' for letter in rawCWD])

#Importing synthesis_bots.utils.nmr.processing
nmrProcessingPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/dependencies/modules/synthesis_bots/utils/nmr/processing.py'
spec = importlib.util.spec_from_file_location('nmrProcessing', nmrProcessingPath)
nmrProcessing = importlib.util.module_from_spec(spec)
sys.modules['nmrProcessing'] = nmrProcessing
spec.loader.exec_module(nmrProcessing)

#Importing synthesis_bots.utils.nmr.acquisition
nmrAcquisitionPath = strCWD + '/DataAnalysisWorkflow/DataSetGeneration/dependencies/modules/synthesis_bots/utils/nmr/acquisition.py'
spec = importlib.util.spec_from_file_location('nmrAcquisition', nmrAcquisitionPath)
nmrAcquisition = importlib.util.module_from_spec(spec)
sys.modules['nmrAcquisition'] = nmrAcquisition
spec.loader.exec_module(nmrAcquisition)


nmrTestPath = 'C:/Users/emanuele/Desktop/PlacementEssay/PlacementEssay/backup/ChemspeedPlatformAllVersions/V12/Workflows/Data/StartingMaterials/NmrData/reagentAnalysis-18'
nmr = nmrProcessing.NMRExperiment(nmrAcquisition.FOURIER.open_experiment(nmrTestPath))

nmr.process_spectrum(zero_filling="8k", line_broadening=1.2, reference=True,)

peaks_ppm = nmr.pick_peaks(
            reference_intensity=100,
            minimum_intensity=0.5,
            sensitivity=10,
            ppm_range=[11, 6],
        )
nmr.plot_nmr()
print(peaks_ppm)