import json
import os

from garmin_mcp.workout_builders import (
    build_continuous_run_json,
    build_walk_run_json,
    build_z2_walk_json,
    build_strength_json,
    _lookup_exercise,
)

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "captured")


def test_build_walk_run_json_matches_poc_snapshot():
    """The walk/run builder must produce the exact JSON that Garmin accepted in the POC."""
    result = build_walk_run_json(
        name="POC Walk/Run 7x1m/3m Z3",
        run_seconds=60,
        walk_seconds=180,
        repeats=7,
        warmup_min=10,
        cooldown_min=8,
        hr_zone="Z3",
    )

    # Compare against the validated POC snapshot
    snapshot_path = os.path.join(SNAPSHOT_DIR, "poc_walk_run.json")
    with open(snapshot_path, "r", encoding="utf-8") as f:
        expected = json.load(f)

    assert result == expected


def test_build_z2_walk_json_structure():
    result = build_z2_walk_json(
        name="Z2 Walk 30m",
        duration_min=30,
        hr_min=110,
        hr_max=130,
    )
    assert result["workoutName"] == "Z2 Walk 30m"
    assert result["sportType"]["sportTypeKey"] == "walking"
    assert result["sportType"]["sportTypeId"] == 12
    steps = result["workoutSegments"][0]["workoutSteps"]
    assert len(steps) == 3
    assert steps[1]["zoneNumber"] == 2
    assert steps[1]["endConditionValue"] == 1800.0


def test_build_continuous_run_json_custom_hr_range():
    result = build_continuous_run_json(
        name="Run 25m",
        duration_min=25,
        hr_min=123,
        hr_max=133,
        warmup_min=5,
        cooldown_min=5,
    )

    assert result["workoutName"] == "Run 25m"
    assert result["sportType"]["sportTypeKey"] == "running"
    steps = result["workoutSegments"][0]["workoutSteps"]
    assert len(steps) == 3
    assert steps[0]["zoneNumber"] == 1
    assert steps[1]["stepType"]["stepTypeId"] == 3
    assert steps[1]["zoneNumber"] == 0
    assert steps[1]["targetValueOne"] == 123
    assert steps[1]["targetValueTwo"] == 133
    assert steps[1]["endConditionValue"] == 1500.0
    assert steps[2]["zoneNumber"] == 1


def test_build_strength_json_structure():
    result = build_strength_json(
        name="Full Body A",
        exercises=[
            {"name": "Sentadillas", "sets": 3, "reps": 12, "rest_seconds": 90},
            {"name": "Curl de biceps", "sets": 3, "reps": 15, "rest_seconds": 60},
        ],
    )
    assert result["workoutName"] == "Full Body A"
    assert result["sportType"]["sportTypeKey"] == "strength_training"
    assert result["sportType"]["sportTypeId"] == 5
    steps = result["workoutSegments"][0]["workoutSteps"]
    # Each exercise is a RepeatGroupDTO
    assert len(steps) == 2
    # First exercise: catalog exercise (Sentadillas) maps to Garmin codes
    assert steps[0]["type"] == "RepeatGroupDTO"
    assert steps[0]["numberOfIterations"] == 3
    assert steps[0]["skipLastRestStep"] is True
    nested = steps[0]["workoutSteps"]
    assert len(nested) == 2  # work + rest
    assert nested[0]["endCondition"]["conditionTypeKey"] == "reps"
    assert nested[0]["endConditionValue"] == 12.0
    assert nested[0]["category"] == "SQUAT"
    assert nested[0]["exerciseName"] == "SQUAT"
    assert nested[1]["stepType"]["stepTypeKey"] == "rest"
    assert nested[1]["endConditionValue"] == 90.0
    # Second exercise: fuzzy matched ("Curl de biceps" matches English catalog)
    nested2 = steps[1]["workoutSteps"]
    assert nested2[0]["category"] == "CURL"
    assert nested2[0]["exerciseName"] == "ALTERNATING_DUMBBELL_BICEPS_CURL"


def test_lookup_exercise_spanish_alias():
    category, exercise_name = _lookup_exercise("Sentadillas")
    assert category == "SQUAT"
    assert exercise_name == "SQUAT"


def test_lookup_exercise_english_catalog():
    category, exercise_name = _lookup_exercise("Barbell Bench Press")
    assert category == "BENCH_PRESS"
    assert exercise_name == "BARBELL_BENCH_PRESS"


def test_lookup_exercise_fuzzy_matching():
    """Fuzzy matching finds English exercises from Spanish descriptions."""
    # "curl de biceps inclinado" should match a curl exercise
    category, exercise_name = _lookup_exercise("curl de biceps inclinado")
    assert category == "CURL"
    assert "BICEPS" in exercise_name

    # "peso muerto rumano" should match a deadlift exercise
    category, exercise_name = _lookup_exercise("peso muerto rumano")
    assert category == "DEADLIFT"
    assert "DEADLIFT" in exercise_name


def test_lookup_exercise_fallback():
    category, exercise_name = _lookup_exercise("Ejercicio Totalmente Inventado XYZ123")
    assert category is None
    assert exercise_name is None


def test_build_strength_json_time_based_exercise():
    """Time-based exercises (isometric) use conditionTypeKey='time' instead of 'reps'."""
    result = build_strength_json(
        name="Core Session",
        exercises=[
            {"name": "Plank", "sets": 3, "duration_seconds": 45, "rest_seconds": 60},
            {"name": "Squat", "sets": 3, "reps": 10, "rest_seconds": 90},
        ],
    )
    steps = result["workoutSegments"][0]["workoutSteps"]
    # First exercise: time-based (plank)
    plank_work = steps[0]["workoutSteps"][0]
    assert plank_work["endCondition"]["conditionTypeKey"] == "time"
    assert plank_work["endConditionValue"] == 45.0
    assert plank_work["description"] == "Plank: 3x45s"
    assert plank_work["category"] == "PLANK"
    assert plank_work["exerciseName"] == "PLANK"
    # Second exercise: rep-based (squat)
    squat_work = steps[1]["workoutSteps"][0]
    assert squat_work["endCondition"]["conditionTypeKey"] == "reps"
    assert squat_work["endConditionValue"] == 10.0
    assert squat_work["description"] == "Squat: 3x10"
