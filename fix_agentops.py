import os
import re

def update_agentops(directory):
    replacements = [
        # Fix Session.end_session() signature
        (r'end_session\("([^"]+)"\)', r'end_session(end_state="\1")'),
        (r'end_session\("([^"]+)",\s*end_state_reason=(.*)\)', r'end_session(end_state="\1", end_state_reason=\2)'),
        # To clear the ActionEvent deprecation warning if we want, but let's just fix the crash first.
    ]

    modified_files = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    original_content = content
                    for pattern, replacement in replacements:
                        content = re.sub(pattern, replacement, content)

                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"Updated: {filepath}")
                        modified_files += 1

                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

    print(f"Update complete. Modified {modified_files} files.")

if __name__ == "__main__":
    update_agentops("c:\\Users\\AADHITHAN\\Downloads\\Tenderbot\\backend")
