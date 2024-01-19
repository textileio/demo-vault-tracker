from json import JSONDecodeError, loads
from logging import INFO, basicConfig, getLogger
from pathlib import Path
from typing import Any, Dict, List

from requests import get
from requests.exceptions import RequestException
from rich.console import Console
from rich.logging import RichHandler
from web3 import Web3
from web3.exceptions import BlockNotFound

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


def get_w3() -> Web3:
    url = "https://api.calibration.node.glif.io/rpc/v1"
    return Web3(Web3.HTTPProvider(url))


def get_contract_create_events(
    start_block: int, end_block: int
) -> List[Dict[str, Any]]:
    """
    Get all vault creators from the Basin API.
    event PubCreated(string indexed pub, address indexed owner);

    Returns
    -------
        List[str]: The list of vault creators.

    Raises
    ------
        Exception: If there is an error getting the vault creators.
    """
    try:
        w3 = get_w3()
        abi_file = Path(__file__).parent / "abi.json"
        with open(abi_file, "r") as basin_abi:
            abi = loads(basin_abi.read())
        new_vault_event = "PubCreated"
        basin_address = Web3.to_checksum_address(
            "0xaB16d51Fa80EaeAF9668CE102a783237A045FC37"
        )
        contract = w3.eth.contract(address=basin_address, abi=abi)

        # First Basin contract call was at block 1076346
        # Node provider can only look back 30 days, though—1224694 is Jan 1,
        # 2024
        events = contract.events[new_vault_event].get_logs(  # type: ignore[attr-defined]
            fromBlock=start_block, toBlock=end_block
        )
        return events

    except ValueError as e:
        if "lookbacks of more than 720h0m0s are disallowed" in str(e):
            log.error("Block range exceeds 30 days")
        log.exception(e)
        raise

    except Exception as e:
        log.error(
            f"Error getting contract create events for range: {start_block}, {end_block}"
        )
        log.exception(e)
        raise


def get_vault_owners(contract_events: List[Dict[str, Any]]) -> List[str]:
    """
    Get all vault owners from the Basin API.

    Returns
    -------
        List[str]: The list of vault owners.

    Raises
    ------
        Exception: If there is an error getting the vault owners.
    """
    try:
        owners = []
        for item in contract_events:
            args = item["args"]
            owner = args["owner"]
            owners.append(owner)

        # Remove duplicates
        owners = list(set(owners))
        return owners

    except Exception as e:
        error_msg = f"Error getting vault owners: {e}"
        log.error(error_msg)
        raise Exception


def get_vaults(address: str) -> List[str]:
    """
    Get all vaults for a namespace creator at `address`. For example, the
    creator of `xm_data.p1` is `0xfc7C55c4A9e30A4e23f0e48bd5C1e4a865dA06C5`.

    Parameters
    ----------
        address (str): The address of the namespace creator.

    Returns
    -------
        List[str]: The list of vaults for the namespace.

    Raises
    ------
        Exception: If there is an error getting the vaults.
    """
    try:
        url = "https://basin.tableland.xyz/vaults"
        params = {"account": address}
        response = get(url, params=params)

        if response.status_code == 200:
            vaults = response.json()
            return vaults
        else:
            raise RequestException(
                f"Failed to fetch vault data: {response.status_code}",
            )
    except RequestException as e:
        error_msg = f"Error getting vaults: {e}"
        log.exception(e)
        raise
    except JSONDecodeError as e:
        error_msg = f"JSON decoding error for vault: {e}"
        log.exception(error_msg)
        raise


def get_latest_valid_block() -> int:
    """
    Get the last mined block from the Basin API.

    Returns
    -------
        int: The last mined block.

    Raises
    ------
        Exception: If there is an error getting the last mined block.
    """
    try:
        w3 = get_w3()
        latest_block = Web3.to_int(w3.eth.block_number)
        # Optimistically assume 5 block depth for reorgs
        latest_block -= 5
        return latest_block
    except BlockNotFound as e:
        error_msg = f"Error getting latest valid block '{latest_block}': {e}"
        log.exception(error_msg)
        raise


def get_preceding_block_by_n_hours(end_block: int, hours: int) -> int:
    """
    Get the last mined block from the Basin API.

    Returns
    -------
        int: The last mined block.

    Raises
    ------
        Exception: If there is an error getting the last mined block.
    """
    block_time = 30  # Blocks are mined every 30 seconds
    blocks_per_hour = 3600 // block_time
    blocks_per_window = blocks_per_hour * hours

    return end_block - blocks_per_window


def check_block_range_is_valid(start_block: int, end_block: int) -> None:
    """
    Check if the block range is within 60480 block limit imposed by the
        Web3 events API.
    """
    block_range = end_block - start_block
    if (block_range) > 60480:
        error_msg = f"Block range exceeds 60480: {start_block} to {end_block}; block_range: {block_range}"
        log.exception(error_msg)
        raise
