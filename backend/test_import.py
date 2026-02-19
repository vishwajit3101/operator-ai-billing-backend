# test_import.py

try:
    from app.database import get_db_connection
    print("SUCCESS: Imported app.database correctly")
    print("get_db_connection function is available")
except ImportError as e:
    print("FAIL: Cannot import")
    print("Error:", e)
except Exception as e:
    print("Other error:", e)