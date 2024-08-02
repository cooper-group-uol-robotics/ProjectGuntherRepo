"""
Driver for a Bruker Fourier 80 benchtop NMR.

Requires the official TopSpin API (TopSpin >= 4.3).

"""

from os import PathLike
from pathlib import Path
from shutil import (
    copyfile,
    rmtree,
)
from time import (
    sleep,
    time,
)
from typing import (
    Optional,
    Union,
)
from warnings import warn

from bruker.api.topspin import Topspin
from bruker.model.nmr_model import ApiException

from dependencies.modules.fourier_nmr_driver.constants.constants import (
    PARAMS,
    SOLVENTS,
)


class NMRExperiment:
    """NMR experiment and associated data."""

    def __init__(
        self,
        top: Topspin,
        path: PathLike,
    ):
        """Initalise NMRExperiment."""
        self.top = top
        self.data_provider = self.top.getDataProvider()
        self.path = Path(path).resolve()
        self.nmr_data = self.data_provider.getNMRData(str(self.path))
        self.display = self.top.getDisplay()
        self.display.show(dataset=self.nmr_data, newWindow=False)

    def _get_parameter(self, parameter, status=False):
        """Get acquisition or processing parameter value."""
        if status:
            return self.nmr_data.getPar(f"status {parameter.upper()}")
        else:
            return self.nmr_data.getPar(f"{parameter.upper()}")

    @property
    def name(self):
        """Experiment name."""
        return self.path.parents[2].name

    @name.setter
    def name(
        self,
        value: str,
    ) -> None:
        (self.path.parents[2]).rename((self.path.parents[2]).with_name(value))
        self.path = (
            self.path.parents[3]
            / value
            / self.path.parents[1].name
            / self.path.parent.name
            / self.path.name
        )
        self.nmr_data = self.data_provider.getNMRData(str(self.path))

    def get_spectral_width(
        self,
        status: bool = False,
    ) -> float:
        """
        Get spectral width (in ppm).

        Allows to extract the "status" spectral width too.

        """
        return float(self._get_parameter("SW", status=status))

    @property
    def spectral_width(self) -> float:
        """Spectral width (in ppm)."""
        return self.get_spectral_width()

    @spectral_width.setter
    def spectral_width(
        self,
        value: float,
    ) -> None:
        self.nmr_data.launch(f"sw {value}")

    def get_number_scans(
        self,
        status: bool = False,
    ) -> int:
        """
        Get number of scans.

        Allows to extract the "status" number of scans too.

        """
        return int(self._get_parameter("NS", status=status))

    @property
    def number_scans(self) -> int:
        """Number of scans."""
        return self.get_number_scans()

    @number_scans.setter
    def number_scans(
        self,
        value: int,
    ) -> None:
        self.nmr_data.launch(f"ns {value}")

    def get_offset(
        self,
        status: bool = False,
    ) -> float:
        """
        Get offset for the main nucleus (ppm).

        Allows to extract the "status" offset too.

        """
        return float(self._get_parameter("O1P", status=status))

    @property
    def offset(self) -> float:
        """Offset for the main nucleus (ppm)."""
        return self.get_offset()

    @offset.setter
    def offset(self, value: float) -> None:
        self.nmr_data.launch(f"o1p {value}")

    @property
    def title(self) -> str:
        """Title of the NMR experiment."""
        return (self.path / "title").read_text()

    @title.setter
    def title(
        self,
        value: str,
    ) -> None:
        (self.path / "title").write_text(value)

    def get_parameters(
        self,
        status: bool = False,
    ) -> str:
        """
        Get the experiment parameters set.

        Allows to extract the "status" parameters set too.

        """
        return self._get_parameter("EXP", status=status)

    @property
    def parameters(self) -> str:
        """Acquisition parameters set."""
        return self.get_parameters()

    @parameters.setter
    def parameters(
        self,
        value: str,
    ) -> None:
        if value not in PARAMS:
            warn(
                message=(
                    "Requested parameters set is not in the valid parameters "
                    "list. It might have caused a TopSpin error if not "
                    "present in the TopSpin's user parameters list."
                ),
                category=TopSpinWarning,
            )
        self.nmr_data.launch("rpar " + value + " all")

    def get_solvent(
        self,
        status: bool = False,
    ) -> str:
        """
        Get sample solvent.

        Allows to extract the "status" solvent too.

        """
        return self._get_parameter("SOLVENT", status=status)

    @property
    def solvent(self) -> str:
        """Sample solvent."""
        return self.get_solvent()

    @solvent.setter
    def solvent(self, value: str) -> None:
        if value.upper() not in SOLVENTS:
            warn(
                message=(
                    "Requested solvent is not in the valid solvents list. "
                    "It might have caused a TopSpin error if not present "
                    "in the edlock table."
                ),
                category=TopSpinWarning,
            )
        self.nmr_data.launch(f"solvent {value}")

    def process(self):
        """
        Process the NMR spectrum in a very basic way.

        Simple forward Fourier transform, automatic phase correction and
        automatic baseline correction, using TopSpin ML algorithms.

        """
        self.display.show(dataset=self.nmr_data, newWindow=False)
        self.nmr_data.launch("efp", wait=True)
        self.nmr_data.launch("apbk -n", wait=True)
        self.nmr_data.launch("sigreg", wait=True)


class Fourier80:
    """
    Bruker Fourier80 NMR.

    Based on the the original operation manual.

    Attributes
    ----------
    top : bruker.api.topspin.Topspin
        The main Topspin API instance.

    url : Optional[str]
        The network address and port to the Topspin REST interface.
        Bruker's default is localhost:3081.

    data_provider : bruker.api.topspin.DataProvider
        The main data handler within the Topspin API.

    """

    def __init__(
        self,
        address: Optional[str] = None,
        port: Optional[Union[str, int]] = None,
    ):
        """
        Initialise the spectrometer.

        Parameters
        ----------
        address : Optional[str]
            Network address to the spectrometer, typically localhost.

        port : Optional[str | int]
            Connection port to the REST interface. Bruker's default is 3081.

        """
        if address is not None:
            self.url = f"{address}:{port}"
            self.top = Topspin(url=self.url)

        else:
            self.url = "localhost:3081"
            self.top = Topspin()

        try:
            self.top.getVersion()

        except ApiException:
            raise ConnectionError("Cannot connect to TopSpin.")

        self.display = self.top.getDisplay()
        self.display.closeAllWindows()
        self.data_provider = self.top.getDataProvider()
        self._busy = False

        # This will in the future allow checks if sample is in the magnet, etc.
        # However, it is not currently implemented by Bruker.

        # self.spectrometer = self.top.getSpectrometerInterface()

    def new_experiment(
        self,
        path: PathLike,
        exp_name: str,
        title: Optional[str] = None,
        exp_num: int = 10,
        proc_num: int = 1,
        parameters: str = "PROTON",
        solvent: str = "CDCl3",
        getprosol: bool = True,
        overwrite: bool = False,
    ) -> NMRExperiment:
        """
        Create new dataset for an experiment.

        Parameters
        ----------
        path : os.PathLike
            A path to the dataset to be created.

        exp_name : str
            A name for the dataset, commonly sample name.

        title : Optional[str]
            A title to be included in the processing directory.

        exp_num : int
            Experiment number.

        proc_num : int
            Processing number.

        parameters : str
            Acquisition parameters set.

        solvent : str
            Solvent name.

        getprosol : bool
            If True, the pulse programme and probe parameters will be set up.

        overwrite : bool
            If True, any existing experiment will be overwritten.

        Returns
        -------
        Path
            A path to the newly created NMR dataset.

        Notes
        -----
        Check `fourier_nmr_driver.constants` for valid solvents and parameters.
        Parameters are crucial for successful acquisition. However, solvent is
        mostly irrelevant on Fourier80 as it has an internal lock sample. The
        choice of solvent might influence the sample susceptibility settings
        and is useful for future spectrum referencing.

        """
        path = Path(path).resolve()

        if (path / exp_name / str(exp_num)).exists() and not overwrite:
            raise FileExistsError(f"Experiment {exp_name} already exists.")

        elif (path / exp_name / str(exp_num)).exists() and overwrite:
            rmtree(path / exp_name / str(exp_num))

        nmr_data = self.data_provider.createNMRData(
            path=str(path),
            name=exp_name,
            expno=exp_num,
            procno=proc_num,
            parameter=parameters,
        )
        nmr_path = Path(nmr_data.getIdentifier())
        if solvent.upper() not in SOLVENTS:
            warn(
                message=(
                    "Requested solvent is not in the valid solvents list. "
                    "It might have caused a TopSpin error if not present "
                    "in the edlock table."
                ),
                category=TopSpinWarning,
            )
        nmr_data.launch(f"solvent {solvent}", wait=True)

        if getprosol:
            nmr_data.launch("getprosol", wait=True)

        if title is not None:
            (nmr_path / "title").write_text(title)

        return NMRExperiment(self.top, nmr_path)

    def copy_experiment(
        self,
        nmr_experiment: NMRExperiment,
        path: PathLike,
        exp_name: str,
        title: Optional[str] = None,
        exp_num: Optional[int] = None,
        proc_num: int = 1,
        parameters: Optional[str] = None,
        solvent: Optional[str] = None,
        getprosol: bool = False,
        overwrite: bool = False,
    ) -> NMRExperiment:
        """
        Copy parameters of an existing experiment.

        This method copies the parameters and then applies any changes
        requested upon calling (e.g., a new solvent). If data already exists,
        a completely new experiment will be created with the corresponding
        parameters. This is contrary to the default TopSpin behaviour, where
        the parameters are overwritten but the data are kept.

        Parameters
        ----------
        nmr_experiment: NMRExperiment
            The NMR experiment to copy the parameters from.

        path : os.PathLike
            A path to the dataset to be created.

        exp_name : str
            A name for the dataset, commonly sample name.

        title : Optional[str]
            A title to be included in the processing directory.

        exp_num : int
            Experiment number.

        proc_num : int
            Processing number.

        parameters : str
            Acquisition parameters set.

        solvent : str
            Solvent name.

        getprosol : bool
            If True, the pulse programme and probe parameters will be set up.

        overwrite : bool
            If True, any existing experiment will be overwritten.

        Returns
        -------
        Path
            A path to the newly created NMR dataset.

        Notes
        -----
        Check `fourier_nmr_driver.constants` for valid solvents and parameters.
        Parameters are crucial for successful acquisition.

        """
        path = Path(path).resolve()
        old_pdata = nmr_experiment.path
        old_exp = old_pdata.parents[1]

        exp_num = int(old_exp.name) + 1 if exp_num is None else exp_num

        if (path / exp_name / str(exp_num)).exists() and not overwrite:
            raise FileExistsError(f"Experiment {exp_name} already exists.")

        elif (path / exp_name / str(exp_num)).exists() and overwrite:
            rmtree(path / exp_name / str(exp_num))

        new_pdata = path / f"{exp_name}/{exp_num}/pdata/{proc_num}"
        new_exp = new_pdata.parents[1]

        new_pdata.mkdir(exist_ok=True, parents=True)
        copyfile(old_pdata / "outd", new_pdata / "outd")
        copyfile(old_pdata / "proc", new_pdata / "proc")
        copyfile(old_pdata / "procs", new_pdata / "procs")
        copyfile(old_pdata / "title", new_pdata / "title")
        copyfile(old_exp / "acqu", new_exp / "acqu")
        copyfile(old_exp / "acqus", new_exp / "acqus")

        nmr_experiment = NMRExperiment(self.top, new_pdata)

        if title is not None:
            nmr_experiment.title = title
        if parameters is not None:
            nmr_experiment.parameters = parameters
        if solvent is not None:
            nmr_experiment.solvent = solvent
        if getprosol:
            nmr_experiment.nmr_data.launch("getprosol", wait=True)

        return nmr_experiment

    def open_experiment(
        self,
        path: PathLike,
        expno: int = 10,
        procno: int = 1,
    ) -> NMRExperiment:
        """Open an existing NMR experiment.

        The path provided can be either to the processed data file (typically:
        `pdata/1`) or to the actual main dataset folder (i.e., the parent to
        the EXPNO folder). For example, for a dataset:

        `TEST_NMR/10/pdata/1`

        one can pass either that entire path as the main argument, or just
        `TEST_NMR`. Furthermore, if TEST_NMR contains also EXPNO 20, one could
        call using: path = `TEST_NMR/10/pdata/1`, expno = 20.

        Parameters
        ----------
        path : PathLike
            A path to the NMR experiment.
        expno, optional
            Experiment number, by default 10.
        procno, optional
            Processing number, by default 1.

        Returns
        -------
            NMRExperiment, including loading in the TopSpin window.
        """
        path = Path(path)
        if path.parent.name == "pdata":
            pdata_path = path.parents[2] / f"{expno}/pdata/{procno}"
        else:
            pdata_path = path / f"{expno}/pdata/{procno}"
        return NMRExperiment(self.top, pdata_path)

    def change_sample(
        self,
        position: int,
    ) -> None:
        """
        Change sample in the probe.

        Parameters
        ----------
        position : int
            A rack position of the sample to be inserted.

        """
        if self.is_busy():
            raise RuntimeError("Spectrometer is currently busy.")
        self._busy = True
        self.top.executeCommand(f"sx {position}", wait=True)
        self._busy = False

    def start_acquisition(
        self,
        nmr_experiment: NMRExperiment,
        overwrite: bool = True,
    ) -> None:
        """
        Start NMR data acquisition.

        Parameters
        ----------
        nmr_dataset : Path
            A path to the NMR dataset that contains the acquisition parameters.

        overwrite : bool
            If True, any previously existing data in this experiment will be
            overwritten. Otherwise, new data will be appended.

        """
        if self.is_busy():
            raise RuntimeError("Spectrometer is currently busy.")
        self._busy = True
        self.display.show(dataset=nmr_experiment.nmr_data, newWindow=False)
        nmr_experiment.nmr_data.launch("rga", wait=True)

        if overwrite:
            nmr_experiment.nmr_data.launch("zg", wait=True)

        else:
            nmr_experiment.nmr_data.launch("go", wait=True)

        self._busy = False

    def lock(
        self,
        nmr_experiment: NMRExperiment,
    ) -> None:
        """
        Start locking to the internal sample.

        This is not strictly necessary for Fourier80 as the instrument
        has its internal lock sample and hence is always locked. In practice,
        the only outocme of running this result is ensuring that the solvent is
        set in the acquisition parameters for future reference.

        Parameters
        ----------
        nmr_experiment : NMRExperiment
            NMR experiment with acquisition parameters for the lock solvent.

        """
        self.display.show(dataset=nmr_experiment.nmr_data, newWindow=False)
        nmr_experiment.nmr_data.launch("lock -acqu", wait=True)

    def start_shimming(
        self,
        quick=True,
    ) -> None:
        """
        Start the shimming procedure.

        Fourier80 spectrometer uses a shim sample (by default in position 1)
        and has two built-in shimming algorithms: quickshim and fullshim.
        It is recommended to leave the spectrometer shimming whenever it is
        not in use.

        Parameters
        ----------
        quick : bool
            If True, quickshim is performed. Otherwise, the method calls
            the fullshim algorithm.

        Notes
        -----
        Shimming algoritms on Fourier80 never complete. They need to be
        manually stopped via the API `stop_shimming()` method.

        Current version of TopSpin (4.2.0) often displays some
        temperature instability, which might lead to lost lock but should
        not affect the experiemnt results.

        """
        if self.is_busy():
            raise RuntimeError("Spectrometer is currently busy.")
        self._busy = True

        if quick:
            self.top.executeCommand("quickshim")

        else:
            self.top.executeCommand("fullshim")

    def stop_shimming(
        self,
        save_shims=True,
    ) -> None:
        """
        Stop the shimming procedure.

        Parameters
        ----------
        save_shims : bool
            If True, the current best shims are saved. Otherwise, lost.

        """
        if save_shims:
            self.top.executeCommand("haltshim", wait=True)
            self.last_shim = time()
            sleep(60)
        else:
            self.top.executeCommand("stopshim", wait=True)
            sleep(60)
        self._busy = False

    def is_busy(self) -> bool:
        """Check whether the spectrometer is currently busy."""
        return self._busy

    def is_connected(self) -> bool:
        """Check whether the device is connected by."""
        try:
            self.top.getVersion()
            return True
        except ConnectionError:
            return False

    def halt(self):
        """
        Halt executing current program/action immediately.

        This method stops execution of whatever command in TopSpin and
        saves the partial output.

        """
        self.top.executeCommand("halt", wait=True)
        self._busy = False

    def stop(self):
        """
        Stop executing current program/action immediately.

        This method stops execution of whatever command in TopSpin and
        does NOT save any partial autput.

        """
        self.top.executeCommand("stop", wait=True)
        self._busy = False


class TopSpinWarning(Warning):
    """Custom warnings pertaining to potential TopSpin errors."""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)
