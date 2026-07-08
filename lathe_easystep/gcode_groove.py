from __future__ import annotations

from typing import Callable, Dict, List

from .model import Operation


def groove_sub_definition() -> List[str]:
    return [
        "(=== GROOVE CYCLE LIBRARY ===)",
        "o200 sub",
        "  #<Wbase> = #1",
        "  #<mode>  = #2",
        "  #<C>     = #3",
        "  #<camp>  = #4",
        "  #<Fsw>   = #5",
        "  #<cn>    = #6",
        "  o201 if [#<camp> GT 0.0001 AND #<cn> GT 0]",
        "    #<i> = [0]",
        "    o202 while [#<i> LT #<cn>]",
        "      o203 if [#<mode> EQ 0]",
        "        G1 Z[#<C> + #<Wbase> + #<camp>] F[#<Fsw>]",
        "        G1 Z[#<C> + #<Wbase> - #<camp>] F[#<Fsw>]",
        "        G1 Z[#<C> + #<Wbase>]           F[#<Fsw>]",
        "      o203 else",
        "        G1 X[#<C> + #<Wbase> + #<camp>] F[#<Fsw>]",
        "        G1 X[#<C> + #<Wbase> - #<camp>] F[#<Fsw>]",
        "        G1 X[#<C> + #<Wbase>]           F[#<Fsw>]",
        "      o203 endif",
        "      #<i> = [#<i> + 1]",
        "    o202 endwhile",
        "  o201 endif",
        "o200 endsub",
        "",
        "o210 sub",
        "  #<Atgt>  = #1",
        "  #<mode>  = #2",
        "  #<C>     = #3",
        "  #<Astart> = #4",
        "  #<retr>  = #5",
        "  #<sgn>   = #6",
        "  #<Fpl>   = #7",
        "  #<stepW> = #8",
        "  #<omin>  = #9",
        "  #<omax>  = #10",
        "  #<camp>  = #11",
        "  #<Fsw>   = #12",
        "  #<cn>    = #13",
        "",
        "  (Offset order: 0, +stepW, -stepW, +2stepW, -2stepW, ...)",
        "  #<k> = [0]",
        "  o211 while [1]",
        "    o212 if [#<k> EQ 0]",
        "      #<Woff> = [0]",
        "    o212 else",
        "      #<tmp>  = [#<k> + 1]",
        "      #<tmp>  = [#<tmp> / 2]",
        "      #<m>    = [FIX[#<tmp>]]",
        "      #<kmod> = [#<k> MOD 2]",
        "      o213 if [#<kmod> EQ 1]",
        "        #<Woff> = [#<m> * #<stepW>]",
        "      o213 else",
        "        #<Woff> = [0 - #<m> * #<stepW>]",
        "      o213 endif",
        "    o212 endif",
        "",
        "    #<omin_lim> = [#<omin> - 0.0001]",
        "    #<omax_lim> = [#<omax> + 0.0001]",
        "    o214 if [#<Woff> LT #<omin_lim>]",
        "      o211 break",
        "    o214 endif",
        "    o215 if [#<Woff> GT #<omax_lim>]",
        "      o211 break",
        "    o215 endif",
        "",
        "    o216 if [#<mode> EQ 0]",
        "      (radial: width axis Z, plunge axis X)",
        "      G0 X[#<Astart>] Z[#<C> + #<Woff>]",
        "      G1 X[#<Atgt>] F[#<Fpl>]",
        "      o200 call [#<Woff>] [#<mode>] [#<C>] [#<camp>] [#<Fsw>] [#<cn>]",
        "      (retract towards start)",
        "      G1 X[#<Atgt> - #<sgn> * #<retr>] F[#<Fpl>]",
        "      G0 X[#<Astart>]",
        "    o216 else",
        "      (face: width axis X in diameter, plunge axis Z)",
        "      G0 Z[#<Astart>] X[#<C> + #<Woff>]",
        "      G1 Z[#<Atgt>] F[#<Fpl>]",
        "      o200 call [#<Woff>] [#<mode>] [#<C>] [#<camp>] [#<Fsw>] [#<cn>]",
        "      G1 Z[#<Atgt> - #<sgn> * #<retr>] F[#<Fpl>]",
        "      G0 Z[#<Astart>]",
        "    o216 endif",
        "",
        "    #<k> = [#<k> + 1]",
        "    o217 if [#<k> GT 200]",
        "      o211 break",
        "    o217 endif",
        "  o211 endwhile",
        "",
        "o210 endsub",
        "",
        "o220 sub",
        "",
        "  M70",
        "  G90",
        "  G18",
        "",
        "  #<mode>   = [FIX[#1]]",
        "  #<wtool>  = [ABS[#2]]",
        "  #<wnut>   = [ABS[#3]]",
        "  #<C>      = [#4]",
        "  #<Astart> = [#5]",
        "  #<Aend>   = [#6]",
        "  #<stepA>  = [ABS[#7]]",
        "  #<over>   = [ABS[#8]]",
        "  #<retr>   = [ABS[#9]]",
        "  #<Fpl>    = [ABS[#10]]",
        "  #<Fsw>    = [ABS[#11]]",
        "  #<fin>    = [ABS[#12]]",
        "  #<camp>   = [ABS[#13]]",
        "  #<cn>     = [ABS[#14]]",
        "  #<cn>     = [FIX[#<cn>]]",
        "",
        "  (Checks)",
        "  o221 if [#<wtool> LE 0]",
        "    (ABORT, wtool le 0)",
        "  o221 endif",
        "  o222 if [#<wnut> LE 0]",
        "    (ABORT, wnut le 0)",
        "  o222 endif",
        "  o223 if [#<stepA> LE 0]",
        "    (ABORT, stepA le 0)",
        "  o223 endif",
        "  o224 if [#<wtool> GT #<wnut> + 0.0001]",
        "    (ABORT, tool wider than groove)",
        "  o224 endif",
        "",
        "  (Width stepping)",
        "  #<stepW> = [#<wtool> - #<over>]",
        "  o225 if [#<stepW> GT 0.8 * #<wtool>]",
        "    #<stepW> = [0.8 * #<wtool>]",
        "  o225 endif",
        "  o226 if [#<stepW> LE 0.001]",
        "    (ABORT, overlap too large)",
        "  o226 endif",
        "",
        "  #<extra> = [#<wnut> - #<wtool>]",
        "  #<omin>  = [0 - 0.5 * #<extra>]",
        "  #<omax>  = [0.5 * #<extra>]",
        "  o227 if [#<stepW> GT #<omax>]",
        "    #<stepW> = #<omax>",
        "  o227 endif",
        "",
        "  (Direction along plunge axis: from start to end)",
        "  #<sgn> = [1]",
        "  o232 if [#<Aend> LT #<Astart>]",
        "    #<sgn> = [0 - 1]",
        "  o232 endif",
        "",
        "  (Rough target with finish allowance)",
        "  #<Arough> = [#<Aend> - #<sgn> * #<fin>]",
        "",
        "  (Roughing passes up to Arough)",
        "  #<Acur> = [#<Astart>]",
        "  o228 if [#<sgn> * [#<Arough> - #<Astart>] GT 0]",
        "    o229 while [#<sgn> * [#<Acur> - #<Arough>] LT 0]",
        "      #<Anext> = [#<Acur> + #<sgn> * #<stepA>]",
        "      o230 if [#<sgn> * [#<Anext> - #<Arough>] GT 0]",
        "        #<Anext> = [#<Arough>]",
        "      o230 endif",
        "      o210 call [#<Anext>] [#<mode>] [#<C>] [#<Astart>] [#<retr>] [#<sgn>] [#<Fpl>] [#<stepW>] [#<omin>] [#<omax>] [#<camp>] [#<Fsw>] [#<cn>]",
        "      #<Acur> = [#<Anext>]",
        "    o229 endwhile",
        "  o228 endif",
        "",
        "  (Finish pass optional)",
        "  o231 if [#<fin> GT 0.0001]",
        "    o210 call [#<Aend>] [#<mode>] [#<C>] [#<Astart>] [#<retr>] [#<sgn>] [#<Fpl>] [#<stepW>] [#<omin>] [#<omax>] [#<camp>] [#<Fsw>] [#<cn>]",
        "  o231 endif",
        "",
        "  M72",
        "o220 endsub",
        "(=== END GROOVE CYCLE LIBRARY ===)",
    ]


def get_param_float(params: Dict[str, object], keys: List[str], default: float | None = None) -> float | None:
    for key in keys:
        if key in params and params.get(key) not in (None, ""):
            try:
                return float(params.get(key))
            except (TypeError, ValueError):
                continue
    return default


def get_param_int(params: Dict[str, object], keys: List[str], default: int | None = None) -> int | None:
    for key in keys:
        if key in params and params.get(key) not in (None, ""):
            try:
                return int(float(params.get(key)))
            except (TypeError, ValueError):
                continue
    return default


def groove_center_from_ref(base: float, width: float, ref: int) -> float:
    if ref == 1:
        return base + (width / 2.0)
    if ref == 2:
        return base - (width / 2.0)
    return base


def generate_groove_gcode(
    op: Operation,
    settings: Dict[str, object] | None,
    *,
    require_tool: Callable[[Dict[str, object], str], int],
    get_tool_number: Callable[[Dict[str, object]], int],
    append_tool_and_spindle: Callable[[List[str], object | None, object | None, Dict[str, object] | None], None],
    emit_coolant: Callable[[List[str], object], None],
) -> List[str]:
    settings = settings or {}
    require_tool(op.params, "GROOVE")
    lines: List[str] = []
    append_tool_and_spindle(
        lines,
        get_tool_number(op.params),
        op.params.get("spindle"),
        settings,
    )
    emit_coolant(lines, op.params.get("coolant_mode", op.params.get("coolant", False)))
    p = op.params
    safe_z = float(p.get("safe_z", 2.0))
    lage = get_param_int(p, ["lage"], 0) or 0

    mode = get_param_int(p, ["mode", "groove_mode"])
    if mode not in (0, 1):
        mode = 0 if lage in (0, 1) else 1

    wnut = abs(get_param_float(p, ["wnut", "W_nut", "width", "groove_width"], 0.0) or 0.0)
    use_tool_width = bool(p.get("use_tool_width", False))
    wtool = get_param_float(
        p,
        ["wtool", "W_tool", "tool_width", "cutting_width", "groove_cutting_width"],
        None,
    )
    if use_tool_width and wtool is not None:
        wtool = abs(wtool)
    if wtool is None:
        wtool = wnut
    wtool = abs(float(wtool))

    c_val = get_param_float(p, ["C", "c", "center"], None)
    ref = get_param_int(p, ["ref"], 0) or 0
    if c_val is None:
        if mode == 0:
            c_val = groove_center_from_ref(float(p.get("z", 0.0) or 0.0), wnut, ref)
        else:
            c_val = groove_center_from_ref(float(p.get("diameter", 0.0) or 0.0), wnut, ref)

    a_start = get_param_float(p, ["A_start", "Astart", "start"], None)
    if a_start is None:
        if mode == 0:
            a_start = float(p.get("diameter", 0.0) or 0.0)
        else:
            a_start = float(p.get("z", 0.0) or 0.0)

    a_end = get_param_float(p, ["A_end", "Aend", "end"], None)
    if a_end is None:
        depth = abs(float(p.get("depth", 0.0) or 0.0))
        if mode == 0:
            dia_depth = 2.0 * depth
            if lage == 1:
                a_end = a_start + dia_depth
            else:
                a_end = a_start - dia_depth
        else:
            if lage == 3:
                a_end = a_start + depth
            else:
                a_end = a_start - depth

    step_a = abs(get_param_float(p, ["stepA", "step_a", "depth_per_pass", "step"], 0.0) or 0.0)
    if step_a <= 0.0:
        step_a = abs(float(p.get("depth", 0.0) or 0.0))

    overlap = abs(get_param_float(p, ["overlap", "over"], 0.0) or 0.0)
    retr = abs(get_param_float(p, ["retract", "retr"], 0.0) or 0.0)
    f_plunge = abs(get_param_float(p, ["F_plunge", "f_plunge", "plunge_feed", "feed"], 0.0) or 0.0)
    f_sweep = abs(get_param_float(p, ["F_sweep", "f_sweep", "sweep_feed"], f_plunge) or 0.0)
    finish = abs(get_param_float(p, ["finish", "fin"], 0.0) or 0.0)
    chip_amp = abs(get_param_float(p, ["chip_amp", "camp"], 0.0) or 0.0)
    chip_n = int(round(get_param_float(p, ["chip_n", "cn"], 0.0) or 0.0))

    if mode == 0:
        step_a *= 2.0
        retr *= 2.0
        finish *= 2.0

        if lage == 1 and not (a_end > a_start):
            raise ValueError("GROOVE innen: Aend muss groesser als Astart sein (ID + 2*Tiefe).")
        if lage != 1 and not (a_end < a_start):
            raise ValueError("GROOVE aussen: Aend muss kleiner als Astart sein (OD - 2*Tiefe).")

    start_x = a_start if mode == 0 else c_val
    lines.append("(Anfahren vor Groove)")
    lines.append(f"G0 Z{safe_z:.3f}")
    lines.append(f"G0 X{start_x:.3f}")

    def macro_arg(value: float, digits: int = 3) -> str:
        if value < 0:
            return f"[-{abs(value):.{digits}f}]"
        return f"[{value:.{digits}f}]"

    def macro_arg_int(value: int) -> str:
        if value < 0:
            return f"[-{abs(value)}]"
        return f"[{value:d}]"

    lines.append(
        "o220 call "
        f"{macro_arg(float(int(mode)), 0)} "
        f"{macro_arg(wtool, 3)} "
        f"{macro_arg(wnut, 3)} "
        f"{macro_arg(c_val, 3)} "
        f"{macro_arg(a_start, 3)} "
        f"{macro_arg(a_end, 3)} "
        f"{macro_arg(step_a, 3)} "
        f"{macro_arg(overlap, 3)} "
        f"{macro_arg(retr, 3)} "
        f"{macro_arg(f_plunge, 3)} "
        f"{macro_arg(f_sweep, 3)} "
        f"{macro_arg(finish, 3)} "
        f"{macro_arg(chip_amp, 3)} "
        f"{macro_arg_int(chip_n)}"
    )
    return lines
