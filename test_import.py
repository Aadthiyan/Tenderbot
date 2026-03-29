import sys
try:
    from backend.main import app
    print("Application imported successfully!")
except Exception as e:
    import traceback
    with open('error_clean.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    print("Error written to error_clean.txt")
