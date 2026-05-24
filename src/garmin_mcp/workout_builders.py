"""
High-level workout builders for Garmin Connect MCP Server.

These tools construct the internal Garmin Connect JSON internally and delegate
to the existing upload_workout / schedule_workout endpoints.
"""
import json
import os
from typing import Any, Dict, List, Optional, Tuple

# The garmin_client will be set by the main file
garmin_client = None

# Load full Garmin exercise catalog (English names → {category, exerciseName})
_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "data", "garmin_exercises.json")
_EXERCISE_CATALOG_EN: Dict[str, Dict[str, str]] = {}
if os.path.exists(_CATALOG_PATH):
    with open(_CATALOG_PATH, "r", encoding="utf-8") as _f:
        _EXERCISE_CATALOG_EN = json.load(_f)


def configure(client):
    """Configure the module with the Garmin client instance"""
    global garmin_client
    garmin_client = client


# =============================================================================
# JSON BUILDERS
# =============================================================================

HR_ZONE_MAP = {
    "Z1": 1,
    "Z2": 2,
    "Z3": 3,
    "Z4": 4,
    "Z5": 5,
}


def _zone_number(zone: str) -> int:
    """Resolve a human-friendly zone string like 'Z3' to Garmin's zoneNumber."""
    zone_upper = zone.strip().upper()
    if zone_upper in HR_ZONE_MAP:
        return HR_ZONE_MAP[zone_upper]
    # Fallback: if user passed a digit directly
    try:
        z = int(zone_upper)
        if 1 <= z <= 5:
            return z
    except ValueError:
        pass
    raise ValueError(f"Invalid hr_zone '{zone}'. Use Z1-Z5 or 1-5.")


def build_walk_run_json(
    name: str,
    run_seconds: int,
    walk_seconds: int,
    repeats: int,
    warmup_min: int,
    cooldown_min: int,
    hr_zone: str = "Z3",
) -> dict:
    """Build the Garmin Connect JSON for a walk/run interval workout.

    Parameters match create_walk_run_workout exactly.
    """
    zone = _zone_number(hr_zone)
    return {
        "workoutName": name,
        "description": (
            f"{warmup_min}m warmup + {repeats}x({run_seconds}s run / {walk_seconds}s walk) Z{zone} + "
            f"{cooldown_min}m cooldown"
        ),
        "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
        "workoutSegments": [{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
            "workoutSteps": [
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 1,
                    "stepType": {"stepTypeId": 1, "stepTypeKey": "warmup"},
                    "description": f"Warmup {warmup_min} min",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": float(warmup_min * 60),
                    "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                },
                {
                    "type": "RepeatGroupDTO",
                    "stepOrder": 2,
                    "numberOfIterations": repeats,
                    "workoutSteps": [
                        {
                            "type": "ExecutableStepDTO",
                            "stepOrder": 1,
                            "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                            "description": f"Run {run_seconds}s Z{zone}",
                            "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                            "endConditionValue": float(run_seconds),
                            "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
                            "zoneNumber": zone,
                        },
                        {
                            "type": "ExecutableStepDTO",
                            "stepOrder": 2,
                            "stepType": {"stepTypeId": 4, "stepTypeKey": "recovery"},
                            "description": f"Walk {walk_seconds}s Z{zone}",
                            "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                            "endConditionValue": float(walk_seconds),
                            "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
                            "zoneNumber": zone,
                        },
                    ],
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 3,
                    "stepType": {"stepTypeId": 2, "stepTypeKey": "cooldown"},
                    "description": f"Cooldown {cooldown_min} min",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": float(cooldown_min * 60),
                    "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                },
            ],
        }],
    }


def build_z2_walk_json(
    name: str,
    duration_min: int,
    hr_min: int,
    hr_max: int,
) -> dict:
    """Build the Garmin Connect JSON for a steady Z2 walking workout with absolute HR range."""
    return {
        "workoutName": name,
        "description": f"Walk {duration_min} min at Z2 ({hr_min}-{hr_max} bpm)",
        "sportType": {"sportTypeId": 12, "sportTypeKey": "walking"},
        "workoutSegments": [{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": 12, "sportTypeKey": "walking"},
            "workoutSteps": [
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 1,
                    "stepType": {"stepTypeId": 1, "stepTypeKey": "warmup"},
                    "description": "Warmup 5 min",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": 300.0,
                    "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 2,
                    "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                    "description": f"Walk {duration_min} min Z2",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": float(duration_min * 60),
                    "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
                    "zoneNumber": 2,
                },
                {
                    "type": "ExecutableStepDTO",
                    "stepOrder": 3,
                    "stepType": {"stepTypeId": 2, "stepTypeKey": "cooldown"},
                    "description": "Cooldown 5 min",
                    "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                    "endConditionValue": 300.0,
                    "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                },
            ],
        }],
    }


def build_continuous_run_json(
    name: str,
    duration_min: int,
    hr_min: int,
    hr_max: int,
    warmup_min: int = 0,
    cooldown_min: int = 0,
) -> dict:
    """Build the Garmin Connect JSON for a continuous run with a custom HR range."""
    steps = []
    step_order = 1

    if warmup_min:
        steps.append({
            "type": "ExecutableStepDTO",
            "stepOrder": step_order,
            "stepType": {"stepTypeId": 1, "stepTypeKey": "warmup"},
            "description": f"Warmup {warmup_min} min Z1",
            "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
            "endConditionValue": float(warmup_min * 60),
            "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
            "zoneNumber": 1,
        })
        step_order += 1

    steps.append({
        "type": "ExecutableStepDTO",
        "stepOrder": step_order,
        "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
        "description": f"Run {duration_min} min {hr_min}-{hr_max} bpm",
        "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
        "endConditionValue": float(duration_min * 60),
        "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
        "zoneNumber": 0,
        "targetValueOne": hr_min,
        "targetValueTwo": hr_max,
    })
    step_order += 1

    if cooldown_min:
        steps.append({
            "type": "ExecutableStepDTO",
            "stepOrder": step_order,
            "stepType": {"stepTypeId": 2, "stepTypeKey": "cooldown"},
            "description": f"Cooldown {cooldown_min} min Z1",
            "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
            "endConditionValue": float(cooldown_min * 60),
            "targetType": {"workoutTargetTypeId": 4, "workoutTargetTypeKey": "heart.rate.zone"},
            "zoneNumber": 1,
        })

    return {
        "workoutName": name,
        "description": f"Run {duration_min} min at {hr_min}-{hr_max} bpm",
        "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
        "workoutSegments": [{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": 1, "sportTypeKey": "running"},
            "workoutSteps": steps,
        }],
    }


# Spanish → Garmin Connect exercise catalog mapping.
# Validated by creating workouts via API and verifying that Garmin preserves
# category + exerciseName. If Garmin returns nulls, the code is invalid.
EXERCISE_CATALOG_ES = {
    # === PLANCHA / PLANK ===
    "Plancha": {"category": "PLANK", "exerciseName": "PLANK"},
    "Plancha lateral": {"category": "PLANK", "exerciseName": "SIDE_PLANK"},
    "Plancha con piernas elevadas": {"category": "PLANK", "exerciseName": "ELEVATED_FEET_PLANK"},
    "Plancha con brazos extendidos": {"category": "PLANK", "exerciseName": "EXTENDED_PLANK"},
    "Plancha con toque de hombro": {"category": "PLANK", "exerciseName": "SHOULDER_TAP_PLANK"},
    "Plancha pica": {"category": "PLANK", "exerciseName": "PLANK_PIKE"},
    "Plancha con rotación": {"category": "PLANK", "exerciseName": "PLANK_ROTATION"},
    "Plancha con salto": {"category": "PLANK", "exerciseName": "PLANK_JACK"},
    "Plancha de rodillas": {"category": "PLANK", "exerciseName": "KNEELING_PLANK"},

    # === SENTADILLAS / SQUAT ===
    "Sentadillas": {"category": "SQUAT", "exerciseName": "SQUAT"},
    "Sentadilla con barra": {"category": "SQUAT", "exerciseName": "BARBELL_BACK_SQUAT"},
    "Sentadilla frontal": {"category": "SQUAT", "exerciseName": "BARBELL_FRONT_SQUAT"},
    "Sentadilla búlgara": {"category": "SQUAT", "exerciseName": "BARBELL_BULGARIAN_SPLIT_SQUAT"},
    "Sentadilla goblet": {"category": "SQUAT", "exerciseName": "GOBLET_SQUAT"},
    "Sentadilla con mancuernas": {"category": "SQUAT", "exerciseName": "DUMBBELL_SQUAT"},
    "Sentadilla hack": {"category": "SQUAT", "exerciseName": "HACK_SQUAT"},
    "Sentadilla sumo": {"category": "SQUAT", "exerciseName": "SUMO_SQUAT"},
    "Sentadilla con salto": {"category": "SQUAT", "exerciseName": "JUMP_SQUAT"},
    "Sentadilla isométrica": {"category": "SQUAT", "exerciseName": "WALL_SIT"},
    "Sentadilla box": {"category": "SQUAT", "exerciseName": "BARBELL_BOX_SQUAT"},
    "Sentadilla dividida": {"category": "SQUAT", "exerciseName": "DUMBBELL_SPLIT_SQUAT"},
    "Sentadilla sissy": {"category": "SQUAT", "exerciseName": "SISSY_SQUAT"},
    "Sentadilla pistola": {"category": "SQUAT", "exerciseName": "PISTOL_SQUAT"},
    "Prensa de piernas": {"category": "SQUAT", "exerciseName": "LEG_PRESS"},
    "Prensa 45": {"category": "SQUAT", "exerciseName": "LEG_PRESS"},
    "Sentadilla en máquina": {"category": "SQUAT", "exerciseName": "LEG_PRESS"},
    "Sentadilla aéreo": {"category": "SQUAT", "exerciseName": "AIR_SQUAT"},
    "Sentadilla con banda": {"category": "SQUAT", "exerciseName": "BANDED_SQUAT"},

    # === PRESS BANCA / BENCH_PRESS ===
    "Press banca": {"category": "BENCH_PRESS", "exerciseName": "BENCH_PRESS"},
    "Press banca con barra": {"category": "BENCH_PRESS", "exerciseName": "BARBELL_BENCH_PRESS"},
    "Press banca con mancuernas": {"category": "BENCH_PRESS", "exerciseName": "DUMBELL_BENCH_PRESS"},
    "Press banca inclinado": {"category": "BENCH_PRESS", "exerciseName": "INCLINE_BARBELL_BENCH_PRESS"},
    "Press banca declinado": {"category": "BENCH_PRESS", "exerciseName": "DECLINE_DUMBBELL_BENCH_PRESS"},
    "Press banca con agarre cerrado": {"category": "BENCH_PRESS", "exerciseName": "CLOSE_GRIP_BARBELL_BENCH_PRESS"},
    "Press banca en máquina": {"category": "BENCH_PRESS", "exerciseName": "SMITH_MACHINE_BENCH_PRESS"},
    "Press de pecho": {"category": "BENCH_PRESS", "exerciseName": "BENCH_PRESS"},
    "Press de pecho con mancuernas": {"category": "BENCH_PRESS", "exerciseName": "DUMBELL_BENCH_PRESS"},

    # === PESO MUERTO / DEADLIFT ===
    "Peso muerto": {"category": "DEADLIFT", "exerciseName": "DEADLIFT"},
    "Peso muerto con barra": {"category": "DEADLIFT", "exerciseName": "BARBELL_DEADLIFT"},
    "Peso muerto rumano": {"category": "DEADLIFT", "exerciseName": "ROMANIAN_DEADLIFT"},
    "Peso muerto sumo": {"category": "DEADLIFT", "exerciseName": "SUMO_DEADLIFT"},
    "Peso muerto con mancuernas": {"category": "DEADLIFT", "exerciseName": "DUMBBELL_DEADLIFT"},
    "Peso muerto a una pierna": {"category": "DEADLIFT", "exerciseName": "SINGLE_LEG_DEADLIFT"},
    "Peso muerto hexagonal": {"category": "DEADLIFT", "exerciseName": "HEX_BAR_DEADLIFT"},
    "Peso muerto stiff": {"category": "DEADLIFT", "exerciseName": "STIFF_LEG_DEADLIFT"},

    # === DOMINADAS / PULL_UP ===
    "Dominadas": {"category": "PULL_UP", "exerciseName": "PULL_UP"},
    "Dominada agarre prono": {"category": "PULL_UP", "exerciseName": "PULL_UP"},
    "Dominada agarre supino": {"category": "PULL_UP", "exerciseName": "CHIN_UP"},
    "Dominada en máquina": {"category": "PULL_UP", "exerciseName": "LAT_PULLDOWN"},
    "Jalón al pecho": {"category": "PULL_UP", "exerciseName": "LAT_PULLDOWN"},
    "Jalón tras nuca": {"category": "PULL_UP", "exerciseName": "BEHIND_THE_NECK_LAT_PULLDOWN"},
    "Muscle up": {"category": "PULL_UP", "exerciseName": "MUSCLE_UP"},
    "Dominada con agarre cerrado": {"category": "PULL_UP", "exerciseName": "CLOSE_GRIP_CHIN_UP"},

    # === FLEXIONES / PUSH_UP ===
    "Flexiones": {"category": "PUSH_UP", "exerciseName": "PUSH_UP"},
    "Flexión de pecho": {"category": "PUSH_UP", "exerciseName": "PUSH_UP"},
    "Flexiones con agarre cerrado": {"category": "PUSH_UP", "exerciseName": "CLOSE_HANDS_PUSH_UP"},
    "Flexiones con aplauso": {"category": "PUSH_UP", "exerciseName": "CLAPPING_PUSH_UP"},
    "Flexiones con pies elevados": {"category": "PUSH_UP", "exerciseName": "ELEVATED_FEET_PUSH_UP"},
    "Flexiones diamante": {"category": "PUSH_UP", "exerciseName": "DIAMOND_PUSH_UP"},
    "Flexiones pike": {"category": "PUSH_UP", "exerciseName": "PIKE_PUSH_UP"},
    "Flexiones hindú": {"category": "PUSH_UP", "exerciseName": "HINDU_PUSH_UP"},
    "Fondos": {"category": "PUSH_UP", "exerciseName": "DIP"},
    "Fondos en paralelas": {"category": "PUSH_UP", "exerciseName": "DIP"},
    "Fondos en banco": {"category": "PUSH_UP", "exerciseName": "BENCH_DIP"},

    # === ZANCADAS / LUNGE ===
    "Zancadas": {"category": "LUNGE", "exerciseName": "LUNGE"},
    "Zancada con mancuernas": {"category": "LUNGE", "exerciseName": "ALTERNATING_DUMBBELL_LUNGE"},
    "Zancada búlgara": {"category": "LUNGE", "exerciseName": "BARBELL_BULGARIAN_SPLIT_SQUAT"},
    "Zancada lateral": {"category": "LUNGE", "exerciseName": "LATERAL_LUNGE"},
    "Zancada caminando": {"category": "LUNGE", "exerciseName": "WALKING_LUNGE"},
    "Zancada inversa": {"category": "LUNGE", "exerciseName": "REVERSE_LUNGE"},
    "Zancada con salto": {"category": "LUNGE", "exerciseName": "JUMP_LUNGE"},

    # === ABDOMINALES / CRUNCH ===
    "Abdominales": {"category": "CRUNCH", "exerciseName": "CRUNCH"},
    "Crunch": {"category": "CRUNCH", "exerciseName": "CRUNCH"},
    "Crunch bicicleta": {"category": "CRUNCH", "exerciseName": "BICYCLE_CRUNCH"},
    "Crunch inverso": {"category": "CRUNCH", "exerciseName": "REVERSE_CRUNCH"},
    "Crunch con cable": {"category": "CRUNCH", "exerciseName": "CABLE_CRUNCH"},
    "Crunch oblicuo": {"category": "CRUNCH", "exerciseName": "OBLIQUE_CRUNCH"},
    "Crunch en máquina": {"category": "CRUNCH", "exerciseName": "MACHINE_CRUNCH"},
    "Crunch en V": {"category": "CRUNCH", "exerciseName": "V_UP"},

    # === CURL BICEPS / CURL ===
    "Curl bíceps": {"category": "CURL", "exerciseName": "DUMBBELL_BICEPS_CURL"},
    "Curl bíceps con barra": {"category": "CURL", "exerciseName": "BARBELL_BICEPS_CURL"},
    "Curl bíceps con mancuernas": {"category": "CURL", "exerciseName": "DUMBBELL_BICEPS_CURL"},
    "Curl bíceps alternado": {"category": "CURL", "exerciseName": "ALTERNATING_DUMBBELL_BICEPS_CURL"},
    "Curl bíceps en banco inclinado": {"category": "CURL", "exerciseName": "INCLINE_DUMBBELL_BICEPS_CURL"},
    "Curl bíceps martillo": {"category": "CURL", "exerciseName": "HAMMER_CURL"},
    "Curl bíceps concentrado": {"category": "CURL", "exerciseName": "CONCENTRATION_CURL"},
    "Curl bíceps con cable": {"category": "CURL", "exerciseName": "CABLE_BICEPS_CURL"},
    "Curl bíceps predicador": {"category": "CURL", "exerciseName": "PREACHER_CURL"},

    # === PRESS MILITAR / SHOULDER_PRESS ===
    "Press militar": {"category": "SHOULDER_PRESS", "exerciseName": "SHOULDER_PRESS"},
    "Press militar con barra": {"category": "SHOULDER_PRESS", "exerciseName": "BARBELL_SHOULDER_PRESS"},
    "Press militar con mancuernas": {"category": "SHOULDER_PRESS", "exerciseName": "DUMBBELL_SHOULDER_PRESS"},
    "Press de hombros": {"category": "SHOULDER_PRESS", "exerciseName": "SHOULDER_PRESS"},
    "Press Arnold": {"category": "SHOULDER_PRESS", "exerciseName": "ARNOLD_PRESS"},
    "Press de hombros sentado": {"category": "SHOULDER_PRESS", "exerciseName": "SEATED_DUMBBELL_SHOULDER_PRESS"},

    # === REMO / ROW ===
    "Remo": {"category": "ROW", "exerciseName": "BARBELL_ROW"},
    "Remo con barra": {"category": "ROW", "exerciseName": "BARBELL_ROW"},
    "Remo con mancuernas": {"category": "ROW", "exerciseName": "BENT_OVER_ROW_WITH_DUMBBELL"},
    "Remo en máquina": {"category": "ROW", "exerciseName": "SEATED_CABLE_ROW"},
    "Remo sentado": {"category": "ROW", "exerciseName": "SEATED_CABLE_ROW"},
    "Remo con cable": {"category": "ROW", "exerciseName": "CABLE_ROW_STANDING"},
    "Remo T": {"category": "ROW", "exerciseName": "T_BAR_ROW"},
    "Remo pendlay": {"category": "ROW", "exerciseName": "PENDLAY_ROW"},
    "Remo con TRX": {"category": "ROW", "exerciseName": "TRX_INVERTED_ROW"},
    "Remo face pull": {"category": "ROW", "exerciseName": "FACE_PULL"},

    # === HIP THRUST / HIP_RAISE ===
    "Hip thrust": {"category": "HIP_RAISE", "exerciseName": "BARBELL_HIP_THRUST_WITH_BENCH"},
    "Hip thrust con barra": {"category": "HIP_RAISE", "exerciseName": "BARBELL_HIP_THRUST_WITH_BENCH"},
    "Hip thrust con mancuernas": {"category": "HIP_RAISE", "exerciseName": "DUMBBELL_HIP_THRUST"},
    "Puente de glúteos": {"category": "HIP_RAISE", "exerciseName": "HIP_RAISE"},
    "Puente de glúteos con mancuernas": {"category": "HIP_RAISE", "exerciseName": "WEIGHTED_HIP_RAISE"},
    "Puente de glúteos a una pierna": {"category": "HIP_RAISE", "exerciseName": "SINGLE_LEG_HIP_RAISE"},

    # === GEMELOS / CALF_RAISE ===
    "Elevación de gemelos": {"category": "CALF_RAISE", "exerciseName": "CALF_RAISE"},
    "Elevación de gemelos de pie": {"category": "CALF_RAISE", "exerciseName": "STANDING_CALF_RAISE"},
    "Elevación de gemelos sentado": {"category": "CALF_RAISE", "exerciseName": "SEATED_CALF_RAISE"},
    "Elevación de gemelos en prensa": {"category": "CALF_RAISE", "exerciseName": "LEG_PRESS_CALF_RAISE"},

    # === TRÍCEPS / TRICEPS_EXTENSION ===
    "Extensión de tríceps": {"category": "TRICEPS_EXTENSION", "exerciseName": "TRICEPS_EXTENSION"},
    "Extensión de tríceps con cable": {"category": "TRICEPS_EXTENSION", "exerciseName": "CABLE_OVERHEAD_TRICEPS_EXTENSION"},
    "Extensión de tríceps con mancuernas": {"category": "TRICEPS_EXTENSION", "exerciseName": "DUMBBELL_LYING_TRICEPS_EXTENSION"},
    "Extensión de tríceps en polea": {"category": "TRICEPS_EXTENSION", "exerciseName": "CABLE_TRICEP_PUSH_DOWN"},
    "Press francés": {"category": "TRICEPS_EXTENSION", "exerciseName": "DUMBBELL_LYING_TRICEPS_EXTENSION"},
    "Patada de tríceps": {"category": "TRICEPS_EXTENSION", "exerciseName": "DUMBBELL_KICK_BACK"},

    # === ABDOMINALES / SIT_UP ===
    "Sit-ups": {"category": "SIT_UP", "exerciseName": "SIT_UP"},
    "Sit-ups con mancuernas": {"category": "SIT_UP", "exerciseName": "WEIGHTED_SIT_UP"},
    "Sit-ups en máquina": {"category": "SIT_UP", "exerciseName": "MACHINE_SIT_UP"},
    "Elección de piernas": {"category": "LEG_RAISE", "exerciseName": "LEG_RAISE"},
    "Elevación de piernas colgado": {"category": "LEG_RAISE", "exerciseName": "HANGING_LEG_RAISE"},
    "Elevación de piernas en banco": {"category": "LEG_RAISE", "exerciseName": "LYING_LEG_RAISE"},

    # === CARDIO ===
    "Burpees": {"category": "PLYO", "exerciseName": "BURPEE"},
    "Saltos al cajón": {"category": "PLYO", "exerciseName": "BOX_JUMP"},
    "Saltos con comba": {"category": "PLYO", "exerciseName": "JUMP_ROPE"},
    "Jumping jacks": {"category": "WARM_UP", "exerciseName": "JUMPING_JACK"},
    "Mountain climbers": {"category": "CORE", "exerciseName": "MOUNTAIN_CLIMBER"},
    "Escaladores": {"category": "CORE", "exerciseName": "MOUNTAIN_CLIMBER"},
    "Escalador cruzado": {"category": "PLANK", "exerciseName": "CROSS_BODY_MOUNTAIN_CLIMBER"},
    "Sprints": {"category": "RUN", "exerciseName": "SPRINT"},

    # === OLÍMPICOS / OLYMPIC_LIFT ===
    "Clean and jerk": {"category": "OLYMPIC_LIFT", "exerciseName": "CLEAN_AND_JERK"},
    "Snatch": {"category": "OLYMPIC_LIFT", "exerciseName": "SNATCH"},
    "Power clean": {"category": "OLYMPIC_LIFT", "exerciseName": "POWER_CLEAN"},
    "Hang clean": {"category": "OLYMPIC_LIFT", "exerciseName": "HANG_CLEAN"},
    "Push press": {"category": "OLYMPIC_LIFT", "exerciseName": "PUSH_PRESS"},

    # === CUERPO COMPLETO / TOTAL_BODY ===
    "Thrusters": {"category": "TOTAL_BODY", "exerciseName": "THRUSTER"},
    "Turkish get-up": {"category": "TOTAL_BODY", "exerciseName": "TURKISH_GET_UP"},
    "Clean and press": {"category": "TOTAL_BODY", "exerciseName": "DUMBBELL_CLEAN_AND_PRESS"},
    "Man maker": {"category": "TOTAL_BODY", "exerciseName": "MAN_MAKER"},

    # === FARMER / CARRY ===
    "Farmer walk": {"category": "CARRY", "exerciseName": "FARMERS_WALK"},
    "Cargas": {"category": "CARRY", "exerciseName": "FARMERS_WALK"},
    "Paseo del granjero": {"category": "CARRY", "exerciseName": "FARMERS_WALK"},

    # === APERTURAS / FLYE ===
    "Aperturas": {"category": "FLYE", "exerciseName": "DUMBBELL_FLYE"},
    "Aperturas con mancuernas": {"category": "FLYE", "exerciseName": "DUMBBELL_FLYE"},
    "Aperturas con cable": {"category": "FLYE", "exerciseName": "CABLE_FLYE"},
    "Aperturas en máquina": {"category": "FLYE", "exerciseName": "MACHINE_FLYE"},
    "Aperturas inversas": {"category": "FLYE", "exerciseName": "REVERSE_FLYE"},
    "Pájaro": {"category": "FLYE", "exerciseName": "REVERSE_FLYE"},

    # === ENCOGIMIENTOS / SHRUG ===
    "Encogimientos": {"category": "SHRUG", "exerciseName": "SHRUG"},
    "Encogimientos con barra": {"category": "SHRUG", "exerciseName": "BARBELL_SHRUG"},
    "Encogimientos con mancuernas": {"category": "SHRUG", "exerciseName": "DUMBBELL_SHRUG"},

    # === ELEVACIÓN LATERAL / LATERAL_RAISE ===
    "Elevación lateral": {"category": "LATERAL_RAISE", "exerciseName": "DUMBBELL_LATERAL_RAISE"},
    "Elevación lateral con mancuernas": {"category": "LATERAL_RAISE", "exerciseName": "DUMBBELL_LATERAL_RAISE"},
    "Elevación lateral con cable": {"category": "LATERAL_RAISE", "exerciseName": "CABLE_LATERAL_RAISE"},
    "Elevación frontal": {"category": "LATERAL_RAISE", "exerciseName": "DUMBBELL_FRONT_RAISE"},

    # === HIPEREXTENSIONES / HYPEREXTENSION ===
    "Hiperextensión": {"category": "HYPEREXTENSION", "exerciseName": "HYPEREXTENSION"},
    "Hiperextensión lumbar": {"category": "HYPEREXTENSION", "exerciseName": "BACK_EXTENSION"},
    "Extensión de espalda": {"category": "HYPEREXTENSION", "exerciseName": "BACK_EXTENSION"},

    # === KETTLEBELL ===
    "Kettlebell swing": {"category": "OLYMPIC_LIFT", "exerciseName": "KETTLEBELL_SWING"},
    "Swing con kettlebell": {"category": "OLYMPIC_LIFT", "exerciseName": "KETTLEBELL_SWING"},
    "Kettlebell snatch": {"category": "OLYMPIC_LIFT", "exerciseName": "KETTLEBELL_SNATCH"},

    # === CHOP ===
    "Chop": {"category": "CHOP", "exerciseName": "CHOP"},
    "Chop con cable": {"category": "CHOP", "exerciseName": "CABLE_CHOP"},

    # === BANDA / BANDED_EXERCISES ===
    "Face pull": {"category": "ROW", "exerciseName": "FACE_PULL"},
    "Pull apart": {"category": "BANDED_EXERCISES", "exerciseName": "PULL_APART"},
    "Abducción de cadera": {"category": "HIP_STABILITY", "exerciseName": "HIP_ABDUCTION"},
    "Adducción de cadera": {"category": "HIP_STABILITY", "exerciseName": "HIP_ADDUCTION"},
    "Clam shells": {"category": "HIP_STABILITY", "exerciseName": "CLAM_SHELL"},
    "Shell de almeja": {"category": "HIP_STABILITY", "exerciseName": "CLAM_SHELL"},

    # === ESTIRAMIENTOS / WARM_UP ===
    "Estiramiento": {"category": "WARM_UP", "exerciseName": "STRETCH"},
    "Estiramiento de isquiotibiales": {"category": "WARM_UP", "exerciseName": "HAMSTRING_STRETCH"},
    "Estiramiento de cuádriceps": {"category": "WARM_UP", "exerciseName": "QUAD_STRETCH"},
    "Estiramiento de pecho": {"category": "WARM_UP", "exerciseName": "CHEST_STRETCH"},
    "Estiramiento de hombros": {"category": "WARM_UP", "exerciseName": "SHOULDER_STRETCH"},
    "Rotación de cadera": {"category": "WARM_UP", "exerciseName": "HIP_ROTATION"},
    "Cat cow": {"category": "WARM_UP", "exerciseName": "CAT_COW_STRETCH"},
    "Postura del niño": {"category": "WARM_UP", "exerciseName": "CHILDS_POSE_STRETCH"},
    "Cobra": {"category": "WARM_UP", "exerciseName": "COBRA_STRETCH"},
    "Pájaro perro": {"category": "WARM_UP", "exerciseName": "BIRD_DOG"},
}


def _normalize_text(text: str) -> str:
    """Normalize text for fuzzy matching: lowercase, remove accents."""
    import unicodedata
    text = text.lower().strip()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    return text


# Spanish → English keyword translations for fuzzy matching
_ES_TO_EN_KEYWORDS = {
    'inclinado': 'incline',
    'declinado': 'decline',
    'alternado': 'alternating',
    'sentado': 'seated',
    'de pie': 'standing',
    'con barra': 'barbell',
    'con mancuernas': 'dumbbell',
    'mancuernas': 'dumbbell',
    'en maquina': 'machine',
    'maquina': 'machine',
    'cable': 'cable',
    'banda': 'band',
    'bosu': 'bosu',
    'swiss': 'swiss',
    'pelota': 'ball',
    'una pierna': 'single leg',
    'pierna': 'leg',
    'brazo': 'arm',
    'gemelos': 'calf',
    'cuadriceps': 'quad',
    'isquiotibiales': 'hamstring',
    'gluteos': 'glute',
    'espalda': 'back',
    'pecho': 'chest',
    'hombros': 'shoulder',
    'biceps': 'biceps',
    'triceps': 'triceps',
    'abdominales': 'abs',
    'oblicuos': 'oblique',
    'lumbar': 'lower back',
    'elevacion': 'raise',
    'extensión': 'extension',
    'rumano': 'romanian',
    'sumo': 'sumo',
    'stiff': 'stiff',
    'hexagonal': 'hex',
    'frontal': 'front',
    'hack': 'hack',
    'goblet': 'goblet',
    'pistol': 'pistol',
    'sissy': 'sissy',
    'bulgaro': 'bulgarian',
    'aereo': 'air',
    'box': 'box',
    'con salto': 'jump',
    'isometrico': 'wall',
    'curl': 'curl',
    'press': 'press',
    'remo': 'row',
    'dominada': 'pull',
    'flexion': 'push',
    'fondo': 'dip',
    'zancada': 'lunge',
    'sentadilla': 'squat',
    'plancha': 'plank',
    'peso muerto': 'deadlift',
}


def _extract_keywords(text: str) -> set:
    """Extract meaningful keywords from exercise name, translating Spanish to English."""
    common_words = {'de', 'con', 'en', 'por', 'para', 'el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'the', 'with', 'on', 'at', 'to', 'for', 'and'}
    normalized = _normalize_text(text)
    
    # First try multi-word translations
    for es_phrase, en_phrase in _ES_TO_EN_KEYWORDS.items():
        if es_phrase in normalized:
            normalized = normalized.replace(es_phrase, en_phrase)
    
    words = normalized.split()
    return {w for w in words if len(w) > 2 and w not in common_words}


def _fuzzy_lookup(ex_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Fuzzy match: find best English exercise matching keywords from Spanish name."""
    keywords = _extract_keywords(ex_name)
    if not keywords:
        return None, None

    best_match = None
    best_score = 0

    for en_name, mapping in _EXERCISE_CATALOG_EN.items():
        en_keywords = _extract_keywords(en_name)
        # Count how many keywords match
        matches = len(keywords & en_keywords)
        if matches > best_score:
            best_score = matches
            best_match = mapping

    # Require at least 2 keyword matches or 1 if only 1 keyword provided
    min_matches = min(2, len(keywords))
    if best_match and best_score >= min_matches:
        return best_match.get("category"), best_match.get("exerciseName")

    return None, None


def _lookup_exercise(ex_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Lookup an exercise name in the Garmin catalog.

    Priority:
      1. Spanish aliases (EXERCISE_CATALOG_ES) - exact match
      2. English names from full catalog (_EXERCISE_CATALOG_EN) - exact match
      3. Fuzzy matching against English catalog (keyword search)
      4. Return (None, None) for fallback

    Returns (category, exerciseName) if found, otherwise (None, None).
    """
    # 1. Try Spanish aliases first (exact)
    mapping = EXERCISE_CATALOG_ES.get(ex_name)
    if mapping:
        return mapping.get("category"), mapping.get("exerciseName")

    # 2. Try English names from full catalog (exact)
    mapping = _EXERCISE_CATALOG_EN.get(ex_name)
    if mapping:
        return mapping.get("category"), mapping.get("exerciseName")

    # 3. Fuzzy matching (e.g., "curl de biceps inclinado" → "Incline Dumbbell Biceps Curl")
    return _fuzzy_lookup(ex_name)


def build_strength_json(
    name: str,
    exercises: List[Dict[str, Any]],
) -> dict:
    """Build the Garmin Connect JSON for a strength workout.

    Each exercise becomes a RepeatGroupDTO with numberOfIterations = sets.
    Inside each repeat group:
      - ExecutableStepDTO (interval) targeting reps (conditionTypeId: 10)
      - ExecutableStepDTO (rest) with configured rest time

    The last rest step of each exercise is skipped via skipLastRestStep.
    """
    steps: List[dict] = []
    step_order = 1

    for ex in exercises:
        ex_name = ex.get("name", "Exercise")
        sets = int(ex.get("sets", 1))
        reps = int(ex.get("reps", 1))
        rest_seconds = int(ex.get("rest_seconds", 60))
        duration_seconds = ex.get("duration_seconds")  # Optional: for time-based exercises (plank, etc.)

        category, exercise_name_key = _lookup_exercise(ex_name)

        nested_steps: List[dict] = []
        nested_order = 1

        # Work step (reps or time target)
        if duration_seconds is not None:
            # Time-based exercise (isometric)
            duration = float(duration_seconds)
            work_step: dict = {
                "type": "ExecutableStepDTO",
                "stepOrder": nested_order,
                "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                "description": f"{ex_name}: {sets}x{int(duration)}s",
                "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True},
                "endConditionValue": duration,
                "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1},
            }
        else:
            # Rep-based exercise
            work_step = {
                "type": "ExecutableStepDTO",
                "stepOrder": nested_order,
                "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                "description": f"{ex_name}: {sets}x{reps}",
                "endCondition": {"conditionTypeId": 10, "conditionTypeKey": "reps", "displayOrder": 10, "displayable": True},
                "endConditionValue": float(reps),
                "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1},
            }
        if category is not None and exercise_name_key is not None:
            work_step["category"] = category
            work_step["exerciseName"] = exercise_name_key
        else:
            work_step["exerciseName"] = ex_name
        nested_steps.append(work_step)
        nested_order += 1

        # Rest step
        nested_steps.append({
            "type": "ExecutableStepDTO",
            "stepOrder": nested_order,
            "stepType": {"stepTypeId": 5, "stepTypeKey": "rest", "displayOrder": 5},
            "description": f"Rest {rest_seconds}s",
            "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time", "displayOrder": 2, "displayable": True},
            "endConditionValue": float(rest_seconds),
            "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target", "displayOrder": 1},
        })

        steps.append({
            "type": "RepeatGroupDTO",
            "stepOrder": step_order,
            "stepType": {"stepTypeId": 6, "stepTypeKey": "repeat", "displayOrder": 6},
            "numberOfIterations": sets,
            "workoutSteps": nested_steps,
            "endCondition": {"conditionTypeId": 7, "conditionTypeKey": "iterations", "displayOrder": 7, "displayable": False},
            "endConditionValue": float(sets),
            "skipLastRestStep": True,
            "smartRepeat": False,
        })
        step_order += 1

    return {
        "workoutName": name,
        "description": f"Strength: {len(exercises)} exercises",
        "sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
        "workoutSegments": [{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
            "workoutSteps": steps,
        }],
    }


# =============================================================================
# MCP TOOLS
# =============================================================================

def register_tools(app):
    """Register all high-level workout builder tools with the MCP server app"""

    @app.tool()
    async def create_walk_run_workout(
        name: str,
        run_seconds: int,
        walk_seconds: int,
        repeats: int,
        warmup_min: int,
        cooldown_min: int,
        hr_zone: str = "Z3",
    ) -> str:
        """Create a walk/run interval workout and upload it to Garmin Connect.

        Builds the internal Garmin JSON automatically and returns the new workout ID.

        Args:
            name: Workout name (e.g. "W3 Mié 2:2")
            run_seconds: Duration of each run interval in seconds
            walk_seconds: Duration of each walk/recovery interval in seconds
            repeats: Number of run/walk repetitions
            warmup_min: Warmup duration in minutes
            cooldown_min: Cooldown duration in minutes
            hr_zone: Target heart-rate zone (Z1-Z5, default Z3)
        """
        try:
            workout_json = build_walk_run_json(
                name=name,
                run_seconds=run_seconds,
                walk_seconds=walk_seconds,
                repeats=repeats,
                warmup_min=warmup_min,
                cooldown_min=cooldown_min,
                hr_zone=hr_zone,
            )
            result = garmin_client.upload_workout(workout_json)

            if isinstance(result, dict):
                curated = {
                    "status": "success",
                    "workout_id": result.get("workoutId"),
                    "name": result.get("workoutName"),
                    "message": "Workout uploaded successfully",
                }
                curated = {k: v for k, v in curated.items() if v is not None}
                return json.dumps(curated, indent=2)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error creating walk/run workout: {str(e)}"

    @app.tool()
    async def create_z2_walk_workout(
        name: str,
        duration_min: int,
        hr_min: int,
        hr_max: int,
    ) -> str:
        """Create a steady Z2 walking workout and upload it to Garmin Connect.

        Args:
            name: Workout name
            duration_min: Main walking block duration in minutes
            hr_min: Minimum heart rate in bpm (used for description; target is Z2)
            hr_max: Maximum heart rate in bpm (used for description; target is Z2)
        """
        try:
            workout_json = build_z2_walk_json(
                name=name,
                duration_min=duration_min,
                hr_min=hr_min,
                hr_max=hr_max,
            )
            result = garmin_client.upload_workout(workout_json)

            if isinstance(result, dict):
                curated = {
                    "status": "success",
                    "workout_id": result.get("workoutId"),
                    "name": result.get("workoutName"),
                    "message": "Workout uploaded successfully",
                }
                curated = {k: v for k, v in curated.items() if v is not None}
                return json.dumps(curated, indent=2)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error creating Z2 walk workout: {str(e)}"

    @app.tool()
    async def create_continuous_run_workout(
        name: str,
        duration_min: int,
        hr_min: int,
        hr_max: int,
        warmup_min: int = 0,
        cooldown_min: int = 0,
    ) -> str:
        """Create a continuous running workout with a custom HR range.

        Args:
            name: Workout name
            duration_min: Main running block duration in minutes
            hr_min: Minimum heart rate in bpm for the custom target range
            hr_max: Maximum heart rate in bpm for the custom target range
            warmup_min: Optional warmup duration in minutes at Z1
            cooldown_min: Optional cooldown duration in minutes at Z1
        """
        try:
            workout_json = build_continuous_run_json(
                name=name,
                duration_min=duration_min,
                hr_min=hr_min,
                hr_max=hr_max,
                warmup_min=warmup_min,
                cooldown_min=cooldown_min,
            )
            result = garmin_client.upload_workout(workout_json)

            if isinstance(result, dict):
                curated = {
                    "status": "success",
                    "workout_id": result.get("workoutId"),
                    "name": result.get("workoutName"),
                    "message": "Workout uploaded successfully",
                }
                curated = {k: v for k, v in curated.items() if v is not None}
                return json.dumps(curated, indent=2)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error creating continuous run workout: {str(e)}"

    @app.tool()
    async def create_strength_workout(
        name: str,
        exercises: List[Dict[str, Any]],
    ) -> str:
        """Create a strength workout and upload it to Garmin Connect.

        Each exercise is mapped to a generic step; unsupported names fallback to
        "Other" with the original name stored in exerciseName.

        Args:
            name: Workout name
            exercises: List of dicts with keys: name, sets, reps, rest_seconds
        """
        try:
            workout_json = build_strength_json(name=name, exercises=exercises)
            result = garmin_client.upload_workout(workout_json)

            if isinstance(result, dict):
                curated = {
                    "status": "success",
                    "workout_id": result.get("workoutId"),
                    "name": result.get("workoutName"),
                    "message": "Workout uploaded successfully",
                }
                curated = {k: v for k, v in curated.items() if v is not None}
                return json.dumps(curated, indent=2)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error creating strength workout: {str(e)}"

    @app.tool()
    async def search_exercises(query: str, limit: int = 20) -> str:
        """Search available exercises in the Garmin Connect catalog.

        Use this to find the exact English name of an exercise before calling
        create_strength_workout. The catalog contains 1500+ exercises.

        Args:
            query: Partial exercise name to search for (e.g., "squat", "bench", "plank").
                   Case-insensitive.
            limit: Maximum number of results to return (default 20).

        Returns:
            JSON list of matching exercises with their exact names.
        """
        try:
            q = query.strip().lower()
            matches = []

            # Search Spanish aliases
            for name_es, mapping in EXERCISE_CATALOG_ES.items():
                if q in name_es.lower():
                    matches.append({
                        "name": name_es,
                        "language": "es",
                        "category": mapping["category"],
                        "exerciseName": mapping["exerciseName"],
                    })

            # Search English catalog
            for name_en, mapping in _EXERCISE_CATALOG_EN.items():
                if q in name_en.lower():
                    matches.append({
                        "name": name_en,
                        "language": "en",
                        "category": mapping["category"],
                        "exerciseName": mapping["exerciseName"],
                    })

            # Deduplicate by exerciseName and sort
            seen = set()
            unique = []
            for m in matches:
                key = (m["category"], m["exerciseName"])
                if key not in seen:
                    seen.add(key)
                    unique.append(m)

            unique = sorted(unique, key=lambda x: x["name"])[:limit]

            return json.dumps({
                "query": query,
                "total_matches": len(unique),
                "exercises": unique,
            }, indent=2)
        except Exception as e:
            return f"Error searching exercises: {str(e)}"

    @app.tool()
    async def schedule_week(week: List[Dict[str, Any]]) -> str:
        """Schedule a list of workouts for the week in a single call.

        Args:
            week: List of dicts with keys: date (YYYY-MM-DD), workout_id (int)
        """
        try:
            results = []
            for item in week:
                calendar_date = item["date"]
                workout_id = int(item["workout_id"])
                url = f"workout-service/schedule/{workout_id}"
                response = garmin_client.garth.post(
                    "connectapi", url, json={"date": calendar_date}
                )
                if response.status_code == 200:
                    results.append({
                        "date": calendar_date,
                        "workout_id": workout_id,
                        "status": "scheduled",
                    })
                else:
                    results.append({
                        "date": calendar_date,
                        "workout_id": workout_id,
                        "status": "failed",
                        "http_status": response.status_code,
                    })
            return json.dumps({
                "status": "complete",
                "scheduled": results,
            }, indent=2)
        except Exception as e:
            return f"Error scheduling week: {str(e)}"

    return app
