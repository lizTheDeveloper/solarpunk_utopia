#!/usr/bin/env python3
"""
Script to fix deprecated datetime.now(datetime.UTC) calls.

Replaces datetime.now(datetime.UTC) with datetime.now(timezone.utc)
and ensures timezone is imported.
"""

import os
import re
from pathlib import Path


def fix_file(filepath: Path) -> bool:
    """
    Fix datetime.now(datetime.UTC) calls in a single file.

    Returns:
        True if file was modified
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Check if file uses datetime.now(datetime.UTC)
        if 'datetime.now(datetime.UTC)' not in content:
            return False

        # Check if timezone is already imported
        has_timezone_import = 'from datetime import' in content and 'timezone' in content
        has_datetime_import = 'from datetime import datetime' in content or 'import datetime' in content

        # Add timezone import if needed
        if not has_timezone_import and 'datetime.now(datetime.UTC)' in content:
            # Find existing datetime import
            import_pattern = r'from datetime import ([^\n]+)'
            match = re.search(import_pattern, content)

            if match:
                # Add timezone to existing import
                imports = match.group(1)
                if 'timezone' not in imports:
                    new_imports = imports.rstrip() + ', timezone'
                    content = content.replace(match.group(0), f'from datetime import {new_imports}')

        # Replace datetime.now(datetime.UTC) with datetime.now(timezone.utc)
        content = content.replace('datetime.now(datetime.UTC)', 'datetime.now(timezone.utc)')

        # Only write if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """Fix all Python files in the project"""
    project_root = Path(__file__).parent
    fixed_count = 0
    total_count = 0

    # Directories to process
    dirs_to_process = [
        'app',
        'mesh_network',
        'discovery_search',
        'file_chunking',
        'valueflows_node',
        'tests'
    ]

    for dir_name in dirs_to_process:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue

        for py_file in dir_path.rglob('*.py'):
            # Skip __pycache__ and venv
            if '__pycache__' in str(py_file) or 'venv' in str(py_file):
                continue

            total_count += 1
            if fix_file(py_file):
                fixed_count += 1
                print(f"✓ Fixed: {py_file.relative_to(project_root)}")

    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} of {total_count} files")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
