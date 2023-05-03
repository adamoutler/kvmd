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


import operator
import functools
import multiprocessing.queues
import queue
import shlex

from typing import Hashable
from typing import TypeVar


# =====
def remap(value: int, in_min: int, in_max: int, out_min: int, out_max: int) -> int:
    return int((value - in_min) * (out_max - out_min) // (in_max - in_min) + out_min)


# =====
def cmdfmt(cmd: list[str]) -> str:
    return " ".join(map(shlex.quote, cmd))


def efmt(err: Exception) -> str:
    return f"{type(err).__name__}: {err}"


def deep_merge(dest: dict, src: dict) -> None:
    """
    Merges source dictionary into destination dictionary recursively.

    Args:
        dest (dict): Destination dictionary to merge into.
        src (dict): Source dictionary to merge.

    Returns:
        None
    """
    def merge_lists(dest: list, src: list) -> list:
        result = dest.copy()
        for item in src:
            if isinstance(item, list):
                if item not in result:
                    result.append(item)
            elif isinstance(item, dict):
                for dest_item in result:
                    if isinstance(dest_item, dict) and set(dest_item.keys()) == set(item.keys()):
                        deep_merge(dest_item, item)
                        break
                else:
                    result.append(item)
            elif item not in result:
                result.append(item)
        return result

    for key, value in src.items():
        if key in dest and value is not None and dest[key] is not None:
            if isinstance(dest[key], dict) and isinstance(value, dict):
                deep_merge(dest[key], value)
            elif isinstance(dest[key], list) and isinstance(value, list):
                dest[key] = merge_lists(dest[key], value)
        else:
            dest[key] = value

    def merge_lists(dest: list, src: list) -> list:
        result = dest.copy()
        for item in src:
            if item not in result:
                result.append(item)
        return result


def append(dest: dict, src: dict) -> None:
    """
    Appends new keys to the destination dictionary from the source dictionary.

    Args:
        dest: The destination dictionary to append to.
        src: The source dictionary to append from.

    Note:
        This method only appends new keys to the destination dictionary. If a key already exists in the destination
        dictionary, the corresponding value from the source dictionary will not be appended.

    Example:
        >>> dest = {'a': 1, 'b': 2}
        >>> src = {'b': 3, 'c': 4}
        >>> append(dest, src)
        >>> print(dest)
        {'a': 1, 'b': 2, 'c': 4}
    """
    for key, value in src.items():
        if key not in dest:
            dest[key] = value


def rget(dct: dict, *keys: Hashable) -> dict:
    result = functools.reduce((lambda nxt, key: nxt.get(key, {})), keys, dct)
    if not isinstance(result, dict):
        raise TypeError(f"Not a dict as result: {result!r} from {dct!r} at {list(keys)}")
    return result


_DictKeyT = TypeVar("_DictKeyT")
_DictValueT = TypeVar("_DictValueT")


def sorted_kvs(dct: dict[_DictKeyT, _DictValueT]) -> list[tuple[_DictKeyT, _DictValueT]]:
    return sorted(dct.items(), key=operator.itemgetter(0))


def swapped_kvs(dct: dict[_DictKeyT, _DictValueT]) -> dict[_DictValueT, _DictKeyT]:
    return {value: key for (key, value) in dct.items()}


# =====
def clear_queue(q: multiprocessing.queues.Queue) -> None:  # pylint: disable=invalid-name
    for _ in range(q.qsize()):
        try:
            q.get_nowait()
        except queue.Empty:
            break


# =====
def build_cmd(cmd: list[str], cmd_remove: list[str], cmd_append: list[str]) -> list[str]:
    assert len(cmd) >= 1, cmd
    return [
        cmd[0],  # Executable
        *filter((lambda item: item not in cmd_remove), cmd[1:]),
        *cmd_append,
    ]
