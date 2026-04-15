"""
SM-2 Spaced Repetition Algorithm - Pure functions, no I/O dependencies.
"""

def accuracy_to_quality(accuracy: float) -> int:
    """Convert accuracy percentage (0-100) to SM-2 quality score (1-5)."""
    if accuracy >= 90:
        return 5
    elif accuracy >= 75:
        return 4
    elif accuracy >= 60:
        return 3
    elif accuracy >= 40:
        return 2
    else:
        return 1

def calculate_next_interval(
    repetitions: int,
    ease_factor: float,
    interval_days: float,
    quality: int
) -> tuple[int, float, float]:
    """
    Calculate next review interval using SM-2 algorithm.

    Args:
        repetitions: Number of successful repetitions
        ease_factor: Current ease factor (min 1.3)
        interval_days: Current interval in days
        quality: Quality of response (0-5)

    Returns:
        (new_repetitions, new_interval_days, new_ease_factor)
    """
    if quality < 3:
        new_repetitions = 0
        new_interval = 1.0
    elif repetitions == 0:
        new_repetitions = 1
        new_interval = 1.0
    elif repetitions == 1:
        new_repetitions = 2
        new_interval = 3.0
    else:
        new_repetitions = repetitions + 1
        new_interval = round(interval_days * ease_factor, 1)

    new_ease_factor = max(1.3, ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    return new_repetitions, new_interval, new_ease_factor
