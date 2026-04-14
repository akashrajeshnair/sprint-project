XP_RULES = {
    "Mathematics": {"easy": 5, "medium": 10, "hard": 20},
    "Physics": {"easy": 6, "medium": 12, "hard": 24},
    "Chemistry": {"easy": 5, "medium": 11, "hard": 22},
    "History": {"easy": 4, "medium": 8, "hard": 16},
}


def calculate_xp(subject: str, difficulty: str) -> int:
    return XP_RULES.get(subject, {}).get(difficulty, 0)