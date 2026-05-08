import os
import sqlite3
from storage.database import init_db, save_comment, get_patterns, resolve_pattern, DB_PATH


def setup():
    # Use a test DB
    import storage.database as db_module
    db_module.DB_PATH = "test_codereview.db"
    global DB_PATH
    DB_PATH = db_module.DB_PATH
    init_db()


def teardown():
    if os.path.exists("test_codereview.db"):
        os.remove("test_codereview.db")


def test_save_and_get_patterns():
    save_comment("testuser", "test-repo", 1, "security", "Missing auth")
    save_comment("testuser", "test-repo", 2, "security", "Token leak")
    save_comment("testuser", "test-repo", 3, "code_smell", "Long function")
    patterns = get_patterns("testuser")
    categories = [p[0] for p in patterns]
    assert "security" in categories
    security_count = next(count for cat, count in patterns if cat == "security")
    assert security_count == 2
    print(f"✅ Test 1 passed: patterns = {patterns}")


def test_resolve_pattern():
    save_comment("resolveuser", "test-repo", 1, "bad_practice", "Using eval()")
    resolve_pattern("resolveuser", "bad_practice")
    patterns = get_patterns("resolveuser")
    cats = [p[0] for p in patterns]
    assert "bad_practice" not in cats
    print("✅ Test 2 passed: pattern resolved correctly")


def test_no_patterns():
    patterns = get_patterns("brandnewuser")
    assert patterns == []
    print("✅ Test 3 passed: empty patterns for new user")


if __name__ == "__main__":
    setup()
    test_save_and_get_patterns()
    test_resolve_pattern()
    test_no_patterns()
    teardown()
    print("All DB tests passed!")
