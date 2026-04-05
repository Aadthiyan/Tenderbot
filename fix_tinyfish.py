import os
import re

def update_tinyfish_config(directory):
    replacements = [
        # Base URL
        (r'TINYFISH_BASE_URL\s*=\s*"https://api\.tinyfish\.ai"', 'TINYFISH_BASE_URL = "https://agent.tinyfish.ai/v1"'),
        # Endpoints
        (r'f"\{TINYFISH_BASE_URL\}/agent"', 'f"{TINYFISH_BASE_URL}/automation/run-sse"'),
        (r'"https://api\.tinyfish\.ai/agent"', '"https://agent.tinyfish.ai/v1/automation/run-sse"'),
        # Headers
        (r'"Authorization":\s*f"Bearer\s*\{settings\.tinyfish_api_key\}"', '"X-API-Key": f"{settings.tinyfish_api_key}"'),
        (r"'Authorization':\s*f'Bearer\s*\{settings\.tinyfish_api_key\}'", "'X-API-Key': f'{settings.tinyfish_api_key}'")
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
    update_tinyfish_config("c:\\Users\\AADHITHAN\\Downloads\\Tenderbot\\backend")
