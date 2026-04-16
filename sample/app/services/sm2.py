def calculate_next_interval(repetitions: int, ease_factor: float, quality: int, current_interval: int = 1):
    if quality < 3:
        repetitions = 0
        interval = 1
    elif repetitions == 0:
        interval = 1
    elif repetitions == 1:
        interval = 3
    else:
        interval = round(current_interval * ease_factor)

    ease_factor = max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    repetitions += 1
    return interval, ease_factor, repetitions


def score_to_quality(score: float) -> int:
    if score >= 90:
        return 5
    elif score >= 75:
        return 4
    elif score >= 60:
        return 3
    elif score >= 40:
        return 2
    else:
        return 0
