import json

import pandas as pd


class HostGuestPlanner:
    """
    ReplicationPlanner class for generating chemspeed workflow instructions
    from screening experiment results.

    Args:
    - screening_data (str): Path to the JSON file containing screening
    experiment results.
    - predicted_ms (str): Path to the JSON file containing predicted masses
      of complexes.
    - import_file (str): Path to the CSV file for importing chemspeed workflow
      data.

    Attributes:
    - screening_data (str): Path to the JSON file containing screening e
    xperiment results.
    - predicted_ms (str): Path to the JSON file containing predicted masses
    of complexes.
    - df (pd.DataFrame): DataFrame for chemspeed workflow data.

    """

    def __init__(self, replication_data, import_file):
        self.replication_data = replication_data
        self.df = pd.read_csv(import_file)

    def data_loader(self):
        """Load screening and mass data from specified JSON files."""
        with open(f"{self.replication_data}", "r") as f:
            self.data = json.load(f)

    def identification_successful_experiments(self):
        """
        Identify experiments selected for replication.

        Returns:
        - List[str]: List of experiment IDs selected for replication.

        """
        self.replication_list = [
            exp for exp in self.data if self.data[exp]["REPLICATED"]
        ]
        return self.replication_list

    def generate_nmr_dict(self):
        """
        Create a dictionary of NMR experiments containing the nature of the
        complex being replicated and the type of nmr experiment to be run.

        Returns:

        - Dict[int, Dict[str, Any]]: Dictionary with experiment indices and
        NMR experiment details.

        """
        self.replication_list = self.identification_successful_experiments()
        nmr_dict = {}
        counter = 0
        for exp in self.replication_list:  # might need changing
            for _ in range(6):
                counter += 1
                nmr_dict[counter] = {
                    "sample_info": {"screening_id": exp},
                    "solvent": "CH3CN",
                    "nmr_experiments": ["MULTISUPPDC70_f"],
                }

        return nmr_dict

    def update_chemspeed_dataframe(self):
        """Update chemspeed DataFrame with replication information."""
        self.df.loc[self.df["Experiment"] == 1, ["Program"]] = 3

    def generate_chemspeed_csv(self, csv_path):
        """
        Generate and save chemspeed CSV file.

        Args:
        - csv_path (str): Path to save the generated CSV file.

        """
        self.update_chemspeed_dataframe()
        self.df.to_csv(csv_path, index=False)

    def generate(self, csv_path):
        """
        Generate all necessary files for the replication workflow.

        Args:
        - csv_path (str): Path to save the generated chemspeed CSV file.
        - ms_path (str): Path to save the generated MS peaks JSON file.
        - nmr_path (str): Path to save the generated NMR experiments JSON file.

        """
        self.generate_chemspeed_csv(csv_path)
