import sys
from logging import INFO, basicConfig, getLogger
from traceback import format_exc

from rich.console import Console
from rich.logging import RichHandler

from .fetch import (
    get_contract_create_events,
    get_data_from_events,
    get_latest_valid_block,
    get_vaults,
)
from .write import get_saved_state, write_to_markdown, write_to_state

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

if __name__ == "__main__":
    try:
        end_block = get_latest_valid_block()
        current_saved_state = get_saved_state()
        runs = current_saved_state["runs"]
        if len(runs) > 0:
            # Use latest block in state + 1 as start block
            start_block = int(max(runs.keys(), key=int)) + 1
        else:
            # Only for initialization—360 hours before end block as start block
            start_block = 1224694

        events = get_contract_create_events(start_block, end_block)
        data = get_data_from_events(events)
        # Remove duplicates
        owners = {data["owner"] for data in data}
        vaults = []
        for owner in owners:
            vault = get_vaults(owner)
            vaults.append({owner: vault})
        snapshot = {
            "start_block": start_block,
            "end_block": end_block,
            "events_data": data,
        }
        new_run = {end_block: snapshot}

        write_to_state(new_run, vaults)
        updated_state = get_saved_state()
        write_to_markdown(updated_state, end_block)

    except Exception as e:
        log.error(f"Error in program: {e}")
        log.error(format_exc())
        sys.exit(1)
