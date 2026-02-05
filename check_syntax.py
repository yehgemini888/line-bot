#!/usr/bin/env python3
"""
Quick syntax check for modified files
"""
import sys

def check_syntax():
    files_to_check = [
        'src/usecase/summarize.py',
        'src/infrastructure/line_handler.py',
        'src/infrastructure/telegram_handler.py',
        'src/main.py'
    ]
    
    errors = []
    
    for filepath in files_to_check:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, filepath, 'exec')
            print(f"✅ {filepath} - Syntax OK")
        except SyntaxError as e:
            errors.append(f"❌ {filepath} - Line {e.lineno}: {e.msg}")
            print(f"❌ {filepath} - Syntax Error at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"❌ {filepath} - {str(e)}")
            print(f"❌ {filepath} - Error: {str(e)}")
    
    if errors:
        print(f"\n❌ Found {len(errors)} error(s)")
        return False
    else:
        print(f"\n✅ All files passed syntax check!")
        return True

if __name__ == '__main__':
    success = check_syntax()
    sys.exit(0 if success else 1)
