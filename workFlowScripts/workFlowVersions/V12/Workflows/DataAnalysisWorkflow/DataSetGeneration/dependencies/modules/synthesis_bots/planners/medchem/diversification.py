"""Planner for MedChem diversification."""

import json
import re
from itertools import product
from pathlib import Path

import pandas as pd

from synthesis_bots.utils.ms.exact_mass import Molecule

# Constants for leaving groups for Sonogashira
LEAVING_FOR = {"H": "1", "Br": "1"}

# Constants for NMR experiments
NMR_SOLVENT = "CH2Cl2"
NMR_EXPERIMENTS = ["MULTISUPPDC_f"]


class DiversificationPlanner:
    """
    A class to plan and manage diversification experiments via Sonogashira
    coupling and CuAAC cycloaddition from an input CSV file containing
    informations about the chemicals to be used and from the results obtained
    during the replication step of the workflow.

    Attributes:
    replication_data (str): Path to the replication data JSON file containing
    the information about the outcome of the replication step.
    replication_nmr (str): Path to the NMR aquisition data for the replication
    experiment as a JSON file.
    replication_ms (str):  Path to the MS aquisition data for the replication
    experiment as a JSON file.
    input_file (str): Path to the input CSV file containg the a "Code", a
    chemical "Type", the "CAS" and the "Molecular Formula" of each chemical
    to be used.
    import_file (str): Path to the ChemSpeed import CSV file.
    df_chemspeed (pd.DataFrame): A Pandas DataFrame containing ChemSpeed data
    to be used for the diversification step.
    df (pd.DataFrame): A Pandas DataFrame containing experiment data.
    dict_experiments (dict): A dictionary containing experiment details.

    """

    def __init__(
        self,
        replication_data: Path,
        replication_nmr: Path,
        replication_ms: Path,
        input_file: Path,
        import_file: Path,
    ):
        """
        Initialize the DiversificationPlanner with necessary file paths.

        Args:
        replication_data (str): Path to the replication data JSON file.
        replication_nmr (str): Path to the replication NMR data JSON file.
        replication_ms (str): Path to the replication MS data JSON file.
        input_file (str): Path to the input CSV file.
        import_file (str): Path to the ChemSpeed import CSV file.

        """
        self.replication_data = replication_data
        self.replication_nmr = replication_nmr
        self.replication_ms = replication_ms
        self.df_chemspeed = pd.read_csv(import_file)
        self.df = pd.read_csv(input_file)
        self.dict_experiments: dict[str, tuple[str, str]] = {}

        self.data_loader()
        self.populate_experiment_dictionary()
        self.create_experiment_dataframe()

    def data_loader(self) -> None:
        """Load replication outcome, aquisition data for mass and nmr from
        replication from specified JSON files."""
        with open(f"{self.replication_data}", "r") as f:
            self.data = json.load(f)
        with open(f"{self.replication_nmr}", "r") as f:
            self.nmr_data = json.load(f)
        with open(f"{self.replication_ms}", "r") as f:
            _ms_data = json.load(f)

        ms_data = {}
        for exp_no, species in _ms_data.items():
            names = []
            for structure in species.keys():
                names.append(structure.split()[0])
            structures: dict[str, dict[str, float]] = {
                name: {} for name in names
            }
            for structure, mzs in species.items():
                name, adduct = structure.split()
                structures[name].update({adduct: mzs["1"]})
            ms_data[exp_no] = structures
        self.ms_data = ms_data

    def identification_diversification_experiments(self) -> list:
        """
        Identify diversification experiments from replication outcome.

        Returns:
        list: A list of experiments identified for replication.

        """
        replication_list = [
            exp for exp in self.data if "REPLICATED" in self.data[exp]
        ]
        return replication_list

    def urea_product_finder(self) -> list:
        """
        Find urea products formed during replication from the loaded data.

        Returns:
        list: A list of urea products.

        """
        r_data = self.identification_diversification_experiments()

        urea_list = []

        for key, value in self.data.items():
            if key in r_data:
                urea = (
                    f"{value['sample_info']['amine']}_"
                    f"{value['sample_info']['isocyanate']}"
                )
                urea_list.append(urea)

        return urea_list

    def populate_experiment_dictionary(self) -> None:
        """Populate a dictionary with all possible combinations of experiments,
        from the coupling partner selected for the Sonogashira coupling and
        CuAAC cycloaddition and presented in the input file."""
        exp = 1

        new_reagents = self.df["Code"].tolist()
        ureas = self.urea_product_finder()

        for reagent in new_reagents:
            for combination in product([reagent], ureas):
                self.dict_experiments[f"Exp{exp}"] = combination
                exp += 1

    def create_experiment_dataframe(self) -> None:
        """
        Create a Pandas DataFrame from the experiment dictionary.

        Returns:
        pd.DataFrame: A DataFrame containing experiment details.

        """
        dict_list = [
            {
                "Experiment": experiment,
                "Reagent": reagents[0],
                "Urea": reagents[1],
            }
            for experiment, reagents in self.dict_experiments.items()
        ]

        self.df_experiments = pd.DataFrame(dict_list)

    def generate_experiment_list(self) -> None:
        """
        Generate a CSV file containing a list of experiments.

        Args:
        output_file (str): Path to the output CSV file.

        """
        self.df_experiments.to_csv(
            "list_experiments_diversification.csv", index=False
        )

    def calculate_mass_modification_fragment(self, formula: str) -> float:
        """
        Calculate the mass modification induced by the coupling partner
        selected for the Sonogashira coupling and CuAAC cycloaddition.

        Args:
        formula (str): The molecular formula.

        Returns:
        float: The calculated mass modification.

        """
        pattern = r"([A-Z][a-z]*)(?:_\{(\d*)\})?"
        elements = re.findall(pattern, formula)

        formula_dict = {}
        for element in elements:
            formula_dict[element[0]] = element[1]

        output = ""
        for element, count in formula_dict.items():
            output += element + str(count)

        mol = Molecule(output)
        mass = mol.isotopic_distribution(charge=0)

        return round(mass[0][mass[1].argmax()], 2)

    def calculate_mass_diversification(
        self, experiment: str, mass: float
    ) -> float:
        """
        Calculate the mass of the product formed via the Sonogashira coupling
        or CuAAC cycloaddition selected from the mass of a given urea product.

        Args:
        experiment (str): The experiment ID.
        mass (dict): Dictionary of masses for different adducts.

        Returns:
        float: The new mass after diversification.

        """
        reagent = self.df_experiments.loc[
            self.df_experiments["Experiment"] == experiment, ["Reagent"]
        ].values[0]

        formula_pyr = self.df.loc[
            self.df["Code"] == "Pyr", ["Molecular Formula"]
        ].values[0]

        formula_zido = self.df.loc[
            self.df["Code"] == "Zido", ["Molecular Formula"]
        ].values[0]

        if reagent == "Pyr":
            new_mass = (
                mass
                - self.calculate_mass_modification_fragment(str(LEAVING_FOR))
                + self.calculate_mass_modification_fragment(str(formula_pyr))
            )

        elif reagent == "Zido":
            new_mass = mass + self.calculate_mass_modification_fragment(
                str(formula_zido)
            )

        else:
            raise ValueError("No such reagent exists.")

        return new_mass

    def isolate_masses_for_diversification(self) -> dict:
        """
        Isolate masses of ureas selected for replication.

        Returns:
        - Dict[str, float]: Dictionary of experiment IDs and corresponding
        predicted masses.

        """
        r_data = self.identification_diversification_experiments()

        ms_replication = {}

        for entry in [
            value for (key, value) in self.ms_data.items() if key in r_data
        ]:
            ms_replication.update(entry)

        return ms_replication

    def update_masses_for_diversification(self) -> dict:
        """
        Update masses for diversification experiments, generating the mass of
        the expected product for either the Sonogashira coupling or the CuAAC
        cycloaddition selected.

        Returns:
        dict: Dictionary of possible masses for diversification.

        """
        ms_replication = self.isolate_masses_for_diversification()
        dict_possible_mass = {}
        adducts = ["[M+H]+", "[M+CH3CN+H]+", "[M+Na]+", "[M+K]+"]

        list_experiments = list(self.df_experiments["Experiment"])

        list_replication_products = [
            (key, value) for (key, value) in ms_replication.items()
        ] * (self.df_experiments["Reagent"].nunique())

        for exp, (prod, mass) in zip(
            list_experiments, list_replication_products
        ):
            reagent = self.df_experiments.loc[
                self.df_experiments["Experiment"] == exp, ["Reagent"]
            ].values[0]

            if reagent == "Pyr":
                exp_no = int(exp.replace("Exp", "")) + 6

            elif reagent == "Zido":
                exp_no = int(exp.replace("Exp", "")) + 7

            else:
                raise ValueError("Unknown reagent.")

            dict_possible_mass[exp_no] = {
                f"{prod}_{str(reagent[0])}": {
                    adduct: self.calculate_mass_diversification(
                        exp, mass[adduct]
                    )
                    for adduct in adducts
                }
            }

        reformatted_dict = {}
        for exp_num, molecules in dict_possible_mass.items():
            structures = {}
            for mol, adds in molecules.items():
                for adduct, mass in adds.items():
                    structures[f"{mol} {adduct}"] = {"1": mass}
            reformatted_dict[exp_num] = structures

        return reformatted_dict

    def generate_nmr_dict(self) -> dict:
        """
        Generate a JSON file containing a list of experiments to run on the
        benchtopNMR.

        Returns:
        dict: Dictionary of NMR experiments.

        """
        dict_nmr = {}

        for experiment in self.df_experiments["Experiment"]:
            reagent = self.df_experiments.loc[
                self.df_experiments["Experiment"] == experiment, ["Reagent"]
            ].values[0]

            urea = self.df_experiments.loc[
                self.df_experiments["Experiment"] == experiment, ["Urea"]
            ].values[0]

            if reagent == "Pyr":
                number = int(experiment.replace("Exp", "")) + 6

            elif reagent == "Zido":
                number = int(experiment.replace("Exp", "")) + 7

            else:
                raise ValueError("Unknown reagent.")

            dict_nmr[f"{number}"] = {
                "sample_info": {
                    "urea": urea[0],
                    "reagent": reagent[0],
                },
                "solvent": NMR_SOLVENT,
                "nmr_experiments": NMR_EXPERIMENTS,
            }

        return dict_nmr

    def update_chemspeed_dataframe(self) -> None:
        """Update the ChemSpeed DataFrame."""
        r_data = self.identification_diversification_experiments()

        for exp in self.df_chemspeed["Index"]:
            if f"{exp}" in r_data:
                self.df_chemspeed.loc[
                    self.df_chemspeed["Index"] == int(exp),
                    ["ReplicationBinary"],
                ] = 1
            else:
                self.df_chemspeed.loc[
                    self.df_chemspeed["Index"] == int(exp),
                    ["ReplicationBinary"],
                ] = 0

        self.df_chemspeed.loc[self.df_chemspeed["Index"] == 1, ["Program"]] = 3

    def generate_chemspeed_csv(self, csv_path: Path) -> None:
        """
        Generate and save chemspeed CSV file.

        Args:
        - csv_path (str): Path to save the generated CSV file.

        """
        self.update_chemspeed_dataframe()
        self.df_chemspeed.to_csv(csv_path, index=False)

    def save_mass_diversification(self, ms_path: Path) -> None:
        """
        Save MS peaks to a JSON file.

        Args:
        ms_path (str): Path to save the generated MS peaks JSON file.

        """
        d = self.update_masses_for_diversification()
        with open(ms_path, "w") as f:
            json.dump(d, f, indent=4)

    def save_nmr_diversification(self, nmr_path: Path) -> None:
        """
        Save NMR experiments to a JSON file.

        Args:
        nmr_path (str): Path to save the generated NMR experiments JSON file.

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
        Generate all necessary files for the diversification workflow.

        Args:
        csv_path (str): Path to save the generated ChemSpeed CSV file.
        ms_path (str): Path to save the generated MS peaks JSON file.
        nmr_path (str): Path to save the generated NMR experiments JSON file.

        """
        self.save_mass_diversification(ms_path)
        self.generate_chemspeed_csv(csv_path)
        self.save_nmr_diversification(nmr_path)
