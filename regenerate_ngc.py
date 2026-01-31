#!/usr/bin/env python3
"""
Regenerate NGC example files with test data.
This script demonstrates how to use the G-code generation pipeline.
"""
import sys
import os

# Add the lathe_easystep directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slicer import Operation, OpType, generate_program_gcode

def regenerate_abdrehen():
    """Regenerate Abdrehen.ngc (turning operation)."""
    
    # Build operations list
    operations = [
        # Program header / stock definition
        Operation(
            OpType.PROGRAM_HEADER,
            {
                "program_name": "Test",
                "xa": 40.0,      # Stock outer diameter
                "xi": 0.0,       # Stock inner diameter
                "za": 0.0,       # Stock front face
                "zi": -55.0,     # Stock back face
                "xra": 40.0,     # Retract diameter
                "xri": 0.0,      # Retract inner
                "zra": 2.0,      # Retract front
                "zri": -60.0,    # Retract back
                "xra_absolute": False,
                "xri_absolute": False,
                "zra_absolute": False,
                "zri_absolute": False,
            }
        ),
        
        # Contour definition (just geometry, no cutting)
        Operation(
            OpType.CONTOUR,
            {
                "name": "main_contour",  # Name so ABSPANEN can reference it
            },
            path=[
                (0.0, 0.0),        # Point 1
                (20.0, 0.0),       # Point 2
                (25.0, -5.0),      # Point 3
                (25.0, -10.025),   # Point 4
                (39.985, -54.980), # Point 5
                (40.0, -55.0),     # Point 6
            ]
        ),
        
        # Abspanen (rough cutting) with parallel Z strategy
        Operation(
            OpType.ABSPANEN,
            {
                "mode": 0,                      # Rough cutting
                "tool": 1,                      # Tool T01
                "spindle": 1300.0,              # Spindle speed 1300 RPM
                "feed": 0.15,                   # Feed 0.15 mm/rev
                "depth_per_pass": 0.5,         # Depth 0.5 mm
                "slice_strategy": 1,            # 1 = parallel Z
                "pause_enabled": False,         # No pause between passes
                "pause_distance": 0.0,          # Pause distance
                "contour_name": "main_contour", # Reference the CONTOUR operation
            }
        ),
    ]
    
    # Program settings
    program_settings = {
        "unit": "mm",
        "program_name": "Test",
        "emit_line_numbers": False,
        "tool_change_pos_x": 150.0,
        "tool_change_pos_z": 300.0,
        "comment_prefix": "(",
        "comment_suffix": ")",
        # Retract positions (required for ABSPANEN)
        "xa": 40.0,      # Stock outer diameter
        "xi": 0.0,       # Stock inner diameter
        "za": 0.0,       # Stock front face
        "zi": -55.0,     # Stock back face
        "xra": 40.0,     # Retract diameter
        "xri": 0.0,      # Retract inner
        "zra": 2.0,      # Retract front
        "zri": -60.0,    # Retract back
        "xra_absolute": False,
        "xri_absolute": False,
        "zra_absolute": False,
        "zri_absolute": False,
        # Tool change position (PHASE A requirement)
        "xt": 150.0,     # Tool change X position
        "zt": 300.0,     # Tool change Z position
        "xt_absolute": True,
        "zt_absolute": True,
    }
    
    # Generate G-code
    gcode_lines = generate_program_gcode(operations, program_settings)
    
    # Write to file
    output_file = os.path.join(os.path.dirname(__file__), "ngc", "Abdrehen.ngc")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w") as f:
        f.write("\n".join(gcode_lines))
    
    print(f"✓ Generated {output_file}")
    return len(gcode_lines)


if __name__ == "__main__":
    try:
        count = regenerate_abdrehen()
        print(f"  {count} lines of G-code generated")
        print("\nValidation notes:")
        print("1. Check for T01 M6 (tool change)")
        print("2. Check for S1300 M3 (spindle speed)")
        print("3. Check for F0.150 (feedrate)")
        print("4. Check for D#<_depth_per_pass> (uses variable, not hardcoded)")
        print("5. Check for no duplicate consecutive coordinates")
        print("6. Check for G71 Q100 X40.000 Z2.000")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
