# safety_filter.py
def check_safety(text: str) -> bool:
    # Flag text if contains any banned words
    banned = ["badword", "unsafe"]
    return any(word in text.lower() for word in banned)






