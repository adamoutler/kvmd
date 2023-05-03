# ========================================================================== #
#                                                                            #
#    KVMD - The main PiKVM daemon.                                           #
#                                                                            #
#    Copyright (C) 2018-2022  Maxim Devaev <mdevaev@gmail.com>               #
#                                                                            #
#    This program is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by    #
#    the Free Software Foundation, either version 3 of the License, or       #
#    (at your option) any later version.                                     #
#                                                                            #
#    This program is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#    GNU General Public License for more details.                            #
#                                                                            #
#    You should have received a copy of the GNU General Public License       #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.  #
#                                                                            #
# ========================================================================== #

from enum import Enum
from typing import Union


STRATEGY_KEY = "Merge Strategy"


class MergeStrategy(Enum):
    """ Each MergeStrategy is used to determine how to merge dictionaries and lists. Also provides upper/lower/space insensitive aliases."""
    MERGE = ["merge"]
    """Merge Strategy is similar to a recursive override of all dictionaries. This is the default strategy."""
    DEEP_MERGE = ["deep_merge", "deep merge", "deepmerge"]
    """Deep Merge Strategy will merge dictionaries and will append lists."""
    APPEND = ["append"]
    """Appends new values to dictionaries, adds new values to lists, but ignores existing non-dictionary keys."""

    @staticmethod
    def strategy_from_name(strategy_name: str) -> 'MergeStrategy':
        for strategy in MergeStrategy:
            if strategy_name.lower() in strategy.value:
                return strategy
        raise ValueError(f"Invalid merge strategy: {strategy_name}")

    @staticmethod
    def get_strategy(src: dict, current_strategy: 'MergeStrategy') -> 'MergeStrategy':
        """Returns the merge strategy defined in the source dictionary or the current strategy."""
        strategy_name = src.pop(STRATEGY_KEY, None)
        return MergeStrategy.strategy_from_name(strategy_name) if strategy_name else current_strategy

    def merge(self, src: Union[dict, list], dest: Union[dict, list], file: str) -> None:
        """ Merges the source dictionary or list into the destination dictionary or list. """
        if isinstance(src, list):
            self.list_handling(src, dest, file)
        else:
            self.dict_handling(src, dest, file)

    def dict_handling(self, src: dict, dest: dict, file: str) -> None:
        """ Merges the source dictionary into the destination dictionary. """
        # strategy = MergeStrategy.get_strategy(src, strategy) # allow redefine strategy from any dictionary
        if not isinstance(dest, dict):
            dest = {}

        for key, value in src.items():
            match self:
                case MergeStrategy.DEEP_MERGE:
                    if isinstance(value, dict):  # dict inside dict
                        dest[key] = dest.get(key, {})
                        self.dict_handling(value, dest[key], file)
                    elif isinstance(value, list):  # list inside dict
                        dest[key] = dest.get(key, [])
                        self.list_handling(value, dest[key], file)
                    else:
                        dest[key] = value
                case _:
                    if isinstance(value, dict):  # dict inside dict
                        if key not in dest:
                            dest[key] = value
                        self.merge(value, dest.get(key, {}), file)
                    elif isinstance(value, list):  # list inside dict
                        self.list_handling(value, dest[key], file)
                    elif self != MergeStrategy.APPEND or (self == MergeStrategy.APPEND and key not in dest):
                        dest[key] = value

        # if isinstance(dest, dict) and bool(dest):  # TODO: This may need special handling due to the way drivers are loaded.
        #     dest["_source_reference"] = file

    def list_handling(self, src: list, dest: list, file: str) -> None:
        """ Merges the source list into the destination list. """
        match self:
            case MergeStrategy.DEEP_MERGE:
                self.deep_merge_list_handling(src, dest, file)
            case MergeStrategy.APPEND:
                dest.extend(item for item in src if item not in dest)
            case _:
                dest = src

    def deep_merge_list_handling(self, src: list, dest: list, file: str) -> None:
        """ Handles list merging for the deep_merge strategy. """
        dest_dict = {tuple(existing_item.keys()): index for index, existing_item in enumerate(dest) if isinstance(existing_item, dict)}
        for item in src:
            if isinstance(item, dict):  # dict inside list
                matching_keys = tuple(item.keys())
                matching_index = dest_dict.get(matching_keys)
                if matching_index is None:
                    dest.append(item)
                    matching_index = len(dest) - 1
                self.dict_handling(item, dest[matching_index], file)
            elif isinstance(item, list):  # list inside list
                new_list = []
                self.list_handling(item, new_list, file)
                dest.append(new_list)
            elif item not in dest:
                dest.append(item)

# =====


def yaml_merge(dest: dict, src: dict, source: str="", strategy: MergeStrategy = MergeStrategy.MERGE) -> None:
    """ Merges the source dictionary into the destination dictionary. """
    strategy = MergeStrategy.get_strategy(src, strategy)
    strategy.merge(src, dest, source)
