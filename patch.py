import os
import re

dir_path = 'frontend/src'
for root, dirs, files in os.walk(dir_path):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use regex to match fetch('/api and fetch(/api
            new_content = re.sub(r\"fetch\(\s*'/api/v1\", r\"fetch((import.meta.env.VITE_API_URL || '') + '/api/v1\", content)
            new_content = re.sub(r\"fetch\(\s*\/api/v1\", r\"fetch(\${import.meta.env.VITE_API_URL || ''}/api/v1\", new_content)

            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print('Updated ' + path)
