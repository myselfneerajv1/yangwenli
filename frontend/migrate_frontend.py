import os
import re

def migrate_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Skipping {filepath}: {e}")
        return False
        
    original = content
    
    # Currency
    content = content.replace('formatCompactMXN', 'formatCompactINR')
    content = content.replace('MXN', 'INR')
    content = content.replace('mxn', 'inr')
    content = content.replace('amount_mxn', 'amount_inr')
    
    # Taxonomy
    content = content.replace('Ramo', 'Ministry')
    content = content.replace('ramo', 'ministry')
    content = content.replace('Ramos', 'Ministries')
    content = content.replace('ramos', 'ministries')
    
    # Geography
    content = content.replace('Mexico', 'India')
    content = content.replace('MexicoMap', 'IndiaMap')
    content = content.replace('Mexican', 'Indian')
    content = content.replace('mexican', 'indian')
    
    # IDs
    content = content.replace('RFC', 'GSTIN')
    content = content.replace('rfc', 'gstin')

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    src_dir = 'src'
    count = 0
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(('.ts', '.tsx', '.json', '.html')):
                filepath = os.path.join(root, file)
                if migrate_file(filepath):
                    count += 1
                    
    # Rename specifically known files
    old_map = os.path.join(src_dir, 'components', 'geography', 'MexicoMap.tsx')
    new_map = os.path.join(src_dir, 'components', 'geography', 'IndiaMap.tsx')
    if os.path.exists(old_map):
        os.rename(old_map, new_map)
        print("Renamed MexicoMap.tsx to IndiaMap.tsx")

    print(f"Migrated terminology in {count} frontend files.")

if __name__ == '__main__':
    main()
