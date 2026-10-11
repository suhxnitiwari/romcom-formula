import sys

from . import catalog, label


def main(argv):
    command = argv[0] if argv else "catalog"
    if command == "catalog":
        pulled, kept, dropped = catalog.build()
        print(f"Pulled {len(pulled)} romances from Hardcover (2010 on, 50+ ratings).")
        for reason, n in sorted(dropped.items(), key=lambda x: -x[1]):
            print(f"  - {n:4} dropped: {reason}")
        print(f"Kept {len(kept)} contemporary romances -> data/books.json")
        for key, name in catalog.SHELVES.items():
            print(f"  {sum(b['shelf'] == key for b in kept):4}  {name}")
    elif command == "label":
        label.serve(open_browser="--no-open" not in argv)
    else:
        raise SystemExit(f"Unknown command: {command}")


main(sys.argv[1:])
