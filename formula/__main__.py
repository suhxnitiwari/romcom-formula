import sys

from . import catalog, label


def main(argv):
    command = argv[0] if argv else "catalog"
    if command == "catalog":
        pulled, kept, dropped = catalog.build()
        print(f"Pulled {len(pulled)} romances readers called funny or lighthearted.")
        for reason, n in sorted(dropped.items(), key=lambda x: -x[1]):
            print(f"  - {n:4} dropped: {reason}")
        print(f"Kept {len(kept)} contemporary rom-coms -> data/books.json")
    elif command == "label":
        label.serve(open_browser="--no-open" not in argv)
    else:
        raise SystemExit(f"Unknown command: {command}")


main(sys.argv[1:])
