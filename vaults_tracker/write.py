"""Write the state of all runs and vaults to a state & markdown file."""
from collections import OrderedDict
from datetime import datetime
from json import dump, load
from logging import INFO, basicConfig, getLogger
from pathlib import Path
from traceback import format_exc
from typing import Any, Dict, List

from rich.console import Console
from rich.logging import RichHandler

from .fetch import get_block_timestamp

# Set up pretty logging
FORMAT = "%(message)s"
console = Console()
basicConfig(
    level=INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(show_path=False, console=console)],
)
log = getLogger("rich")


def get_saved_state() -> Dict[Any, Any]:
    """
    Get the state of all runs and vaults from a file.

    Returns
    -------
    dict
        The state.

    Raises
    ------
    Exception
        If there is an error getting the state.
    """
    try:
        state_file = Path(__file__).parent.parent / "state.json"
        with open(state_file, "r") as f:
            state = load(f)
        return state
    except Exception as e:
        log.exception(f"Error getting state: {e}")
        log.error(format_exc())
        raise


def write_to_state(
    new_run: Dict[int, Dict[str, Any] | dict[str, Any]], vaults: List
) -> None:
    """
    Write the runs and vaults state to a file.

    Parameters
    ----------
    new_run : dict
        The new run to write.
    vaults : list
        The vaults to write.

    Returns
    -------
    None

    Raises
    ------
    Exception
        If there is an error writing to the state.
    """
    try:
        state_file = Path(__file__).parent.parent / "state.json"
        with open(state_file, "r") as f:
            state = load(f)

        # Update current state with new run and all vaults
        state["vaults"] = merge_vaults(state["vaults"], vaults)
        state["runs"].update(new_run)

        with open(state_file, "w") as f:
            dump(state, f, indent=4)

    except Exception as e:
        log.error(f"Error writing to state: {e}")
        log.error(format_exc())


def merge_vaults(
    state_vaults: List[Dict[str, List]], new_vaults: List[Dict[str, List]]
) -> List[Dict[str, List]]:
    """
    Merge 'new_vaults' data from all entries in the state_vaults.

    Parameters
    ----------
    state_vaults : list
        The state vaults to merge.

    new_vaults : list
        The new vaults to merge.

    Returns
    -------
    list
        The merged vaults.

    Raises
    ------
    Exception
        If there is an error merging the vaults.
    """
    # Convert lists of dictionaries to OrderedDicts
    dict1 = OrderedDict((k, v) for d in state_vaults for k, v in d.items())
    dict2 = OrderedDict((k, v) for d in new_vaults for k, v in d.items())

    # Merge the OrderedDicts
    merged_dict = OrderedDict(dict1)
    for key, values in dict2.items():
        if key in merged_dict:
            # Extend existing key with new values, avoiding duplicates and maintaining order
            merged_dict[key].extend(v for v in values if v not in merged_dict[key])
        else:
            # Add new key and values
            merged_dict[key] = values

    # Convert merged OrderedDict back to list of dictionaries
    merged_list = [{k: v} for k, v in merged_dict.items()]
    return merged_list


def write_to_markdown(state: dict, end_block: int) -> None:
    """
    Write the state of all vaults to a markdown file.

    Parameters
    ----------
    state : dict
        The state to write.
    end_block : int
        The end block of the run.

    Returns
    -------
    None

    Raises
    ------
    Exception
        If there is an error writing to markdown.
    """
    try:
        markdown_file = Path(__file__).parent.parent / "Data.md"
        with open(markdown_file, "w") as f:
            f.write("# Basin Vaults Tracker\n\n")
            # Document the timestamp of the latest block used
            run_timestamp = get_block_timestamp(end_block)
            run_date = datetime.fromtimestamp(run_timestamp)
            formatted_run_date = run_date.strftime("%Y-%m-%d")
            f.write(f"Last updated: {formatted_run_date}\n\n")
            # Show each vault owner, their vaults, & links to events API
            f.write("## Vaults by owner\n\n")
            for vault in state["vaults"]:
                for owner, vaults in vault.items():
                    f.write(
                        f"### [{owner}](https://basin.tableland.xyz/vaults?account={owner})\n\n"
                    )
                    f.write("| Vault | Events |\n")
                    f.write("| --- | --- |\n")
                    for vault in vaults:
                        events_url = (
                            f"https://basin.tableland.xyz/vaults/{vault}/events"
                        )
                        f.write(f"| {vault} | [Events]({events_url}) |\n")
                    f.write("\n")
    except Exception as e:
        log.exception(f"Error writing to markdown: {e}")
        log.error(format_exc())
        raise
