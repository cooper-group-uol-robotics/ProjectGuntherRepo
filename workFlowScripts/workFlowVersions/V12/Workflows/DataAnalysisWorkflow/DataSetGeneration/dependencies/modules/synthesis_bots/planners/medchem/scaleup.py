import json
from pathlib import Path

import pandas as pd


class ScaleupPlanner:
    """
    A class to plan replication experiments based on screening data.

    Args:
    screening_data (str): Path to the screening data JSON file, containing the
    information about the outcome of the screening experiments.
    screening_nmr (str): Path to the NMR aquisition data for the screening
    experiment as a JSON file.
    predicted_ms (str): Path to the MS aquisition data for the screening
    experiment as a JSON file.
    import_file (str): Path to the import file a CSV file containing the
    Chemspeed instuctions .

    """

    def __init__(
        self,
        screening_data: Path,
        screening_nmr: Path,
        predicted_ms: Path,
        import_file: Path,
    ):
        """
        Initialize the ScaleupPlanner with the necessary data.

        Args:
        screening_data (str): Path to the screening data JSON file.
        screening_nmr (str): Path to the NMR screening data JSON file.
        predicted_ms (str): Path to the predicted MS peaks JSON file.
        import_file (str): Path to the import file.

        """
        self.screening_data = screening_data
        self.screening_nmr = screening_nmr
        self.predicted_ms = predicted_ms
        self.df = pd.read_csv(import_file)

    def data_loader(self) -> None:
        """Load screening outcome, aquisition data for mass and nmr from
        replication from specified JSON files."""
        with open(f"{self.screening_data}", "r") as f:
            self.data = json.load(f)
        with open(f"{self.screening_nmr}", "r") as f:
            self.nmr_data = json.load(f)
        with open(f"{self.predicted_ms}", "r") as f:
            self.ms_data = json.load(f)

    def identify_replicas(self) -> list:
        """
        Identify experiments marked for replication from the screening
        experiment outcome.

        Returns:
        list: List of experiments marked for replication.

        """
        self.replication_list = [
            exp for exp in self.data if self.data[exp]["SCALEUP"]
        ]
        return self.replication_list

    def generate_ms_dict(self) -> dict:
        """
        Generate a dictionary of MS peaks for replication experiments based on
        the MS peak generated for the screening experiment.

        Returns:
        dict: Dictionary of MS peaks for replication experiments.

        """
        self.data_loader()
        r_data = self.identify_replicas()

        ms_dict = {
            f"{key}": value
            for (key, value) in self.ms_data.items()
            if key in r_data
        }

        return ms_dict

    def generate_nmr_dict(self) -> dict:
        """
        Generate a dictionary of NMR data for replication experiments based on
        the NMR data aquisition used for the screening experiment.

        Returns:
        dict: Dictionary of NMR data for replication experiments.

        """
        self.data_loader()
        r_data = self.identify_replicas()

        nmr_dict = {
            f"{key}": value
            for (key, value) in self.nmr_data.items()
            if key in r_data
        }

        return nmr_dict

    def update_chemspeed_dataframe(self) -> None:
        """Update the ChemSpeed DataFrame with replication information."""
        self.data_loader()
        r_data = self.identify_replicas()

        for exp in r_data:
            self.df.loc[
                self.df["Index"] == int(exp), ["ReplicationBinary"]
            ] = 1

        self.df.loc[self.df["Index"] == 1, ["Program"]] = 2

    def generate_chemspeed_csv(self, csv_path: Path) -> None:
        """
        Generate and save a ChemSpeed CSV file.

        Args:
        csv_path (str): Path to save the generated CSV file.

        """
        self.update_chemspeed_dataframe()
        self.df.to_csv(csv_path, index=False)

    def save_mass_replication(self, ms_path: Path) -> None:
        """
        Predict and save the MS peaks to a JSON file with the given name.

        Args: output_file_name (str): The name of the output JSON file
        (excluding the file extension).

        """
        d = self.generate_ms_dict()
        with open(ms_path, "w") as f:
            json.dump(d, f, indent=4)

    def save_nmr_replication(self, nmr_path: Path) -> None:
        """
        Predict and save the MS peaks to a JSON file with the given name.

        Args: output_file_name (str): The name of the output JSON file
        (excluding the file extension).

        """
        d = self.generate_nmr_dict()
        with open(nmr_path, "w") as f:
            json.dump(d, f, indent=4)

    def generate(
        self,
        csv_path: Path,
        ms_path: Path,
        nmr_path: Path,
    ) -> None:
        """
        Generate all necessary files for the replication workflow.

        Args:
        - csv_path (str): Path to save the generated chemspeed CSV file.
        - ms_path (str): Path to save the generated MS peaks JSON file.
        - nmr_path (str): Path to save the generated NMR experiments JSON file.

        """
        self.save_mass_replication(ms_path)
        self.generate_chemspeed_csv(csv_path)
        self.save_nmr_replication(nmr_path)
