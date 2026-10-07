ACADEMIC_BLOCKS = ["SJT", "TT", "PRP", "SMV", "MB", "GDN", "CDMM"]
MENS_HOSTELS = [f"MH-{chr(c)}" for c in range(ord("A"), ord("T") + 1)]
LADIES_HOSTELS = [f"LH-{chr(c)}" for c in range(ord("A"), ord("J") + 1)]
FOOD_COURTS = ["Gazebo", "Food Mall", "DC"]
OTHER_VENUES = ["Central Library", "Sports Complex"]

VENUES = ACADEMIC_BLOCKS + MENS_HOSTELS + LADIES_HOSTELS + FOOD_COURTS + OTHER_VENUES

CATEGORIES = [
    "ID Cards",
    "Room Keys",
    "Calculators",
    "Lab Equipment",
    "Earphones",
    "Wallets",
]

HANDOFF_POINTS = [
    "SJT Ground Floor Reception",
    "Central Library Security Desk",
    "TT Main Entrance",
    "PRP Ground Floor Reception",
    "Sports Complex Entrance",
    "Main Gate Security Desk",
]
