# Changelog

All notable changes to this enhanced fork will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-07

### Added

- **Full Garmin Exercise Catalog** — Downloaded and integrated the official Garmin Connect exercise catalog (1500+ exercises across 47 categories). Exercises are automatically mapped to Garmin's internal `category` + `exerciseName` codes so workouts display real names and icons on Garmin watches.
- **`search_exercises` MCP tool** — Search the exercise catalog by partial name. Returns exact English names and Garmin codes, making it easy for AI assistants to find the right exercise.
- **Time-based exercise support** — Exercises can now use `duration_seconds` instead of `reps` for isometric holds (plank, wall sit, etc.). Garmin uses `conditionTypeKey: "time"` with the value in seconds.
- **Bilingual exercise lookup** — Supports both Spanish aliases ("Sentadillas" → SQUAT/SQUAT) and English catalog names ("Barbell Bench Press" → BENCH_PRESS/BARBELL_BENCH_PRESS).
- **Data directory** — Added `src/garmin_mcp/data/garmin_exercises.json` with the complete catalog.

### Enhanced

- **`create_strength_workout`** — Now automatically looks up exercises in the catalog before falling back to generic text. If the exercise name is found, Garmin displays the official name and icon.
- **`build_strength_json`** — Supports optional `duration_seconds` field per exercise for time-based training.

### Technical

- Discovered Garmin's public exercise catalog endpoint: `https://connect.garmin.com/web-data/exercises/Exercises.json`
- Discovered translation endpoint: `https://connect.garmin.com/web-translations/exercise_types/exercise_types.properties`
- Validated exercise codes by creating live workouts via API and verifying Garmin preserves the mappings.

## [0.1.0] - 2026-05-07 (Base from upstream)

### Added

- **High-level workout builders** — 4 MCP tools that construct Garmin Connect JSON internally:
  - `create_walk_run_workout` — Walk/run intervals with HR zone targeting
  - `create_z2_walk_workout` — Steady Z2 walking with absolute HR range
  - `create_strength_workout` — Strength circuit from exercise list
  - `schedule_week` — Bulk-schedule multiple workouts
- Fixed `sportTypeId` mappings via live API probing (strength_training = 5, walking = 12)
- Unit tests with POC snapshot validated against Garmin Connect live API

---

## About This Fork

This is an **enhanced fork** of [Taxuspt/garmin_mcp](https://github.com/Taxuspt/garmin_mcp), originally licensed under MIT. The original project provides excellent base MCP tools for Garmin Connect. This fork adds workout automation features specifically designed for AI assistants and structured training.
