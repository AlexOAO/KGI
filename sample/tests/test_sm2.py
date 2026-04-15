"""Unit tests for SM-2 algorithm."""
import pytest
from app.services.sm2 import accuracy_to_quality, calculate_next_interval


class TestAccuracyToQuality:
    def test_90_plus_returns_5(self):
        assert accuracy_to_quality(90) == 5
        assert accuracy_to_quality(100) == 5
        assert accuracy_to_quality(95) == 5

    def test_75_to_89_returns_4(self):
        assert accuracy_to_quality(75) == 4
        assert accuracy_to_quality(80) == 4
        assert accuracy_to_quality(89) == 4

    def test_60_to_74_returns_3(self):
        assert accuracy_to_quality(60) == 3
        assert accuracy_to_quality(70) == 3
        assert accuracy_to_quality(74) == 3

    def test_40_to_59_returns_2(self):
        assert accuracy_to_quality(40) == 2
        assert accuracy_to_quality(50) == 2
        assert accuracy_to_quality(59) == 2

    def test_below_40_returns_1(self):
        assert accuracy_to_quality(0) == 1
        assert accuracy_to_quality(20) == 1
        assert accuracy_to_quality(39) == 1


class TestCalculateNextInterval:
    def test_quality_below_3_resets(self):
        reps, interval, ef = calculate_next_interval(5, 2.5, 10.0, 2)
        assert reps == 0
        assert interval == 1.0

    def test_first_rep(self):
        reps, interval, ef = calculate_next_interval(0, 2.5, 1.0, 4)
        assert reps == 1
        assert interval == 1.0

    def test_second_rep(self):
        reps, interval, ef = calculate_next_interval(1, 2.5, 1.0, 4)
        assert reps == 2
        assert interval == 3.0

    def test_subsequent_rep(self):
        reps, interval, ef = calculate_next_interval(2, 2.5, 3.0, 4)
        assert reps == 3
        assert interval == round(3.0 * 2.5, 1)

    def test_ease_factor_min_1_3(self):
        _, _, ef = calculate_next_interval(0, 1.3, 1.0, 0)
        assert ef >= 1.3

    def test_ease_factor_increases_on_perfect(self):
        _, _, ef = calculate_next_interval(2, 2.5, 3.0, 5)
        assert ef > 2.5

    def test_ease_factor_decreases_on_poor(self):
        _, _, ef = calculate_next_interval(2, 2.5, 3.0, 3)
        assert ef < 2.5
