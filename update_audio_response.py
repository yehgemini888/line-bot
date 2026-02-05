#!/usr/bin/env python3
"""
Script to add template info display to audio success response
"""

def update_audio_response():
    file_path = 'src/infrastructure/line_handler.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the line with "if page_url:" around line 691
    for i, line in enumerate(lines):
        if i >= 688 and i <= 694 and 'if page_url:' in line and 'audio' in ''.join(lines[max(0, i-20):i]):
            # Insert template info lines before this line
            indent = '        '
            new_lines = [
                f'{indent}# Add template info if available\n',
                f'{indent}if template_used:\n',
                f'{indent}    response += f"\\n\\n🎯 使用模板：{{template_used}}"\n',
                f'{indent}if output_format_used:\n',
                f'{indent}    response += f"\\n📋 輸出格式：{{output_format_used}}"\n',
                '\n',
            ]
            lines[i:i] = new_lines
            break
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Updated audio response builder")

if __name__ == '__main__':
    update_audio_response()
