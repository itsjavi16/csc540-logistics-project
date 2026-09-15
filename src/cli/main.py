"""
Menu-driven CLI entry point.

Root menu mirrors Appendix A of the project description:
  [1] Shipper   [2] Carrier   [3] Viewer   [4] View Queries

This is a stub to get the repo running end-to-end early. Fill in each
role's submenu as the corresponding functions are implemented in
src/models/ and src/reports/.
"""


def root_menu():
    while True:
        print("\n=== CSC 540 Freight Tracking ===")
        print("[1] Shipper")
        print("[2] Carrier")
        print("[3] Viewer")
        print("[4] View Queries")
        print("[0] Exit")
        choice = input("Select an option: ").strip()

        if choice == "1":
            shipper_menu()
        elif choice == "2":
            carrier_menu()
        elif choice == "3":
            viewer_menu()
        elif choice == "4":
            view_queries_menu()
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Invalid selection.")


def shipper_menu():
    print("\n[Shipper] -- TODO: Create/Update Shipment, Book, Track, Reports")


def carrier_menu():
    print("\n[Carrier] -- TODO: Manage Vehicles, Manage Departures, Post Scan, Reports")


def viewer_menu():
    print("\n[Viewer] -- TODO: Track Shipment, Published Performance Reports")


def view_queries_menu():
    print("\n[View Queries] -- TODO: numbered list of required analytical queries")


if __name__ == "__main__":
    root_menu()
