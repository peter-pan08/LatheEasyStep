#!/usr/bin/env python3
"""
Regenerate all NGC example files with test data using slicer.
"""
import sys
import os

# Add the lathe_easystep directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slicer import Operation, OpType, generate_program_gcode

def make_program_settings():
    """Create standard program settings for all programs."""
    return {
        "unit": "mm",
        "emit_line_numbers": False,
        "tool_change_pos_x": 150.0,
        "tool_change_pos_z": 300.0,
        "comment_prefix": "(",
        "comment_suffix": ")",
        # Retract positions
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

def regenerate_abdrehen():
    """Regenerate Abdrehen.ngc - Turning with ABSPANEN (parallel Z, move-based)."""
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "Test"}),
        Operation(OpType.CONTOUR, {"name": "main_contour"}, 
                 path=[(0.0, 0.0), (20.0, 0.0), (25.0, -5.0), (25.0, -10.025), (39.985, -54.980), (40.0, -55.0)]),
        Operation(OpType.ABSPANEN, {
            "mode": 0, "tool": 1, "spindle": 1300.0, "feed": 0.15,
            "depth_per_pass": 0.5, "slice_strategy": 1, "pause_enabled": False,
            "pause_distance": 0.0, "contour_name": "main_contour"
        }),
    ]
    
    settings = make_program_settings()
    settings["program_name"] = "Abdrehen"
    gcode_lines = generate_program_gcode(operations, settings)
    
    filepath = os.path.join(os.path.dirname(__file__), "ngc", "Abdrehen.ngc")
    with open(filepath, "w") as f:
        f.write("\n".join(gcode_lines))
    
    print(f"✓ Abdrehen.ngc ({len(gcode_lines)} lines)")
    return len(gcode_lines)

def regenerate_planen():
    """Regenerate Planen.ngc - Facing operation with FACE."""
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "Planen"}),
        Operation(OpType.FACE, {
            "mode": 0,  # 0=rough, 1=finish, 2=both
            "tool": 1, "spindle": 2000.0, "feed": 0.1, "depth_max": 0.05,
            "start_x": 40.0, "end_x": 0.0,  # Required for FACE
            "coolant": True, "comment": "Gesicht planen"
        }, path=[(40.0, 0.0), (0.0, 0.0)]),
    ]
    
    settings = make_program_settings()
    settings["program_name"] = "Planen"
    gcode_lines = generate_program_gcode(operations, settings)
    
    filepath = os.path.join(os.path.dirname(__file__), "ngc", "Planen.ngc")
    with open(filepath, "w") as f:
        f.write("\n".join(gcode_lines))
    
    print(f"✓ Planen.ngc ({len(gcode_lines)} lines)")
    return len(gcode_lines)

def regenerate_bohren():
    """Regenerate Bohren.ngc - Drilling operation."""
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "Bohren"}),
        Operation(OpType.DRILL, {
            "tool": 7, "spindle": 1500.0, "feed": 0.1, "mode": 0,
            "comment": "Loch bohren"
        }, path=[(0.0, 0.0), (0.0, -30.0)]),
    ]
    
    settings = make_program_settings()
    settings["program_name"] = "Bohren"
    gcode_lines = generate_program_gcode(operations, settings)
    
    filepath = os.path.join(os.path.dirname(__file__), "ngc", "Bohren.ngc")
    with open(filepath, "w") as f:
        f.write("\n".join(gcode_lines))
    
    print(f"✓ Bohren.ngc ({len(gcode_lines)} lines)")
    return len(gcode_lines)

def regenerate_gewinde():
    """Regenerate Gewinde.ngc - Threading operation."""
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "Gewinde"}),
        Operation(OpType.THREAD, {
            "tool": 3, "spindle": 500.0, "pitch": 1.5, "length": 30.0,
            "major_diameter": 10.0, "comment": "Gewinde schneiden"
        }, path=[(10.0, 0.0), (10.0, -30.0)]),
    ]
    
    settings = make_program_settings()
    settings["program_name"] = "Gewinde"
    gcode_lines = generate_program_gcode(operations, settings)
    
    filepath = os.path.join(os.path.dirname(__file__), "ngc", "Gewinde.ngc")
    with open(filepath, "w") as f:
        f.write("\n".join(gcode_lines))
    
    print(f"✓ Gewinde.ngc ({len(gcode_lines)} lines)")
    return len(gcode_lines)

def regenerate_einstich():
    """Regenerate Einstich.ngc - Parting operation."""
    operations = [
        Operation(OpType.PROGRAM_HEADER, {"program_name": "Einstich"}),
        Operation(OpType.GROOVE, {
            "tool": 5, "spindle": 800.0, "feed": 0.05,
            "comment": "Einstich"
        }, path=[(0.0, -25.0), (0.0, -26.0)]),
    ]
    
    settings = make_program_settings()
    settings["program_name"] = "Einstich"
    gcode_lines = generate_program_gcode(operations, settings)
    
    filepath = os.path.join(os.path.dirname(__file__), "ngc", "Einstich.ngc")
    with open(filepath, "w") as f:
        f.write("\n".join(gcode_lines))
    
    print(f"✓ Einstich.ngc ({len(gcode_lines)} lines)")
    return len(gcode_lines)

def main():
    try:
        print("Regenerating NGC example files...")
        print()
        
        total_lines = 0
        total_lines += regenerate_abdrehen()
        total_lines += regenerate_planen()
        total_lines += regenerate_bohren()
        total_lines += regenerate_gewinde()
        total_lines += regenerate_einstich()
        
        print()
        print(f"Total: {total_lines} lines of G-code generated in 5 files")
        print()
        print("Next step: Run validate_ngc.py to check for issues")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
