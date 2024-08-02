"""
Isotopic masses and ratios.

This code has been ported directly fro pyISOPACh:
https://github.com/AberystwythSystemsBiology/pyISOPACh

which was shared under the MIT License:

MIT License

Copyright (c) 2019 Keiron O'Shea

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import re

import numpy as np
from numpy.typing import NDArray

ELECTRON_WEIGHT = 0.0005484
NP_EMPTY = np.array([])


class Element(object):
    def __init__(self, symbol: str, count: int):
        self.symbol = symbol
        self.count = count
        self._periodic_table = get_periodic_table()[symbol]

    @property
    def molecular_weight(self) -> float:
        return self.atomic_weight * float(self.count)

    @property
    def isotopic_ratios(self) -> list[float]:
        return self._periodic_table["isotopic_ratio"]

    @property
    def atomic_charge(self) -> int:
        return self._periodic_table["atomic_charge"]

    @property
    def atomic_weight(self) -> float:
        isotopic_weight = self.isotopic_weight
        ratios = self._periodic_table["isotopic_ratio"]
        return float(
            np.matrix(ratios) * np.transpose(np.matrix(isotopic_weight))
        )

    @property
    def isotopic_weight(self) -> list[float]:
        return self._periodic_table["isotopic_weight"]


class Molecule:
    def __init__(self, molecular_formula: str):
        self.molecular_formula = molecular_formula
        self._structure_dict = self._generate_structure_dict()

    @property
    def num_atoms(self) -> int:
        return sum(self._structure_dict.values())

    @property
    def molecular_weight(self) -> float:
        return sum([elem.molecular_weight for elem in self._as_elements])

    @property
    def _as_elements(self) -> list[Element]:
        return [Element(s, c) for (s, c) in self._structure_dict.items()]

    def _generate_structure_dict(self) -> dict:
        parsed = re.findall(
            r"([A-Z][a-z]*)(\d*)|(\()|(\))(\d*)", self.molecular_formula
        )
        structure_dict = {}
        for element_details in parsed:
            element = element_details[0]
            if element not in structure_dict:
                structure_dict[element] = 0
            element_count = sum(
                [int(x) for x in element_details[1:] if x != ""]
            )
            if element_count > 0:
                structure_dict[element] += element_count
            else:
                structure_dict[element] = 1
        return structure_dict

    def isotopic_distribution(self, electrons: int = 0, charge: int = 0):
        def _get_weights_and_ratios() -> tuple[NDArray, NDArray]:
            weights, ratios = [], []

            for elem in self._as_elements:
                for _ in range(elem.count):
                    weights.append(elem.isotopic_weight)
                    ratios.append(elem.isotopic_ratios)

            return np.array(weights, dtype=object), np.array(
                ratios, dtype=object
            )

        def _cartesian_product(
            weights: NDArray,
            ratios: NDArray,
            f_weights: NDArray = NP_EMPTY,
            f_ratios: NDArray = NP_EMPTY,
            count: int = 1,
            cartesian_threshold: float = 0.05,
        ) -> tuple[NDArray, NDArray]:
            new_ratios = []
            new_weights = []

            if count == 1:
                f_ratios = np.array(ratios[0])
                f_weights = np.array(weights[0])

            normalised_ratio = f_ratios / np.max(f_ratios)

            for ratio_indx, _ in enumerate(ratios[count]):
                _ratio = ratios[count][ratio_indx]
                _weight = weights[count][ratio_indx]
                for norm_ratio_indx, _ in enumerate(normalised_ratio):
                    _norm_ratio = normalised_ratio[norm_ratio_indx] * 100  #
                    _norm_weight = f_weights[norm_ratio_indx]  #
                    _transformed_ratio = _norm_ratio * _ratio
                    if _transformed_ratio > cartesian_threshold:
                        new_ratios += [_transformed_ratio]
                        new_weights += [_norm_weight + _weight]
            count = count + 1

            new_weights_np = np.array(new_weights)
            new_ratios_np = np.array(new_ratios)
            if count < len(ratios) and len(new_ratios) < 10000:
                new_weights_np, new_ratios_np = _cartesian_product(
                    weights=weights,
                    ratios=ratios,
                    f_weights=new_weights_np,
                    f_ratios=new_ratios_np,
                    count=count,
                )
            return new_weights_np, new_ratios_np

        def _filter_low_ratios(
            calc_weights: NDArray,
            calc_ratios: NDArray,
            weight_limit: float = 1e-60,
        ) -> tuple[NDArray, NDArray]:
            indx = calc_ratios > weight_limit
            return calc_weights[indx], calc_ratios[indx]

        def _generate_output(
            calc_weights: NDArray, calc_ratios: NDArray
        ) -> tuple[list[float], list[float]]:
            adj_weights = (calc_weights + (ELECTRON_WEIGHT * electrons)) / abs(
                charge
            )
            calc_dict = {x: 0 for x in np.unique(adj_weights)}

            for weight in calc_dict:
                calc_dict[weight] = (
                    np.sum(calc_ratios[adj_weights == weight])
                    * 100
                    / np.max(calc_ratios)
                )

            return list(calc_dict.keys()), list(calc_dict.values())

        if charge == 0:
            charge = 1

        weights, ratios = _get_weights_and_ratios()
        calc_weights, calc_ratios = _cartesian_product(weights, ratios)
        calc_weights, calc_ratios = _filter_low_ratios(
            calc_weights, calc_ratios
        )

        masses, intensities = _generate_output(calc_weights, calc_ratios)

        return np.array(masses), np.array(intensities)


def get_periodic_table() -> dict:
    return {
        "Ru": {
            "isotopic_weight": [
                95.907598,
                97.905287,
                98.9059393,
                99.9042197,
                100.9055822,
                101.9043495,
                103.90543,
            ],
            "atomic_number": 44,
            "atomic_charge": 3,
            "isotopic_ratio": [
                0.0554,
                0.0187,
                0.1276,
                0.126,
                0.1706,
                0.3155,
                0.1862,
            ],
        },
        "Re": {
            "isotopic_weight": [184.9529557, 186.9557508],
            "atomic_number": 75,
            "atomic_charge": 2,
            "isotopic_ratio": [0.374, 0.626],
        },
        "Rf": {
            "isotopic_weight": [261.0],
            "atomic_number": 104,
            "atomic_charge": 0,
            "isotopic_ratio": [1.0],
        },
        "Ra": {
            "isotopic_weight": [226.0],
            "atomic_number": 88,
            "atomic_charge": 2,
            "isotopic_ratio": [1.0],
        },
        "Rb": {
            "isotopic_weight": [84.9117893, 86.9091835],
            "atomic_number": 37,
            "atomic_charge": 1,
            "isotopic_ratio": [0.7217, 0.2783],
        },
        "Rn": {
            "isotopic_weight": [220.0],
            "atomic_number": 86,
            "atomic_charge": 0,
            "isotopic_ratio": [1.0],
        },
        "Rh": {
            "isotopic_weight": [102.905504],
            "atomic_number": 45,
            "atomic_charge": 2,
            "isotopic_ratio": [1.0],
        },
        "Be": {
            "isotopic_weight": [9.0121821],
            "atomic_number": 4,
            "atomic_charge": 2,
            "isotopic_ratio": [1.0],
        },
        "Ba": {
            "isotopic_weight": [
                129.90631,
                131.905056,
                133.904503,
                134.905683,
                135.90457,
                136.905821,
                137.905241,
            ],
            "atomic_number": 56,
            "atomic_charge": 2,
            "isotopic_ratio": [
                0.00106,
                0.00101,
                0.02417,
                0.06592,
                0.07854,
                0.11232,
                0.71698,
            ],
        },
        "Bi": {
            "isotopic_weight": [208.980383],
            "atomic_number": 83,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Bk": {
            "isotopic_weight": [247.0],
            "atomic_number": 97,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Br": {
            "isotopic_weight": [78.9183376, 80.916291],
            "atomic_number": 35,
            "atomic_charge": -1,
            "isotopic_ratio": [0.5069, 0.4931],
        },
        "H": {
            "isotopic_weight": [1.0078250321, 2.014101778],
            "atomic_number": 1,
            "atomic_charge": 1,
            "isotopic_ratio": [0.999885, 0.0001157],
        },
        "P": {
            "isotopic_weight": [30.97376151],
            "atomic_number": 15,
            "atomic_charge": 5,
            "isotopic_ratio": [1.0],
        },
        "Os": {
            "isotopic_weight": [
                183.952491,
                185.953838,
                186.9557479,
                187.955836,
                188.9581449,
                189.958445,
                191.961479,
            ],
            "atomic_number": 76,
            "atomic_charge": 4,
            "isotopic_ratio": [
                0.0002,
                0.0159,
                0.0196,
                0.1324,
                0.1615,
                0.2626,
                0.4078,
            ],
        },
        "Ge": {
            "isotopic_weight": [
                69.9242504,
                71.9220762,
                72.9234594,
                73.9211782,
                75.9214027,
            ],
            "atomic_number": 32,
            "atomic_charge": 2,
            "isotopic_ratio": [0.2084, 0.2754, 0.0773, 0.3628, 0.0761],
        },
        "Gd": {
            "isotopic_weight": [
                151.919788,
                153.920862,
                154.922619,
                155.92212,
                156.923957,
                157.924101,
                159.927051,
            ],
            "atomic_number": 64,
            "atomic_charge": 3,
            "isotopic_ratio": [
                0.002,
                0.0218,
                0.148,
                0.2047,
                0.1565,
                0.2484,
                0.2186,
            ],
        },
        "Ga": {
            "isotopic_weight": [68.925581, 70.924705],
            "atomic_number": 31,
            "atomic_charge": 3,
            "isotopic_ratio": [0.60108, 0.39892],
        },
        "Pr": {
            "isotopic_weight": [140.907648],
            "atomic_number": 59,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Pt": {
            "isotopic_weight": [
                189.95993,
                191.961035,
                193.962664,
                194.964774,
                195.964935,
                197.967876,
            ],
            "atomic_number": 78,
            "atomic_charge": 4,
            "isotopic_ratio": [
                0.00014,
                0.00782,
                0.32967,
                0.33832,
                0.25242,
                0.07163,
            ],
        },
        "Pu": {
            "isotopic_weight": [244.0],
            "atomic_number": 94,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "C": {
            "isotopic_weight": [12.0, 13.0033548378],
            "atomic_number": 6,
            "atomic_charge": -4,
            "isotopic_ratio": [0.9893, 0.0107],
        },
        "Pb": {
            "isotopic_weight": [
                203.973029,
                205.974449,
                206.975881,
                207.976636,
            ],
            "atomic_number": 82,
            "atomic_charge": 2,
            "isotopic_ratio": [0.014, 0.241, 0.221, 0.524],
        },
        "Pa": {
            "isotopic_weight": [231.03588],
            "atomic_number": 91,
            "atomic_charge": 4,
            "isotopic_ratio": [1.0],
        },
        "Pd": {
            "isotopic_weight": [
                101.905608,
                103.904035,
                104.905084,
                105.903483,
                107.903894,
                109.905152,
            ],
            "atomic_number": 46,
            "atomic_charge": 2,
            "isotopic_ratio": [0.0102, 0.1114, 0.2233, 0.2733, 0.2646, 0.1172],
        },
        "Cd": {
            "isotopic_weight": [
                105.906458,
                107.904183,
                109.903006,
                110.904182,
                111.9027572,
                112.9044009,
                113.9033581,
                115.904755,
            ],
            "atomic_number": 48,
            "atomic_charge": 2,
            "isotopic_ratio": [
                0.0125,
                0.0089,
                0.1249,
                0.128,
                0.2413,
                0.1222,
                0.2873,
                0.0749,
            ],
        },
        "Po": {
            "isotopic_weight": [209.0],
            "atomic_number": 84,
            "atomic_charge": 4,
            "isotopic_ratio": [1.0],
        },
        "Pm": {
            "isotopic_weight": [144.9127],
            "atomic_number": 61,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Ho": {
            "isotopic_weight": [164.930319],
            "atomic_number": 67,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Hf": {
            "isotopic_weight": [
                173.94004,
                175.9414018,
                176.94322,
                177.9436977,
                178.9458151,
                179.9465488,
            ],
            "atomic_number": 72,
            "atomic_charge": 4,
            "isotopic_ratio": [0.0016, 0.0526, 0.186, 0.2728, 0.1362, 0.3508],
        },
        "Hg": {
            "isotopic_weight": [
                195.965815,
                197.966752,
                198.968262,
                199.968309,
                200.970285,
                201.970626,
                203.973476,
            ],
            "atomic_number": 80,
            "atomic_charge": 2,
            "isotopic_ratio": [
                0.0015,
                0.0997,
                0.1687,
                0.231,
                0.1318,
                0.2986,
                0.0687,
            ],
        },
        "He": {
            "isotopic_weight": [3.0160293097, 4.0026032497],
            "atomic_number": 2,
            "atomic_charge": 0,
            "isotopic_ratio": [1.37e-06, 0.99999863],
        },
        "Md": {
            "isotopic_weight": [258.0],
            "atomic_number": 101,
            "atomic_charge": 0,
            "isotopic_ratio": [1.0],
        },
        "Mg": {
            "isotopic_weight": [23.9850419, 24.98583702, 25.98259304],
            "atomic_number": 12,
            "atomic_charge": 2,
            "isotopic_ratio": [0.7899, 0.1, 0.1101],
        },
        "K": {
            "isotopic_weight": [38.9637069, 39.96399867, 40.96182597],
            "atomic_number": 19,
            "atomic_charge": 1,
            "isotopic_ratio": [0.932581, 0.000117, 0.067302],
        },
        "Mn": {
            "isotopic_weight": [54.9380496],
            "atomic_number": 25,
            "atomic_charge": 2,
            "isotopic_ratio": [1.0],
        },
        "O": {
            "isotopic_weight": [15.9949146221, 16.9991315, 17.9991604],
            "atomic_number": 8,
            "atomic_charge": -2,
            "isotopic_ratio": [0.99757, 0.00038, 0.00205],
        },
        "S": {
            "isotopic_weight": [
                31.97207069,
                32.9714585,
                33.96786683,
                35.96708088,
            ],
            "atomic_number": 16,
            "atomic_charge": -2,
            "isotopic_ratio": [0.9493, 0.0076, 0.0429, 0.0002],
        },
        "W": {
            "isotopic_weight": [
                179.946704,
                181.9482042,
                182.950223,
                183.9509312,
                185.9543641,
            ],
            "atomic_number": 74,
            "atomic_charge": 6,
            "isotopic_ratio": [0.0012, 0.265, 0.1431, 0.3064, 0.2843],
        },
        "Zn": {
            "isotopic_weight": [
                63.9291466,
                65.9260368,
                66.9271309,
                67.9248476,
                69.925325,
            ],
            "atomic_number": 30,
            "atomic_charge": 2,
            "isotopic_ratio": [0.4863, 0.279, 0.041, 0.1875, 0.0062],
        },
        "Eu": {
            "isotopic_weight": [150.919846, 152.921226],
            "atomic_number": 63,
            "atomic_charge": 3,
            "isotopic_ratio": [0.4781, 0.5219],
        },
        "Zr": {
            "isotopic_weight": [
                89.9047037,
                90.905645,
                91.9050401,
                93.9063158,
                95.908276,
            ],
            "atomic_number": 40,
            "atomic_charge": 4,
            "isotopic_ratio": [0.5145, 0.1122, 0.1715, 0.1738, 0.028],
        },
        "Er": {
            "isotopic_weight": [
                161.928775,
                163.929197,
                165.93029,
                166.932045,
                167.932368,
                169.93546,
            ],
            "atomic_number": 68,
            "atomic_charge": 3,
            "isotopic_ratio": [0.0014, 0.0161, 0.3361, 0.2293, 0.2678, 0.1493],
        },
        "Ni": {
            "isotopic_weight": [
                57.9353479,
                59.9307906,
                60.9310604,
                61.9283488,
                63.9279696,
            ],
            "atomic_number": 27,
            "atomic_charge": 2,
            "isotopic_ratio": [
                0.680769,
                0.262231,
                0.011399,
                0.036345,
                0.009256,
            ],
        },
        "No": {
            "isotopic_weight": [259.0],
            "atomic_number": 102,
            "atomic_charge": 0,
            "isotopic_ratio": [1.0],
        },
        "Na": {
            "isotopic_weight": [22.98976967],
            "atomic_number": 11,
            "atomic_charge": 1,
            "isotopic_ratio": [1.0],
        },
        "Nb": {
            "isotopic_weight": [92.9063775],
            "atomic_number": 41,
            "atomic_charge": 5,
            "isotopic_ratio": [1.0],
        },
        "Nd": {
            "isotopic_weight": [
                141.907719,
                142.90981,
                143.910083,
                144.912569,
                145.913112,
                147.916889,
                149.920887,
            ],
            "atomic_number": 60,
            "atomic_charge": 3,
            "isotopic_ratio": [
                0.272,
                0.122,
                0.238,
                0.083,
                0.172,
                0.057,
                0.056,
            ],
        },
        "Ne": {
            "isotopic_weight": [19.9924401759, 20.99384674, 21.99138551],
            "atomic_number": 10,
            "atomic_charge": 0,
            "isotopic_ratio": [0.9048, 0.0027, 0.0925],
        },
        "Np": {
            "isotopic_weight": [237.0],
            "atomic_number": 93,
            "atomic_charge": 5,
            "isotopic_ratio": [1.0],
        },
        "Fr": {
            "isotopic_weight": [223.0],
            "atomic_number": 87,
            "atomic_charge": 1,
            "isotopic_ratio": [1.0],
        },
        "Fe": {
            "isotopic_weight": [
                53.9396148,
                55.9349421,
                56.9353987,
                57.9332805,
            ],
            "atomic_number": 26,
            "atomic_charge": 3,
            "isotopic_ratio": [0.05845, 0.91754, 0.02119, 0.00282],
        },
        "Fm": {
            "isotopic_weight": [257.0],
            "atomic_number": 100,
            "atomic_charge": 0,
            "isotopic_ratio": [1.0],
        },
        "B": {
            "isotopic_weight": [10.012937, 11.0093055],
            "atomic_number": 5,
            "atomic_charge": 3,
            "isotopic_ratio": [0.199, 0.801],
        },
        "F": {
            "isotopic_weight": [18.9984032],
            "atomic_number": 9,
            "atomic_charge": -1,
            "isotopic_ratio": [1.0],
        },
        "Sr": {
            "isotopic_weight": [83.913425, 85.9092624, 86.9088793, 87.9056143],
            "atomic_number": 38,
            "atomic_charge": 2,
            "isotopic_ratio": [0.0056, 0.0986, 0.07, 0.8258],
        },
        "N": {
            "isotopic_weight": [14.0030740052, 15.0001088984],
            "atomic_number": 7,
            "atomic_charge": 5,
            "isotopic_ratio": [0.99632, 0.00368],
        },
        "Kr": {
            "isotopic_weight": [
                77.920386,
                79.916378,
                81.9134846,
                82.914136,
                83.911507,
                85.9106103,
            ],
            "atomic_number": 36,
            "atomic_charge": 0,
            "isotopic_ratio": [0.0035, 0.0228, 0.1158, 0.1149, 0.57, 0.173],
        },
        "Si": {
            "isotopic_weight": [27.9769265327, 28.97649472, 29.97377022],
            "atomic_number": 14,
            "atomic_charge": 4,
            "isotopic_ratio": [0.92297, 0.046832, 0.030872],
        },
        "Sn": {
            "isotopic_weight": [
                111.904821,
                113.902782,
                114.903346,
                115.901744,
                116.902954,
                117.901606,
                118.903309,
                119.9021966,
                121.9034401,
                123.9052746,
            ],
            "atomic_number": 50,
            "atomic_charge": 4,
            "isotopic_ratio": [
                0.0097,
                0.0066,
                0.0034,
                0.1454,
                0.0768,
                0.2422,
                0.0859,
                0.3258,
                0.0463,
                0.0579,
            ],
        },
        "Sm": {
            "isotopic_weight": [
                143.911995,
                146.914893,
                147.914818,
                148.91718,
                149.917271,
                151.919728,
                153.922205,
            ],
            "atomic_number": 62,
            "atomic_charge": 3,
            "isotopic_ratio": [
                0.0307,
                0.1499,
                0.1124,
                0.1382,
                0.0738,
                0.2675,
                0.2275,
            ],
        },
        "V": {
            "isotopic_weight": [49.9471628, 50.9439637],
            "atomic_number": 23,
            "atomic_charge": 5,
            "isotopic_ratio": [0.0025, 0.9975],
        },
        "Sc": {
            "isotopic_weight": [44.9559102],
            "atomic_number": 21,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Sb": {
            "isotopic_weight": [120.903818, 122.9042157],
            "atomic_number": 51,
            "atomic_charge": 3,
            "isotopic_ratio": [0.5721, 0.4279],
        },
        "Sg": {
            "isotopic_weight": [266.0],
            "atomic_number": 106,
            "atomic_charge": 0,
            "isotopic_ratio": [1.0],
        },
        "Se": {
            "isotopic_weight": [
                73.9224766,
                75.9192141,
                76.9199146,
                77.9173095,
                79.9165218,
                81.9167,
            ],
            "atomic_number": 34,
            "atomic_charge": 4,
            "isotopic_ratio": [0.0089, 0.0937, 0.0763, 0.2377, 0.4961, 0.0873],
        },
        "Co": {
            "isotopic_weight": [58.933195],
            "atomic_number": 28,
            "atomic_charge": 2,
            "isotopic_ratio": [1.0],
        },
        "Cm": {
            "isotopic_weight": [247.0],
            "atomic_number": 96,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Cl": {
            "isotopic_weight": [34.96885271, 36.9659026],
            "atomic_number": 17,
            "atomic_charge": -1,
            "isotopic_ratio": [0.7578, 0.2422],
        },
        "Ca": {
            "isotopic_weight": [
                39.9625912,
                41.9586183,
                42.9587668,
                43.9554811,
                45.9536928,
                47.952534,
            ],
            "atomic_number": 20,
            "atomic_charge": 2,
            "isotopic_ratio": [
                0.96941,
                0.00647,
                0.00135,
                0.02086,
                4e-05,
                0.00187,
            ],
        },
        "Cf": {
            "isotopic_weight": [251.0],
            "atomic_number": 98,
            "atomic_charge": 0,
            "isotopic_ratio": [1.0],
        },
        "Ce": {
            "isotopic_weight": [135.90714, 137.905986, 139.905434, 141.90924],
            "atomic_number": 58,
            "atomic_charge": 3,
            "isotopic_ratio": [0.00185, 0.00251, 0.8845, 0.11114],
        },
        "Xe": {
            "isotopic_weight": [
                123.9058958,
                125.904269,
                127.9035304,
                128.9047795,
                129.9035079,
                130.9050819,
                131.9041545,
                133.9053945,
                135.90722,
            ],
            "atomic_number": 54,
            "atomic_charge": 0,
            "isotopic_ratio": [
                0.0009,
                0.0009,
                0.0192,
                0.2644,
                0.0408,
                0.2118,
                0.2689,
                0.1044,
                0.0887,
            ],
        },
        "Tm": {
            "isotopic_weight": [168.934211],
            "atomic_number": 69,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Cs": {
            "isotopic_weight": [132.905447],
            "atomic_number": 55,
            "atomic_charge": 1,
            "isotopic_ratio": [1.0],
        },
        "Cr": {
            "isotopic_weight": [
                49.9460496,
                51.9405119,
                52.9406538,
                53.9388849,
            ],
            "atomic_number": 24,
            "atomic_charge": 2,
            "isotopic_ratio": [0.04345, 0.83789, 0.09501, 0.02365],
        },
        "Cu": {
            "isotopic_weight": [62.9296011, 64.9277937],
            "atomic_number": 29,
            "atomic_charge": 2,
            "isotopic_ratio": [0.6917, 0.3083],
        },
        "La": {
            "isotopic_weight": [137.907107, 138.906348],
            "atomic_number": 57,
            "atomic_charge": 3,
            "isotopic_ratio": [0.0009, 0.9991],
        },
        "Li": {
            "isotopic_weight": [6.0151233, 7.016004],
            "atomic_number": 3,
            "atomic_charge": 1,
            "isotopic_ratio": [0.0759, 0.9241],
        },
        "Tl": {
            "isotopic_weight": [202.972329, 204.974412],
            "atomic_number": 81,
            "atomic_charge": 1,
            "isotopic_ratio": [0.29524, 0.70476],
        },
        "Lu": {
            "isotopic_weight": [174.9407679, 175.9426824],
            "atomic_number": 71,
            "atomic_charge": 3,
            "isotopic_ratio": [0.9741, 0.0259],
        },
        "Lr": {
            "isotopic_weight": [262.0],
            "atomic_number": 103,
            "atomic_charge": 0,
            "isotopic_ratio": [1.0],
        },
        "Th": {
            "isotopic_weight": [232.0380504],
            "atomic_number": 90,
            "atomic_charge": 4,
            "isotopic_ratio": [1.0],
        },
        "Ti": {
            "isotopic_weight": [
                45.9526295,
                46.9517638,
                47.9479471,
                48.9478708,
                49.9447921,
            ],
            "atomic_number": 22,
            "atomic_charge": 4,
            "isotopic_ratio": [0.0825, 0.0744, 0.7372, 0.0541, 0.0518],
        },
        "Te": {
            "isotopic_weight": [
                119.90402,
                121.9030471,
                122.904273,
                123.9028195,
                124.9044247,
                125.9033055,
                127.9044614,
                129.9062228,
            ],
            "atomic_number": 52,
            "atomic_charge": 4,
            "isotopic_ratio": [
                0.0009,
                0.0255,
                0.0089,
                0.0474,
                0.0707,
                0.1884,
                0.3174,
                0.3408,
            ],
        },
        "Tb": {
            "isotopic_weight": [158.925343],
            "atomic_number": 65,
            "atomic_charge": 4,
            "isotopic_ratio": [1.0],
        },
        "Tc": {
            "isotopic_weight": [96.906365, 97.907216, 98.9062546],
            "atomic_number": 43,
            "atomic_charge": 2,
            "isotopic_ratio": [1.0],
        },
        "Ta": {
            "isotopic_weight": [179.947466, 180.947996],
            "atomic_number": 73,
            "atomic_charge": 5,
            "isotopic_ratio": [0.00012, 0.99988],
        },
        "Yb": {
            "isotopic_weight": [
                167.933894,
                169.934759,
                170.936322,
                171.9363777,
                172.9382068,
                173.9388581,
                175.942568,
            ],
            "atomic_number": 70,
            "atomic_charge": 3,
            "isotopic_ratio": [
                0.0013,
                0.0304,
                0.1428,
                0.2183,
                0.1613,
                0.3183,
                0.1276,
            ],
        },
        "Db": {
            "isotopic_weight": [262.0],
            "atomic_number": 105,
            "atomic_charge": 0,
            "isotopic_ratio": [1.0],
        },
        "Dy": {
            "isotopic_weight": [
                155.924278,
                157.924405,
                159.925194,
                160.92693,
                161.926795,
                162.928728,
                163.929171,
            ],
            "atomic_number": 66,
            "atomic_charge": 3,
            "isotopic_ratio": [
                0.0006,
                0.001,
                0.0234,
                0.1891,
                0.2551,
                0.249,
                0.2818,
            ],
        },
        "At": {
            "isotopic_weight": [210.0],
            "atomic_number": 85,
            "atomic_charge": 7,
            "isotopic_ratio": [1.0],
        },
        "I": {
            "isotopic_weight": [126.904468],
            "atomic_number": 53,
            "atomic_charge": -1,
            "isotopic_ratio": [1.0],
        },
        "U": {
            "isotopic_weight": [
                234.0409456,
                235.0439231,
                236.0455619,
                238.0507826,
            ],
            "atomic_number": 92,
            "atomic_charge": 6,
            "isotopic_ratio": [5.5e-05, 0.0072, 0.0, 0.992745],
        },
        "Y": {
            "isotopic_weight": [88.9058479],
            "atomic_number": 39,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Ac": {
            "isotopic_weight": [227.0],
            "atomic_number": 89,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Ag": {
            "isotopic_weight": [106.905093, 108.904756],
            "atomic_number": 47,
            "atomic_charge": 1,
            "isotopic_ratio": [0.51839, 0.48161],
        },
        "Ir": {
            "isotopic_weight": [190.960591, 192.962924],
            "atomic_number": 77,
            "atomic_charge": 4,
            "isotopic_ratio": [0.373, 0.627],
        },
        "Am": {
            "isotopic_weight": [243.0],
            "atomic_number": 95,
            "atomic_charge": 2,
            "isotopic_ratio": [1.0],
        },
        "Al": {
            "isotopic_weight": [26.98153844],
            "atomic_number": 13,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "As": {
            "isotopic_weight": [74.9215964],
            "atomic_number": 33,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Ar": {
            "isotopic_weight": [35.96754628, 37.9627322, 39.962383123],
            "atomic_number": 18,
            "atomic_charge": 0,
            "isotopic_ratio": [0.003365, 0.000632, 0.996003],
        },
        "Au": {
            "isotopic_weight": [196.966552],
            "atomic_number": 79,
            "atomic_charge": 3,
            "isotopic_ratio": [1.0],
        },
        "Es": {
            "isotopic_weight": [252, 0.0],
            "atomic_number": 99,
            "atomic_charge": 0,
            "isotopic_ratio": [1.0],
        },
        "In": {
            "isotopic_weight": [112.904061, 114.903878],
            "atomic_number": 49,
            "atomic_charge": 3,
            "isotopic_ratio": [0.0429, 0.9571],
        },
        "Mo": {
            "isotopic_weight": [
                91.90681,
                93.9050876,
                94.9058415,
                95.9046789,
                96.906021,
                97.9054078,
                99.907477,
            ],
            "atomic_number": 42,
            "atomic_charge": 6,
            "isotopic_ratio": [
                0.1484,
                0.0925,
                0.1592,
                0.1668,
                0.0955,
                0.2413,
                0.0963,
            ],
        },
    }
