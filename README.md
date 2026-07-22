# 🃏 L1 Backend Core

![Python](https://img.shields.io/badge/python-3.11-blue)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red)
![Architecture](https://img.shields.io/badge/architecture-layered-blue)
[![License](https://img.shields.io/badge/license-Anthropoi%20License%20v1.0-blue)](./LICENSE)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![Type](https://img.shields.io/badge/type-library-lightgrey)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

Domain models, spaced-repetition scheduling, and frequency-based deck generation for **L1** — a flashcard app for language learning that removes the daily friction of "what should I study today?" by generating decks automatically from real word-frequency rankings.

This package has no CLI, no API, and no UI. It is a library, consumed by [`l1-cli`](https://github.com/angellnx/L1-CLI) today and, later, by a FastAPI service consumed by mobile/desktop clients.

---

## 🛠 Tech Stack

**Current:**
* Python 3.11+
* SQLAlchemy 2.0
* SQLite
* Pytest

**Planned:**
* FastAPI (exposed as a hosted service once the mobile client is built)
* JWT Authentication (multi-user, once there's an API)
* `py-fsrs` (optional upgrade path from SM-2)

---

## ▶️ Running the Project

This is a library, not a standalone app — there's no server to start. To develop against it directly:

```bash
git clone <this-repo-url> l1-backend-core
cd l1-backend-core
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

To consume it from another project (e.g. `l1-cli`), install it in editable mode from a local path or a git URL:

```bash
pip install -e ../l1-backend-core
# or
pip install git+https://github.com/<you>/l1-backend-core.git
```

> Once the API layer lands (see Roadmap), this section will grow a second option: running `uvicorn core_app.main:app --reload` to serve it over HTTP, the same way `l1-cli` runs today as a local import.

---

## 🏗 Architecture

```
Consumer (l1-cli today; a future FastAPI router layer later)
↓
Service Layer
↓
Domain Models
↓
Repository Layer (SQLAlchemy)
↓
Database (SQLite)
```

### Domain Models

Core business entities modeling the study loop, from raw frequency data down to individual scheduling state.

Key decision: **Rich Model over Anemic Model**. `Card` owns its own SM-2 state (`ease_factor`, `interval_days`, `repetitions`, `next_review_at`) and exposes the `is_due` business rule directly. The `SrsService` is the only thing that mutates this state, and it does so *through* the card object, not around it.

Current entities:
* `Language` — ISO 639-1 code, name, whether a frequency list exists for it
* `Card` — front/back pair, owns its live SM-2 scheduling state
* `Deck` — a named collection of cards; `MANUAL` (hand-curated) or `FREQUENCY` (auto-generated from a rank range)
* `ReviewLog` — immutable history of every review (quality, intervals before/after, ease factor after, reaction time). Kept separate from `Card`'s live state deliberately: SM-2 only needs the card's current state, but a future migration to **FSRS** needs the full history — so that data is captured from day one even though SM-2 doesn't use it yet
* `FrequencyProgress` — tracks the last frequency rank already turned into a deck, per language, so deck generation always knows where to continue

### Repository Layer

Each repository converts between domain models and SQLAlchemy ORM models (`l1_core/database/models/orm_models.py`), keeping the domain package free of any database import. `FrequencyRepository` is the one exception — it isn't database-backed at all; it reads static frequency word lists shipped under `l1_core/data/frequency/<code>.txt`.

`WordOccurrenceRepository` is a database-backed counterpart: instead of a shipped static list, it derives word frequency directly from live app data — it counts how many `Card`s use a given word as their `front`, per language, aggregated across every card in the database (no per-user or per-deck scoping). It adds no new table; it's a read-only aggregate query over the existing `cards` table. `count_occurrences(language_code, word)` answers "how many times has this word been added?"; `get_word_counts(language_code)` returns every word ranked by how often it's used, most common first. **Not yet wired into `FrequencyService`** — using it as the deck-generation source directly would be circular on a fresh install (no cards yet to count), so for now it's a standalone building block.

### Service Layer

Contains the core business logic, kept independent of I/O wherever possible.

* **`SrsService`** — pure SM-2 implementation. Takes a `Card` and a quality grade (0–5), mutates the card's scheduling state, and returns a `ReviewLog`. No I/O, no session — trivial to unit test and to eventually swap for FSRS
* **`DeckService`** — manual deck/card creation
* **`FrequencyService`** — generates the next N-card deck from a language's frequency list, advancing `FrequencyProgress` automatically
* **`ReviewService`** — orchestrates a study session: fetches due cards, delegates grading to `SrsService`, persists the updated card and the new `ReviewLog`

---

## 🧠 Core Concept

The system is designed around **automatic deck generation from frequency data**.

Each language's word list is walked in order of raw frequency rank. `FrequencyService` turns the next unclaimed chunk into a new deck, tracking exactly where it left off via `FrequencyProgress` — so every call continues rather than repeats.

```python
deck = service.generate_next_deck("en", count=20)
# -> Deck(name="en-freq-0001-0020", ...), 20 cards created
# next call for "en" continues from rank 21
```

---

## ⚠️ Deliberate MVP Scope: No Auto-Translation, No Grammar-Aware Ordering

`FrequencyService` generates cards with the target-language word as `front`, but leaves `back` as a placeholder (`"(translation pending)"`), and orders cards by raw frequency rank only — no part-of-speech awareness. Both are deliberate scope decisions, not oversights: the goal for this stage is a working single-word flashcard loop in daily use as soon as possible. See Roadmap for where translation and grammatical ordering are planned.

---

## 📦 Frequency Data

The lists shipped under `l1_core/data/frequency/` (`en.txt`, `pt.txt`) are **small placeholder samples (50 words each)**, not full lists. For real use, replace them with a complete frequency list in the same one-word-per-line format, ordered from most to least frequent — for example the ones from [hermitdave/FrequencyWords](https://github.com/hermitdave/FrequencyWords).

---

## 🧪 Testing

The project has a full test suite covering the Service and Repository layers: unit tests with no database involved, and integration tests against an in-memory SQLite database.

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

| Suite | Covers |
|---|---|
| `tests/unit/services/` | `SrsService` tested in isolation (no database) — SM-2 progression, lapses, ease-factor floor, and edge cases |
| `tests/integration/repositories/` | `CardRepository` against an in-memory SQLite database — due-card queries, updates; `WordOccurrenceRepository` — counting, case-insensitivity, language scoping, ranking |
| `tests/integration/services/` | `FrequencyService` end-to-end against the shipped sample data — deck naming, rank continuation, exhaustion |

Tests never touch a real `l1.db` file — everything runs against `sqlite:///:memory:` (see `tests/conftest.py`).

---

## 📂 Project Structure

```
l1-backend-core/
├── l1_core/
│   ├── domain/
│   │   └── models/          # Card, Deck, ReviewLog, Language, FrequencyProgress
│   ├── database/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   │       └── orm_models.py
│   ├── repositories/
│   ├── services/
│   │   ├── srs_service.py
│   │   ├── deck_service.py
│   │   ├── frequency_service.py
│   │   └── review_service.py
│   └── data/frequency/       # word-frequency lists (sample data)
├── tests/
│   ├── unit/services/
│   └── integration/
│       ├── repositories/
│       └── services/
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

* **domain/models** → business entities with encapsulated SM-2 state
* **database/** → SQLAlchemy setup, including session, base, and ORM models
* **repositories** → database-backed persistence, plus the static-file-backed `FrequencyRepository` and the live-aggregate `WordOccurrenceRepository`
* **services** → business logic, kept free of I/O wherever possible (`SrsService`)
* **data/frequency** → shipped word-frequency sample lists, one file per language
* **tests/** → unit and integration tests (see Testing section above)

---

## 🗺 Roadmap

### ✅ Sprint 1 — Core Domain & SRS
* Domain models: `Card`, `Deck`, `ReviewLog`, `Language`, `FrequencyProgress`
* SM-2 algorithm implemented in `SrsService`
* SQLAlchemy persistence layer, repository pattern
* Unit tests for SRS logic, integration tests for repositories

### ✅ Sprint 2 — Frequency-Based Decks
* `FrequencyRepository` reading static word lists
* `FrequencyService` auto-generating decks, tracking progress per language
* Deck naming convention (`<lang>-freq-<start>-<end>`)
* Integration tests covering deck naming, rank continuation, and list exhaustion
* `WordOccurrenceRepository` — live, community-driven word counts derived from `Card` data, as a standalone alternative to the static frequency list (not yet wired into `FrequencyService`)

### 🔲 Sprint 3 — Translation
* Bundle or integrate a bilingual dictionary / translation API to fill `Card.back` automatically instead of leaving a placeholder
* **Deliberately deferred, not part of the MVP.** Cards from `deck generate` ship with a placeholder back; translations are added manually via `l1 deck add-card` for now

### 🔲 Sprint 4 — Full Frequency Datasets
* Replace sample word lists with full lists (hermitdave/FrequencyWords or similar) for all supported languages

### 🔲 Sprint 5 — API Layer
* Extract a FastAPI service on top of this package (`routers/`, `schemas/`, JWT auth), following the same layered pattern already proven in this package
* Needed once the mobile client work begins

### 🔲 Sprint 6 — FSRS Migration (optional)
* Swap `SrsService`'s SM-2 implementation for `py-fsrs`, using the review history already captured in `ReviewLog`

### 🔲 Sprint 7 — Grammatical Frequency Ordering (deferred, exploratory)
* Goal: once decks move beyond single words toward example sentences, raw word-frequency rank alone doesn't guarantee grammatically valid output — the N most frequent words combined naively can produce nonsensical phrases
* Idea: tag each word in a frequency list with its grammatical class (POS tagging, per language), then model the frequency of *transitions* between classes (e.g. article → noun) from a POS-annotated corpus, and use that to validate or drive sentence-level card generation
* Needs a POS tagger per supported language and a reference corpus — meaningfully more scope than plain frequency ranking, and not required for single-word cards. Pushed to the end of the roadmap deliberately: it's the least certain, most exploratory piece of work here

---

## 💡 Why This Project Exists

Learning a language takes daily consistency — and the biggest barrier usually isn't the method, it's the friction of deciding "what do I study today?"

For most learners, that small daily decision is where momentum quietly dies. Motivation is treated as the bottleneck, when in practice it's the constant, low-grade cost of figuring out *what* to review that erodes a habit before it can form.

L1 removes that decision. Based on real usage-frequency rankings, it automatically serves up the next most relevant words to learn, in the order that gives the fastest practical return — so opening the app and starting is the only choice left to make.

Every architectural decision in this project — from keeping `SrsService` pure and side-effect-free to capturing full review history before it's even needed — is made so the study loop stays reliable as it grows from single words today toward sentence-level, grammar-aware cards later.

---

## 📜 License

This project is licensed under the [Anthropoi License v1.0](./LICENSE) — a **source-available** license.

You are free to use, modify, and redistribute this project for personal, non-commercial purposes, provided that:

* This is used by an Individual, not on behalf of or for the benefit of an Organization
* The original copyright notice and license text are preserved
* Any modified versions clearly state the changes made
* No AI Service is integrated into the Software or a Derivative Work — only Local Models are permitted

See the [LICENSE](./LICENSE) file for the full license text.
