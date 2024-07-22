import os

def analyze_structure(directory):
    issues = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                if not os.path.exists(os.path.join(root, '__init__.py')):
                    issues.append(f'Missing __init__.py in {root}')
            if file.endswith('.pyc'):
                if '__pycache__' not in root:
                    issues.append(f'.pyc file outside __pycache__ in {root}')
            if ' ' in file:
                issues.append(f'File with space in name: {os.path.join(root, file)}')
    return issues

if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    issues = analyze_structure(project_root)
    if issues:
        for issue in issues:
            print(issue)
    else:
        print("No issues found")
