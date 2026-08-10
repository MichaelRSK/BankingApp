# Branch represents a physical location of the bank, with its own
# manager and staff.
class Branch:

    # Constructor method that runs when a Branch object is created.
    # branch_code, location, and manager_id are expected to be strings.
    # staff is optional, if not provided, the branch starts with no staff.
    def __init__(self, branch_code: str, location: str, manager_id: str, staff=None):
        self.branch_code = branch_code
        self.location = location
        self.manager_id = manager_id

        # If no staff list is provided, start with an empty list instead of
        # sharing one default list across every Branch object.
        self.staff = staff if staff is not None else []

    # Adds a staff member's ID to this branch.
    def add_staff(self, staff_id):
        self.staff.append(staff_id)

    # Removes a staff member's ID from this branch, if they're on staff.
    def remove_staff(self, staff_id):
        if staff_id in self.staff:
            self.staff.remove(staff_id)

    # Calculates how many staff members exist per manager.
    # This model assumes exactly one manager per branch, so the ratio
    # simplifies down to just the number of staff members.
    def staff_to_manager_ratio(self):
        return len(self.staff)