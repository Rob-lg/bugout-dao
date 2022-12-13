"""
Mint badges to addresses.

Caller specifies:
1. Blockchain
2. Terminus contract address
3. Badge pool id
4. Transaction parameters (gas, confirmations, etc.)
5. Addresses to mint badges to

The script checks if the addresses already have badges. It filters *out* the addresses that already
have the badge in question. It mints a single badge to all addresses that do *not* have the badge.
"""

import argparse

from brownie import network
from dao import TerminusFacet

parser = argparse.ArgumentParser(description="Mint Terminus badges to addresses")
TerminusFacet.add_default_arguments(parser, True)
parser.add_argument(
    "--pool-id",
    required=True,
    type=int,
    help="ID of Terminus pool representing the badge",
)
parser.add_argument(
    "--recipients", nargs="*", help="Addresses that badge should be minted to"
)
parser.add_argument(
    "--recipients-file",
    type=argparse.FileType("r"),
    help="(Optional) File containing addresses to mint badges to, one address per line. The addresses in this file are added to the addresses passed with the --recipients argument.",
)
parser.add_argument(
    "-y",
    "--yes",
    action="store_true",
    help="Set this flag to signal y on all confirmation prompts",
)
parser.add_argument(
    "--batch-size",
    type=int,
    default=200,
    help="Number of recipients to mint badges to per transaction.",
)

args = parser.parse_args()

if args.address is None:
    raise ValueError(
        "Please specify the address of a Terminus contract using the --address argument."
    )

if args.batch_size > 200:
    raise ValueError("This script can process at most 200 recipients per batch.")

network.connect(args.network)

recipients = list(set(args.recipients))

batches = []
for i in range(0, len(recipients), args.batch_size):
    batches.append(recipients[i : i + args.batch_size])

terminus = TerminusFacet.TerminusFacet(args.address)
pool_uri = terminus.uri(args.pool_id)

print(
    f"Badge information -- Terminus address: {args.address}, pool ID: {args.pool_id}, pool URI: {pool_uri}"
)

for i, batch in enumerate(batches):
    balances = zip(
        batch,
        terminus.balance_of_batch(recipients, [args.pool_id for _ in recipients]),
    )

    valid_recipients = [recipient for recipient, balance in balances if balance == 0]
    if not valid_recipients:
        print("No valid recipients in this batch")
        continue

    print("\n- ".join([f"Batch {i} -- intended recipients:"] + valid_recipients))

    if not args.yes:
        permission_check = input("Proceed? (y/N)")
        if permission_check.strip().lower() != "y":
            raise Exception("You did not wish to proceed")

    amounts = [1 for _ in valid_recipients]
    transaction_config = TerminusFacet.get_transaction_config(args)
    transaction_info = terminus.pool_mint_batch(
        args.pool_id, valid_recipients, amounts, transaction_config
    )

    print(transaction_info)
