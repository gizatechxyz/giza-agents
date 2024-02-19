from rich.console import Console
from rich.table import Table

from giza_datasets.constants import DATASET_HUB


class DatasetsHub:
    """
    Class to manage datasets from the DATASET_HUB.

    Attributes:
        datasets (list): A list of Dataset objects from the DATASET_HUB.

    Methods:
        show(): Prints a table of all datasets in the hub.
        list(): Returns a list of all datasets in the hub.
        get(dataset_name): Returns a Dataset object with the given name.
        describe(dataset_name): Prints a table of details for the given dataset.
    """

    def __init__(self):
        """
        Initializes the DatasetsHub with the datasets from the DATASET_HUB.
        """
        self.datasets = DATASET_HUB

    def show(self):
        """
        Prints a table of all datasets in the hub.
        """
        table = Table(title="Datasets", show_lines=True)

        table.add_column("Dataset Name", justify="left")

        for dataset in self.datasets:
            table.add_row(dataset.name)

        console = Console()
        console.print(table)

    def list(self):
        """
        Returns a list of all datasets in the hub.
        """
        return self.datasets

    def list_tags(self):
        """
        Returns a list of all tags in the hub.
        """
        all_tags = set()  # Using a set to automatically remove duplicates

        for dataset in self.datasets:
            all_tags.update(dataset.tags)

        return list(all_tags)

    def get(self, dataset_name):
        """
        Returns a Dataset object with the given name.

        Args:
            dataset_name (str): The name of the dataset to return.

        Raises:
            ValueError: If no dataset with the given name is found.
        """
        dataset = next((d for d in self.datasets if d.name == dataset_name), None)
        if dataset is None:
            raise ValueError(f"Dataset name '{dataset_name}' not found.")

        return dataset

    def get_by_tag(self, dataset_tag):
        """
        Returns a list of Dataset objects with the given tag.

        Args:
            dataset_name (str): Tag to query the datasets.

        Raises:
            ValueError: If no dataset with the given tag is found.
        """
        datasets = [d for d in self.datasets if dataset_tag in d.tags]
        if datasets is None:
            raise ValueError(f"Dataset with the tag '{dataset_tag}' not found.")

        return datasets

    def describe(self, dataset_name):
        """
        Prints a table of details for the given dataset.

        Args:
            dataset_name (str): The name of the dataset to describe.
        """
        dataset = self.get(dataset_name)

        table = Table(title=f"Details for {dataset_name}", show_lines=True)

        table.add_column("Attribute", justify="left")
        table.add_column("Value", justify="left")

        table.add_row("Path", dataset.path)
        table.add_row("Description", dataset.description)
        rendered_string = ", ".join(str(item) for item in dataset.tags)
        table.add_row("Tags", rendered_string)
        table.add_row("Documentation", dataset.documentation)

        console = Console()
        console.print(table)
