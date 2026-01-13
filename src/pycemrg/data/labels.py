# src/pycemrg/data/labels.py

import yaml
import itertools
from pathlib import Path
from typing import Union, List, Set, Dict


class LabelManager:
    """
    Manages anatomical label definitions from a YAML configuration file.

    This class reads a label manifest and provides utilities to translate
    between human-readable names, groups, and their integer values.
    """

    def __init__(self, config_path: Union[str, Path]):
        """
        Initializes the LabelManager by loading the configuration file.

        Args:
            config_path (Union[str, Path]): Path to the labels YAML file.
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(
                f"Label configuration file not found at: {config_file}"
            )

        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        self._labels = config.get("labels", {})
        self._groups = config.get("groups", {})

        self._value_to_name = {v: k for k, v in self._labels.items()}

    def get_value(self, name: str) -> int:
        """Translates a single label name (e.g., 'LV_myo') to its integer value."""
        if name not in self._labels:
            raise KeyError(f"Label name '{name}' not found.")
        return self._labels[name]

    def get_name(self, value: int) -> str:
        """Translates an integer value (e.g., 1) to its human-readable name."""
        if value not in self._value_to_name:
            raise KeyError(f"Label value '{value}' not found.")
        return self._value_to_name[value]

    def get_values_from_names(self, names: List[str]) -> List[int]:
        """
        Translates a list of strings into a sorted, unique list of integer label values.
        """
        final_values: Set[int] = set()
        for name in names:
            if name.isdigit():
                final_values.add(int(name))
            elif name in self._labels:
                final_values.add(self._labels[name])
            elif name in self._groups:
                group_names = self._groups[name]
                group_values = self.get_values_from_names(group_names)
                final_values.update(group_values)
            else:
                available_keys = list(self._labels.keys()) + list(self._groups.keys())
                raise KeyError(
                    f"Label or group name '{name}' not found. "
                    f"Available keys are: {available_keys}"
                )

        return sorted(list(final_values))

    def get_tags_string(self, names: List[str], separator: str = ",") -> str:
        if any(isinstance(i, list) for i in names):
            flat_names = list(itertools.chain.from_iterable(names))
        else:
            flat_names = names

        list_of_values = self.get_values_from_names(flat_names)
        return separator.join(map(str, list_of_values))


class LabelMapper:
    """
    Creates a mapping between two different label standards.

    This class uses composition, taking two configured LabelManager instances—one
    for a "source" standard and one for a "target" standard—and provides
    methods to translate between them based on common anatomical names.
    """

    def __init__(self, source: LabelManager, target: LabelManager):
        """
        Initializes the LabelMapper.

        Args:
            source: A LabelManager instance configured with the source labels.
            target: A LabelManager instance configured with the target labels.
        """
        self.source = source
        self.target = target

    def get_source_to_target_mapping(self) -> Dict[int, int]:
        """
        Generates a dictionary mapping source integer tags to target integer tags.

        It iterates through the anatomical names defined in the source manager,
        finds the corresponding name in the target manager, and creates a
        mapping from the source value to the target value.

        Returns:
            A dictionary of {source_tag: target_tag}.
        """
        mapping = {}
        # We iterate through the source labels' items (name: value)
        for name, source_value in self.source._labels.items():
            try:
                # Find the same name in the target manager
                target_value = self.target.get_value(name)
                if source_value != target_value:
                    mapping[source_value] = target_value
            except KeyError:
                # This name exists in source but not target; ignore it.
                pass
        return mapping

    def get_source_tags(self, names: List[str]) -> List[int]:
        """
        Convenience method to resolve names/groups using the source standard.
        Equivalent to calling `source_manager.get_values_from_names()`.
        """
        return self.source.get_values_from_names(names)

    def get_target_tags(self, names: List[str]) -> List[int]:
        """
        Convenience method to resolve names/groups using the target standard.
        Equivalent to calling `target_manager.get_values_from_names()`.
        """
        return self.target.get_values_from_names(names)