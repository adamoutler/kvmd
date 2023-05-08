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
    DISABLED = ["disabled", "disable"]
    """ Disables the configuration """

    @staticmethod
    def strategy_from_name(strategy_name: str) -> 'MergeStrategy':
        for strategy in MergeStrategy:
            if strategy_name.lower() in strategy.value:
                return strategy
        raise ValueError(f"Invalid merge strategy: {strategy_name}")

    @staticmethod
    def get_strategy(src: dict, current_strategy: 'MergeStrategy') -> 'MergeStrategy':
        """Returns the merge strategy defined in the source dictionary or the current strategy."""
        if isinstance(src, dict):
            strategy_name = src.pop(STRATEGY_KEY, None)
            return MergeStrategy.strategy_from_name(strategy_name) if strategy_name else current_strategy
        return current_strategy

    def merge(self, src: Union[dict, list], dest: Union[dict, list], file: str) -> None:
        """ Merges the source dictionary or list into the destination dictionary or list. """
        for (key, value) in src.items():
            match self:
                case MergeStrategy.DISABLED:
                    continue
                case MergeStrategy.MERGE:
                    self.merge_merge_strategy(key, value, src, dest, file)
                case MergeStrategy.DEEP_MERGE:
                    match value:
                        case dict():
                            dest[key] = dest.get(key, {})
                            self.merge(value, dest[key], file)
                        case list():
                            dest[key] = dest.get(key, [])
                            self.deep_merge_list_handling(value, dest[key], file)
                        case _:
                            dest[key] = value
                case MergeStrategy.APPEND:
                    match value:
                        case dict():
                            self._append_dict_handler(dest, key, value, file)
                        case list():
                            self.list_handling(value, dest[key], file)
                        case _:
                            self._append_value_handler(dest, key, value)

    def deep_merge_list_handling(self, src: list, dest: list, file: str) -> None:
        """ Handles list merging for the deep_merge strategy. """
        for item in src:
            if isinstance(item, dict):  # dict inside list
                matching_keys = tuple(item.keys())
                matching_index = dict.get(matching_keys)
                if matching_index is None:
                    dest.append(item)
                    matching_index = len(dest) - 1
                self.merge(item, dest[matching_index], file)
            elif isinstance(item, list):  # list inside list
                new_list = []
                self.deep_merge_list_handling(item, new_list, file)
                dest.append(new_list)
            elif item not in dest:
                dest.append(item)

    def merge_merge_strategy(self, key, value, src, dest, file):
        if key in dest:
            if isinstance(dest[key], dict) and isinstance(value, dict):
                self.merge(value, dest[key], file)
                return
        dest[key] = src[key]
    
    def _append_dict_handler(self, dest, key, value, file):
        self._append_value_handler(dest, key, value)
        self.merge(value, dest.get(key, {}), file)

    def _append_value_handler(self, dest, key, value):
        if key not in dest:
            dest[key] = value
# =====


def yaml_merge(dest: dict, src: dict, source: str="", strategy: MergeStrategy = MergeStrategy.MERGE) -> None:
    """ Merges the source dictionary into the destination dictionary. """
    strategy = MergeStrategy.get_strategy(src, strategy)
    strategy.merge(src, dest, source)
