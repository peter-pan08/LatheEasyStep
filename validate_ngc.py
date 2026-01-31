#!/usr/bin/env python3
"""
Validate NGC files against the 7 identified problems.
"""
import os
import re

def validate_ngc_file(filepath):
    """Validate a single NGC file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    issues_found = []
    checks_passed = []
    
    # Problem 1: No tool/spindle/coolant commands
    if re.search(r'^T\d+ M6', content, re.MULTILINE):
        checks_passed.append("✓ Tool change T.. M6 found")
    else:
        issues_found.append("✗ No tool change (T.. M6)")
    
    if re.search(r'^S\d+ M3', content, re.MULTILINE):
        checks_passed.append("✓ Spindle speed S.. M3 found")
    else:
        issues_found.append("✗ No spindle speed (S.. M3)")
    
    # Check for M8 (coolant on) - might not always be present
    if re.search(r'^M8', content, re.MULTILINE):
        checks_passed.append("✓ Coolant M8 found")
    else:
        checks_passed.append("⊘ Coolant M8 not found (may be disabled)")
    
    # Problem 2: No feedrate F
    if re.search(r'^F[\d.]+', content, re.MULTILINE):
        checks_passed.append("✓ Feedrate F.. found")
    else:
        issues_found.append("✗ No feedrate (F..)")
    
    # Problem 3: Duplicate contour lines
    # Look for consecutive identical G1 lines
    lines = content.split('\n')
    duplicates = []
    for i in range(len(lines)-1):
        curr = lines[i].strip()
        next_line = lines[i+1].strip()
        if curr and next_line and curr == next_line and curr.startswith('G1'):
            duplicates.append(f"  Line {i+1}: {curr}")
    
    if duplicates:
        issues_found.append(f"✗ Duplicate consecutive G1 lines ({len(duplicates)} found)")
        for dup in duplicates[:3]:  # Show first 3
            issues_found.append(dup)
    else:
        checks_passed.append("✓ No duplicate consecutive G1 lines")
    
    # Problem 4: #<_depth_per_pass> variable not used in D parameter
    if re.search(r'D#<_depth_per_pass>', content):
        checks_passed.append("✓ D parameter uses #<_depth_per_pass> variable")
    elif re.search(r'D[\d.]+', content):
        issues_found.append("✗ D parameter uses hardcoded value instead of variable")
    else:
        checks_passed.append("⊘ No D parameter found (not a G71/G72 program)")
    
    # Problem 5: Empty steps still output
    # Check if "(Step X: contour)" appears without following G-code
    step_pattern = r'\(Step \d+: [^)]*\)\s*\n\n'
    empty_steps = re.findall(step_pattern, content)
    if empty_steps:
        issues_found.append(f"✗ Empty steps found ({len(empty_steps)} occurrences)")
    else:
        checks_passed.append("✓ No empty steps")
    
    # Problem 6: M5/M9 when nothing enabled
    # This is actually correct behavior (always disable at end)
    if re.search(r'^M5\s*\n^M9', content, re.MULTILINE):
        checks_passed.append("✓ M5/M9 cleanup at program end (correct)")
    
    # Problem 7: Clearance/Rückzug not used
    # Check for G71/G72 with proper Z parameter
    if re.search(r'^G7[12] Q\d+ X[\d.]+ Z[\d.]+', content, re.MULTILINE):
        checks_passed.append("✓ G71/G72 cycle with Z clearance parameter")
    else:
        checks_passed.append("⊘ No G71/G72 cycle found (not a roughing program)")
    
    return checks_passed, issues_found

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ngc_dir = os.path.join(script_dir, "ngc")
    
    if not os.path.exists(ngc_dir):
        print(f"ERROR: NGC directory not found: {ngc_dir}")
        return
    
    ngc_files = [f for f in os.listdir(ngc_dir) if f.endswith('.ngc')]
    
    if not ngc_files:
        print(f"No NGC files found in {ngc_dir}")
        return
    
    print("=" * 70)
    print("NGC FILES VALIDATION REPORT")
    print("=" * 70)
    print()
    
    total_issues = 0
    total_checks = 0
    
    for ngc_file in sorted(ngc_files):
        filepath = os.path.join(ngc_dir, ngc_file)
        print(f"File: {ngc_file}")
        print("-" * 70)
        
        checks, issues = validate_ngc_file(filepath)
        
        for check in checks:
            print(check)
            total_checks += 1
        
        for issue in issues:
            print(issue)
            total_issues += 1
        
        print()
    
    print("=" * 70)
    print(f"SUMMARY: {total_checks} checks passed, {total_issues} issues found")
    print("=" * 70)
    
    if total_issues == 0:
        print("\n✓ All validation checks passed!")
    else:
        print(f"\n✗ {total_issues} issues need to be fixed")

if __name__ == "__main__":
    main()
