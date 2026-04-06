# Prisoner's Dilemma Implementation Plan

## Phase 1: Game Logic (`game/`)

- [x] **1.1** `game/models.py` ✅
  - `Decision` enum (COOPERATE, BETRAY)
  - `Player` dataclass (id, name, score=0)
  - `RoundResult` dataclass (round_number, decisions dict, payoffs dict)
  - `GameState` dataclass (players list, rounds list, max_rounds=20, current_round=0)
  - `PayoffMatrix` class (CC=3, CD=0, DC=5, DD=1, get_payoff returning single int)

- [ ] **1.2** `game/engine.py`
  - `DecisionMaker` Protocol with async `decide(game_state, player) -> Decision`
  - `GameEngine` class:
    - `__init__(payoff_matrix=PayoffMatrix)` - store matrix reference
    - `play_round(game_state, decision_makers)` - collect decisions, calculate payoffs, return RoundResult
    - `_calculate_payoffs(decisions)` - pairwise interactions, sum for each player
    - `is_game_over(game_state)` - check if game finished

---

## Phase 2: Player Agents (`players/`)

- [ ] **2.1** `players/config/agents.yaml`
  - `player` agent config with role, goal, backstory, llm, max_iter

- [ ] **2.2** `players/player.py`
  - `PlayerDecision` Pydantic model (decision, reasoning)
  - `PlayerAgent` class with agent property and decide() method

---

## Phase 3: Gradio UI (`ui/`)

- [ ] **3.1** `ui/gradio_app.py`
  - Config section: player names, rounds, model selector
  - Game display: live round, decisions, scores, history table
  - Controls: Start, Next Round/Auto-play, Reset
  - Results: leaderboard, win/draw indicators

---

## Phase 4: Entry Points

- [ ] **4.1** `main.py` - Add `run_ui()` function
- [ ] **4.2** `app.py` - Simple launcher script
- [ ] Update `pyproject.toml` with gradio dependency and script entry

---

## Phase 5: Cleanup

- [ ] **5.1** `crew.py` - Simplify or remove
- [ ] **5.2** `pyproject.toml` - Add `gradio>=4.0.0`

---

## Phase 6: Testing

- [x] **6.1** `tests/test_models.py` ✅
- [ ] **6.2** `tests/test_engine.py` - Engine unit tests

---

## Summary

| Phase | Status |
|-------|--------|
| 1.1 | ✅ Done |
| 1.2 | ⬜ Pending |
| 2.1 | ⬜ Pending |
| 2.2 | ⬜ Pending |
| 3.1 | ⬜ Pending |
| 4.1 | ⬜ Pending |
| 4.2 | ⬜ Pending |
| 5.1 | ⬜ Pending |
| 5.2 | ⬜ Pending |
| 6.1 | ✅ Done |
| 6.2 | ⬜ Pending |
