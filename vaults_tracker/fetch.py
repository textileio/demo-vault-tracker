from json import JSONDecodeError, loads
from logging import INFO, basicConfig, getLogger
from pathlib import Path
from traceback import format_exc
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
    url = "https://rpc.ankr.com/filecoin_testnet"
    return Web3(Web3.HTTPProvider(url))


def get_block_timestamp(block_num: int) -> int:
    w3 = get_w3()
    block = w3.eth.get_block(block_num)
    return block["timestamp"]


def get_contract_create_events(
    start_block: int, end_block: int
) -> List[List[Dict[str, Any]]]:
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
        abi_file = Path(__file__).parent.parent / "abi.json"
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
        chunks = chunk_block_range(start_block, end_block)
        events = []
        for chunk in chunks:
            new_events = contract.events[new_vault_event].get_logs(  # type: ignore[attr-defined]
                fromBlock=chunk["start_block"], toBlock=chunk["end_block"]
            )
            if new_events:
                events.append(new_events)
        return events

    except ValueError as e:
        if "lookbacks of more than 720h0m0s are disallowed" in str(e):
            log.error("Block range exceeds 30 days")
        log.exception(e)
        log.error(format_exc())
        raise

    except Exception as e:
        log.error(
            f"Error getting contract create events for range: {start_block}, {end_block}"
        )
        log.exception(e)
        log.error(format_exc())
        raise


def get_data_from_events(
    contract_events: List[List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
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
        for events in contract_events:
            for event in events:
                args = event["args"]
                owner = args["owner"]
                vault = args["pub"]
                block_num = event["blockNumber"]
                owners.append(
                    {"owner": owner, "vault_hash": vault.hex(), "block_num": block_num}
                )

        return owners

    except Exception as e:
        error_msg = f"Error getting vault owners: {e}"
        log.exception(error_msg)
        log.error(format_exc())
        raise


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
        log.error(format_exc())
        raise
    except JSONDecodeError as e:
        error_msg = f"JSON decoding error for vault: {e}"
        log.exception(error_msg)
        log.error(format_exc())
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
        log.error(format_exc())
        raise


def chunk_block_range(start_block: int, end_block: int) -> List[Dict[str, int]]:
    """
    Check if the block range is within 60480 block limit imposed by the
        Web3 events API.
    """
    block_range = end_block - start_block
    if (block_range) > 2880:
        msg = f"Block range exceeds 2880: {start_block} to {end_block}; block_range: {block_range}"
        log.info(msg)
        start_chunk = start_block
        end_final = end_block
        chunks = []
        while block_range > 0:
            end_chunk = start_chunk + 2880  # Block range max is 2880
            if end_chunk > end_final:
                end_chunk = end_final
            chunks.append({"start_block": start_chunk, "end_block": end_chunk})
            start_chunk = end_chunk + 1
            block_range = end_final - start_chunk
        return chunks
    else:
        return [{"start_block": start_block, "end_block": end_block}]
