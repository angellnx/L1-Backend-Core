# 🧪 Test Suite

Test suite for L1 Backend Core, covering the Service and Repository layers.
The suite validates SM-2 scheduling logic and persistence — while ensuring the production database is never touched.

---

## ▶️ Running the Tests

Install the required dependencies:
```bash
pip install -e ".[dev]"
```

Run the full test suite:
```bash
pytest tests/ -v
```

---

## 🔒 Test Isolation

The suite is split into unit and integration tests.

**Unit tests**
Located under `tests/unit/services/`. Validate `SrsService`'s SM-2 logic in complete isolation — no repository, no session, no database or external I/O is performed.

**Integration tests**
Located under `tests/integration/repositories/`. Use an in-memory SQLite database provided by the fixtures defined in `tests/conftest.py`.

As a result:
* The production database (`l1.db`) is never modified or accessed
* Every test starts from a clean database state

---

## 📂 Test Structure

```text
tests/
├── conftest.py
│
├── unit/
│   └── services/
│       └── test_srs_service.py
│
└── integration/
    └── repositories/
        └── test_card_repository.py
```

---

## ✅ Coverage

The test suite covers:
* `SrsService` business logic — SM-2 progression, lapses, ease-factor floor, and edge cases
* `CardRepository` persistence using SQLAlchemy — due-card queries and updates
* Domain-to-database mappings

---

## ⚠️ Testing Notes

This suite was written against the layers available at the time: Domain Models, Repositories, and Services. There is currently no Router, Schema, or API layer to test — L1 is a library consumed directly by `l1-cli`, with the FastAPI layer planned for a later sprint.

Once `FrequencyService` lands (see Roadmap, Sprint 2), this structure will grow an `integration/services/` suite covering the deck-generation flow end-to-end. Once the API layer lands (see Roadmap, Sprint 5), it will grow an `integration/api/` suite mirroring the pattern already used for repositories — auth flow, ownership, pagination/filtering, and error handling — the same way it's structured in `A1-Backend-Core`. The testing infrastructure itself won't need to change.

---

## 💡 Testing Philosophy

The test suite follows the same layered architecture as the library:

* **Unit tests** verify SM-2 business rules in complete isolation
* **Repository integration tests** validate persistence using a real in-memory SQLAlchemy database

Together, these layers provide confidence that the library behaves correctly from the Domain Layer down to the Database — and give a solid foundation to extend into the Service integration layer (frequency-based deck generation) and, later, the API layer.
