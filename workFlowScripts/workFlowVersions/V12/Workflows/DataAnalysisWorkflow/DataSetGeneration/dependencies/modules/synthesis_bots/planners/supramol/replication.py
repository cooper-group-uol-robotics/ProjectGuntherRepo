import json
import math
from collections import Counter

import pandas as pd


class ReplicationPlanner:
    """
    ReplicationPlanner class for generating chemspeed workflow instructions
    from screening experiment results.

    Args:
    - screening_data (str): Path to the JSON file containing screening e
    xperiment results.
    - predicted_ms (str): Path to the JSON file containing predicted masses
      of complexes.
    - import_file (str): Path to the CSV file for importing chemspeed workflow
    data.

    Attributes:
    - screening_data (str): Path to the JSON file containing screening
    experiment results.
    - predicted_ms (str): Path to the JSON file containing predicted
    masses of complexes.
    - df (pd.DataFrame): DataFrame for chemspeed workflow data.

    """

    def __init__(self, screening_data, predicted_ms, import_file):
        self.screening_data = screening_data
        self.predicted_ms = predicted_ms
        self.df = pd.read_csv(import_file)

    def data_loader(self):
        """Load screening and mass data from specified JSON files."""
        with open(f"{self.screening_data}", "r") as f:
            self.data = json.load(f)
        with open(f"{self.predicted_ms}", "r") as f:
            self.ms_data = json.load(f)

    def identification_replication_experiments(self):
        """
        Identify experiments selected for replication.

        Returns:
        - List[str]: List of experiment IDs selected for replication.

        """
        self.replication_list = [
            exp for exp in self.data if self.data[exp]["REPLICATION"]
        ]
        return self.replication_list

    def isolate_masses_for_replication(self):
        """
        Isolate masses of complexes selected for replication.

        Returns:
        - Dict[str, float]: Dictionary of experiment IDs and corresponding
        predicted masses.

        """
        self.data_loader()
        r_data = self.identification_replication_experiments()

        ms_replication = {
            f"{key}": value
            for (key, value) in self.ms_data.items()
            if key in r_data
        }

        return ms_replication

    def generate_mass_experiment_dict(self):
        """
        Create a dictionary of mass experiments containing predicted masses for
        each experiment.

        Returns:
        - Dict[int, float]: Dictionary with experiment indices and
        corresponding predicted masses.

        """
        ms_dict = {}
        ms_replication = self.isolate_masses_for_replication()

        for index, value in enumerate(ms_replication.values()):
            for n in range(1, 7):
                ms_dict[index * 6 + n] = value

        return ms_dict

    def generate_nmr_dict(self):
        """
        Create a dictionary of NMR experiments containing the nature of the
        complex being replicated and the type of nmr experiment to be run.

        Returns:
        - Dict[int, Dict[str, Any]]: Dictionary with experiment indices and
        NMR experiment details.

        """
        self.replication_list = self.identification_replication_experiments()
        nmr_dict = {}
        counter = 0
        for exp in self.replication_list:
            sample_info = self.data[exp]["sample_info"]
            for _ in range(6):
                counter += 1
                nmr_dict[counter] = {
                    "sample_info": sample_info,
                    "solvent": "CH3CN",
                    "nmr_experiments": ["MULTISUPPDC70_f"],
                }
                nmr_dict[counter]["sample_info"]["screening_id"] = exp

        return nmr_dict

    def find_reagents_for_replication(self):
        """
        Find reagents involved in replication experiments based on screening
        conditions.

        Returns:
        - Dict[str, List[Union[str, None]]]: Dictionary with experiment IDs
        and associated reagents.

        """
        self.data_loader()
        r_data = self.identification_replication_experiments()

        reagents = {
            f"{key}": [
                self.data[key]["carbonyl"],
                self.data[key]["amine"],
                self.data[key]["metal"],
            ]
            for key in self.ms_data.keys()
            if key in r_data
        }

        return reagents

    def count_reagent_occurrences(self):
        """
        Count occurrences of each reagent in replication experiments.

        Returns:
        - Counter: Counter object with reagent occurrences.

        """
        reagents_dict = self.find_reagents_for_replication()

        all_reagents = [
            reagent
            for reagent_list in reagents_dict.values()
            for reagent in reagent_list
        ]

        occurrence_counter = Counter(all_reagents)

        return occurrence_counter

    def calculate_required_runs(self):
        """
        Determine the number of chemspeed runs needed for replication.

        Returns:
        - int: Number of chemspeed runs needed.

        """
        self.data_loader()
        r_data = self.identification_replication_experiments()

        nbr_replication_exp = math.ceil(len(r_data) / 3)

        return nbr_replication_exp

    def update_chemspeed_dataframe(self):
        """Update chemspeed DataFrame with replication information."""
        replication_length = len(self.identification_replication_experiments())

        replication_experiments = [n + 1 for n in range(replication_length)]

        source_experiments = [
            int(item) for item in self.identification_replication_experiments()
        ]

        replication_binary = [1] * min(replication_length, 3) + [0] * max(
            0, 3 - replication_length
        )

        columns_to_copy = [
            "ZnNTf",
            "CuBF4",
            "Tris",
            "Tren",
            "Di",
            "Ald1",
            "Ket",
            "Ald2",
        ]

        for rep_exp, source_exp in zip(
            replication_experiments, source_experiments
        ):
            self.df.loc[
                self.df["Experiment"] == rep_exp,
                ["Prog2 " + col for col in columns_to_copy],
            ] = self.df.loc[
                self.df["Experiment"] == source_exp, columns_to_copy
            ].values

        self.df.loc[self.df["Experiment"] == 1, ["Program"]] = 2

        self.df["ReplicationBinary"] = replication_binary + [""] * 15

        self.df["RxnDilution"] = [3] + [""] * 17

        self.df["LCMS"] = [0.1] + [""] * 17

        self.df["LCMSDilution"] = [1.9] + [""] * 17

        self.df["NMR"] = [0.7] + [""] * 17

    def adjust_reagent_volumes(self):
        """Adjust stock solution volumes if a reagent is used in more than 2
        reactions during replication."""
        occurrence_counter = self.count_reagent_occurrences()
        for reagent, count in occurrence_counter.items():
            if count > 2:
                prog2_column = "Prog2 " + reagent
                self.df.loc[self.df[prog2_column].notnull(), prog2_column] /= 2

    def generate_chemspeed_csv(self, csv_path):
        """
        Generate and save chemspeed CSV file.

        Args:
        - csv_path (str): Path to save the generated CSV file.

        """
        self.update_chemspeed_dataframe()
        self.adjust_reagent_volumes()
        self.df.to_csv(csv_path, index=False)

    def save_mass_replication(self, ms_path):
        """
        Predict and save the MS peaks to a JSON file with the given name.

        Args: output_file_name (str): The name of the output JSON file
        (excluding the file extension).

        """
        d = self.generate_mass_experiment_dict()
        with open(ms_path, "w") as f:
            json.dump(d, f, indent=4)

    def generate(self, csv_path, ms_path, nmr_path):
        """
        Generate all necessary files for the replication workflow.

        Args:
        - csv_path (str): Path to save the generated chemspeed CSV file.
        - ms_path (str): Path to save the generated MS peaks JSON file.
        - nmr_path (str): Path to save the generated NMR experiments JSON file.

        """
        self.save_mass_replication(ms_path)
        self.generate_chemspeed_csv(csv_path)
        nmr_dict = self.generate_nmr_dict()

        with open(nmr_path, "w") as f:
            json.dump(nmr_dict, f, indent=4)
