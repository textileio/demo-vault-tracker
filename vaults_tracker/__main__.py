import sys

from .fetch import (
    check_block_range_is_valid,
    get_contract_create_events,
    get_latest_valid_block,
    get_preceding_block_by_n_hours,
    get_vault_owners,
    get_vaults,
)

if __name__ == "__main__":
    try:
        end_block = get_latest_valid_block()
        start_block = get_preceding_block_by_n_hours(end_block, 360)
        check_block_range_is_valid(start_block, end_block)

        events = get_contract_create_events(start_block, end_block)
        owners = get_vault_owners(events)

        vaults = []
        for owner in owners:
            vault = get_vaults(owner)
            vaults.append({owner: vault})
        print(vaults)

    except Exception:
        sys.exit(1)
