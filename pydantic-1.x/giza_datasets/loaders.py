import gcsfs
import polars as pl

from giza_datasets.constants import DATASET_HUB


class DatasetsLoader:
    """
    DatasetsLoader is a class for loading datasets from Google Cloud Storage (GCS).
    It uses the GCSFileSystem for accessing files and Polars for handling data.
    """

    def __init__(self):
        """
        Initializes the DatasetsLoader with a GCS filesystem and the dataset configuration.
        Verification is turned off for the GCS filesystem.
        """
        self.fs = gcsfs.GCSFileSystem(verify=False)
        self.dataset_hub = DATASET_HUB

    def _get_all_parquet_files(self, directory):
        """
        Recursively retrieves all the parquet file paths in the given directory.

        Args:
            directory: The GCS directory to search for parquet files.

        Returns:
            A list of full paths to all the parquet files found.
        """
        all_files = self.fs.ls(directory, detail=True)
        parquet_files = []

        for file_info in all_files:
            if file_info["type"] == "directory":
                parquet_files.extend(self._get_all_parquet_files(file_info["name"]))
            elif file_info["name"].endswith(".parquet"):
                full_path = "gs://" + file_info["name"]
                parquet_files.append(full_path)
        return parquet_files

    def _load_multiple_parquet_files(self, file_paths):
        """
        Loads multiple parquet files into a single Polars DataFrame.

        Args:
            file_paths: A list of file paths to load.

        Returns:
            A concatenated Polars DataFrame containing data from all files.
        """
        dfs = []
        for file_path in file_paths:
            with self.fs.open(file_path) as f:
                df = pl.read_parquet(f, use_pyarrow=True)
            dfs.append(df)
        concatenated_df = pl.concat(dfs, how="diagonal_relaxed")

        return concatenated_df

    def load(self, dataset_name):
        """
        Loads a dataset by name, either as a single file or multiple files.

        Args:
            dataset_name: The name of the dataset to load.

        Returns:
            A Polars DataFrame containing the loaded dataset.

        Raises:
            ValueError: If the dataset name is not found or if no parquet files are found.
        """
        gcs_path = None
        for dataset in self.dataset_hub:
            if dataset.name == dataset_name:
                gcs_path = dataset.path
                break

        if not gcs_path:
            raise ValueError(f"Dataset name '{dataset_name}' not found in Giza.")
        elif gcs_path.endswith(".parquet"):
            with self.fs.open(gcs_path) as f:
                df = pl.read_parquet(f, use_pyarrow=True)
        else:
            parquet_files = self._get_all_parquet_files(gcs_path)
            if not parquet_files:
                raise ValueError(
                    "No .parquet files were found in the directory or subdirectories."
                )
            df = self._load_multiple_parquet_files(parquet_files)
        return df
