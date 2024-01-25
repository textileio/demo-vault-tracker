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
    """
    Get all vault creators and write results to a markdown file weekly.
    - Get the latest valid block and the current saved state's previous end block.
    - Get all vault creators from the Basin contract's `PubCreated` event.
    - Get all vaults for each vault creator via Basin API.
    - Write each new run and cumulative vaults to a state file.
    - Write the cumulative vaults to a markdown file.
    """
    try:
        end_block = get_latest_valid_block()
        current_saved_state = get_saved_state()
        runs = current_saved_state["runs"]
        if len(runs) > 0:
            # Use latest block in state + 1 as start block
            start_block = int(max(runs.keys(), key=int)) + 1
        else:
            # Initial run; first Basin contract call was at block 1076346
            start_block = 1076346

        # Get the vault creators from the Basin contract's `PubCreated` event
        create_events = get_contract_create_events(start_block, end_block)
        # Get data from the logs, including vault creator, vault hash, & block
        data = get_data_from_events(create_events)
        # Remove duplicate vault creators/owners
        owners = {data["owner"] for data in data}
        # Get all vaults for each vault creator via Basin API
        vaults = []
        for owner in owners:
            vault = get_vaults(owner)
            vaults.append({owner: vault})
        # Store the current snapshot/run
        snapshot = {
            "start_block": start_block,
            "end_block": end_block,
            "events_data": data,
        }
        # Index the run by the `end_block` number
        new_run = {end_block: snapshot}

        # Write the new run and cumulative vaults files
        write_to_state(new_run, vaults)
        updated_state = get_saved_state()
        write_to_markdown(updated_state, end_block)

    except Exception as e:
        log.error(f"Error executing: {e}")
        log.error(format_exc())
        sys.exit(1)
