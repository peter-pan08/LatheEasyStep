from __future__ import annotations

UI_TEXT_KEYS = {
    "label_prog_npv": "text.label_prog_npv",
    "label_prog_unit": "text.label_prog_unit",
    "label_prog_shape": "text.label_prog_shape",
    "label_prog_xa": "text.label_prog_xa",
    "label_prog_xi": "text.label_prog_xi",
    "label_prog_za": "text.label_prog_za",
    "label_prog_zi": "text.label_prog_zi",
    "label_prog_zb": "text.label_prog_zb",
    "label_prog_w": "text.label_prog_w",
    "label_prog_l": "text.label_prog_l",
    "label_prog_n": "text.label_prog_n",
    "label_prog_sw": "text.label_prog_sw",
    "label_prog_retract_mode": "text.label_prog_retract_mode",
    "label_prog_xra": "text.label_prog_xra",
    "label_prog_xri": "text.label_prog_xri",
    "label_prog_zra": "text.label_prog_zra",
    "label_prog_zri": "text.label_prog_zri",
    "label_prog_xt": "text.label_prog_xt",
    "label_prog_zt": "text.label_prog_zt",
    "label_prog_sc": "text.label_prog_sc",
    "label_prog_chuck_size": "text.label_prog_chuck_size",
    "label_prog_machine_profile": "text.label_prog_machine_profile",
    "label_prog_chuck_part_type": "text.label_prog_chuck_part_type",
    "label_prog_chuck_grip_mode": "text.label_prog_chuck_grip_mode",
    "label_prog_chuck_profile": "text.label_prog_chuck_profile",
    "label_prog_chuck_x_min": "text.label_prog_chuck_x_min",
    "label_prog_chuck_x_max": "text.label_prog_chuck_x_max",
    "label_prog_chuck_z_limit": "text.label_prog_chuck_z_limit",
    "label_prog_s1": "text.label_prog_s1",
    "label_prog_s3": "text.label_prog_s3",
    "program_has_subspindle": "text.program_has_subspindle",
    "label_prog_name": "text.label_prog_name",
    "label_language": "text.label_language",
    "label_program_spindle_mode": "text.label_program_spindle_mode",
    "label_program_spindle_max_rpm": "text.label_program_spindle_max_rpm",
    "label_program_park_mode": "text.label_program_park_mode",
    "label_program_toolchange_coords": "text.label_program_toolchange_coords",
    "label_program_park_coords": "text.label_program_park_coords",
    "label_program_park_x": "text.label_program_park_x",
    "label_program_park_z": "text.label_program_park_z",
    "label_program_park_sequential": "text.label_program_park_sequential",
    "program_park_sequential": "text.program_park_sequential",
    "label_program_optional_stop_toolchange": "text.label_program_optional_stop_toolchange",
    "program_optional_stop_toolchange": "text.program_optional_stop_toolchange",
    "label_program_preview_warnings": "text.label_program_preview_warnings",
    "program_preview_warnings": "text.program_preview_warnings",
    "label_dirty_status": "text.label_dirty_status",
    "label_face_start_x": "text.label_face_start_x",
    "label_face_start_z": "text.label_face_start_z",
    "label_face_end_x": "text.label_face_end_x",
    "label_face_end_z": "text.label_face_end_z",
    "label_face_mode": "text.label_face_mode",
    "label_face_finish_direction": "text.label_face_finish_direction",
    "label_face_depth_max": "text.label_face_depth_max",
    "label_face_finish_allow_x": "text.label_face_finish_allow_x",
    "label_face_finish_allow_z": "text.label_face_finish_allow_z",
    "label_face_edge_type": "text.label_face_edge_type",
    "label_face_edge_size": "text.label_face_edge_size",
    "label_3": "text.label_3",
    "label_4": "text.label_4",
    "label_face_pause": "text.label_face_pause",
    "face_pause_enabled": "text.face_pause_enabled",
    "label_face_pause_distance": "text.label_face_pause_distance",
    "label_face_spindle": "text.label_face_spindle",
    "label_face_tool": "text.label_face_tool",
    "label_face_coolant": "text.label_face_coolant",
    "face_coolant": "text.face_coolant",
    "label_contour_start_x": "text.label_contour_start_x",
    "label_contour_start_z": "text.label_contour_start_z",
    "label_contour_coord_mode": "text.label_contour_coord_mode",
    "label_contour_name": "text.label_contour_name",
    "contour_add_segment": "text.contour_add_segment",
    "contour_delete_segment": "text.contour_delete_segment",
    "label_contour_edge_type": "text.label_contour_edge_type",
    "label_contour_edge_size": "text.label_contour_edge_size",
    "label_parting_contour": "text.label_parting_contour",
    "label_parting_side": "text.label_parting_side",
    "label_parting_tool": "text.label_parting_tool",
    "label_parting_spindle": "text.label_parting_spindle",
    "label_parting_coolant": "text.label_parting_coolant",
    "label_parting_feed": "text.label_parting_feed",
    "label_parting_depth": "text.label_parting_depth",
    "label_parting_mode": "text.label_parting_mode",
    "label_parting_pause": "text.label_parting_pause",
    "parting_pause_enabled": "text.parting_pause_enabled",
    "label_parting_pause_distance": "text.label_parting_pause_distance",
    "label_parting_slice_strategy": "text.label_parting_slice_strategy",
    "label_parting_slice_step": "text.label_parting_slice_step",
    "label_parting_allow_undercut": "text.label_parting_allow_undercut",
    "parting_allow_undercut": "text.parting_allow_undercut",
    "label_parting_finish_allow_x": "text.label_parting_finish_allow_x",
    "label_parting_finish_allow_z": "text.label_parting_finish_allow_z",
    "label_parting_undercut_mode": "text.label_parting_undercut_mode",
    "label_parting_output_preference": "text.label_parting_output_preference",
    "label_parting_undercut_tool": "text.label_parting_undercut_tool",
    "label_parting_undercut_spindle": "text.label_parting_undercut_spindle",
    "label_parting_undercut_feed": "text.label_parting_undercut_feed",
    "label_parting_optional_stop_before_undercut": "text.label_parting_optional_stop_before_undercut",
    "parting_optional_stop_before_undercut": "text.parting_optional_stop_before_undercut",
    "label_thread_orientation": "text.label_thread_orientation",
    "label_thread_hand": "text.label_thread_hand",
    "label_thread_standard": "text.label_thread_standard",
    "label_thread_tool": "text.label_thread_tool",
    "label_thread_spindle": "text.label_thread_spindle",
    "label_thread_coolant": "text.label_thread_coolant",
    "label_thread_major_diameter": "text.label_thread_major_diameter",
    "label_thread_pitch": "text.label_thread_pitch",
    "label_thread_length": "text.label_thread_length",
    "label_thread_start_z": "text.label_thread_start_z",
    "label_thread_passes": "text.label_thread_passes",
    "label_thread_safe_z": "text.label_thread_safe_z",
    "label_thread_depth": "text.label_thread_depth",
    "label_thread_first_depth": "text.label_thread_first_depth",
    "label_thread_peak_offset": "text.label_thread_peak_offset",
    "label_thread_retract_r": "text.label_thread_retract_r",
    "label_thread_infeed_q": "text.label_thread_infeed_q",
    "label_thread_spring_passes": "text.label_thread_spring_passes",
    "label_thread_e": "text.label_thread_e",
    "label_thread_l": "text.label_thread_l",
    "label_thread_relief_mode": "text.label_thread_relief_mode",
    "label_thread_relief_norm": "text.label_thread_relief_norm",
    "label_thread_optional_stop_before": "text.label_thread_optional_stop_before",
    "thread_optional_stop_before": "text.thread_optional_stop_before",
    "label_groove_tool": "text.label_groove_tool",
    "label_groove_spindle": "text.label_groove_spindle",
    "label_groove_coolant": "text.label_groove_coolant",
    "label_20": "text.label_20",
    "label_21": "text.label_21",
    "label_groove_cutting_width": "text.label_groove_cutting_width",
    "label_22": "text.label_22",
    "label_23": "text.label_23",
    "label_24": "text.label_24",
    "label_25": "text.label_25",
    "label_groove_reduced_feed_start_x": "text.label_groove_reduced_feed_start_x",
    "label_groove_reduced_feed": "text.label_groove_reduced_feed",
    "label_groove_reduced_rpm": "text.label_groove_reduced_rpm",
    "label_groove_step_a": "text.label_groove_step_a",
    "label_groove_overlap": "text.label_groove_overlap",
    "label_groove_retract": "text.label_groove_retract",
    "label_groove_finish": "text.label_groove_finish",
    "label_groove_sweep_feed": "text.label_groove_sweep_feed",
    "label_groove_chip_amp": "text.label_groove_chip_amp",
    "label_groove_chip_n": "text.label_groove_chip_n",
    "label_groove_process_type": "text.label_groove_process_type",
    "label_groove_lage": "text.label_groove_lage",
    "label_groove_ref": "text.label_groove_ref",
    "groove_use_tool_width": "text.groove_use_tool_width",
    "label_drill_tool": "text.label_drill_tool",
    "label_drill_spindle": "text.label_drill_spindle",
    "label_drill_coolant": "text.label_drill_coolant",
    "label_drill_mode": "text.label_drill_mode",
    "label_26": "text.label_26",
    "label_27": "text.label_27",
    "label_28": "text.label_28",
    "label_29": "text.label_29",
    "label_30": "text.label_30",
    "label_31": "text.label_31",
    "label_key_tool": "text.label_key_tool",
    "label_key_coolant": "text.label_key_coolant",
    "label_32": "text.label_32",
    "label_33": "text.label_33",
    "label_key_slot_angle_step": "text.label_key_slot_angle_step",
    "label_34": "text.label_34",
    "label_35": "text.label_35",
    "label_36": "text.label_36",
    "label_37": "text.label_37",
    "label_key_slot_width": "text.label_key_slot_width",
    "label_key_cutting_width": "text.label_key_cutting_width",
    "label_38": "text.label_38",
    "label_39": "text.label_39",
    "label_40": "text.label_40",
    "label_41": "text.label_41",
    "label_42": "text.label_42",
    "label_43": "text.label_43",
    "btnAdd": "text.btnAdd",
    "btnDelete": "text.btnDelete",
    "btnMoveUp": "text.btnMoveUp",
    "btnMoveDown": "text.btnMoveDown",
    "btnNewProgram": "text.btnNewProgram",
    "btnGenerate": "text.btnGenerate",
    "btnSaveChanges": "text.btnSaveChanges",
    "btn_thread_preset": "text.btn_thread_preset",
    "btn_save_step": "text.btn_save_step",
    "btn_load_step": "text.btn_load_step"
}

TAB_TITLE_KEYS = {
    "tabProgram": "tab.tabProgram.title",
    "tabFace": "tab.tabFace.title",
    "tabContour": "tab.tabContour.title",
    "tabParting": "tab.tabParting.title",
    "tabThread": "tab.tabThread.title",
    "tabGroove": "tab.tabGroove.title",
    "tabDrill": "tab.tabDrill.title",
    "tabKeyway": "tab.tabKeyway.title"
}

UI_TOOLTIP_KEYS = {
    "program_language": "tooltip.program_language",
    "program_npv": "tooltip.program_npv",
    "program_unit": "tooltip.program_unit",
    "program_shape": "tooltip.program_shape",
    "program_xa": "tooltip.program_xa",
    "program_xi": "tooltip.program_xi",
    "program_za": "tooltip.program_za",
    "program_zi": "tooltip.program_zi",
    "program_zb": "tooltip.program_zb",
    "program_w": "tooltip.program_w",
    "program_l": "tooltip.program_l",
    "program_n": "tooltip.program_n",
    "program_sw": "tooltip.program_sw",
    "program_retract_mode": "tooltip.program_retract_mode",
    "program_xra": "tooltip.program_xra",
    "program_xri": "tooltip.program_xri",
    "program_zra": "tooltip.program_zra",
    "program_zri": "tooltip.program_zri",
    "program_chuck_x_min": "tooltip.program_chuck_x_min",
    "program_chuck_x_max": "tooltip.program_chuck_x_max",
    "program_chuck_z_limit": "tooltip.program_chuck_z_limit",
    "program_spindle_mode": "tooltip.program_spindle_mode",
    "program_spindle_max_rpm": "tooltip.program_spindle_max_rpm",
    "program_park_mode": "tooltip.program_park_mode",
    "program_toolchange_coords": "tooltip.program_toolchange_coords",
    "program_park_coords": "tooltip.program_park_coords",
    "program_park_x": "tooltip.program_park_x",
    "program_park_z": "tooltip.program_park_z",
    "program_park_sequential": "tooltip.program_park_sequential",
    "program_optional_stop_toolchange": "tooltip.program_optional_stop_toolchange",
    "program_preview_warnings": "tooltip.program_preview_warnings",
    "groove_process_type": "tooltip.groove_process_type",
    "thread_start_z": "tooltip.thread_start_z",
    "thread_length": "tooltip.thread_length",
    "thread_safe_z": "tooltip.thread_safe_z",
    "thread_passes": "tooltip.thread_passes",
    "thread_depth": "tooltip.thread_depth",
    "thread_first_depth": "tooltip.thread_first_depth",
    "thread_peak_offset": "tooltip.thread_peak_offset",
    "thread_retract_r": "tooltip.thread_retract_r",
    "thread_infeed_q": "tooltip.thread_infeed_q",
    "thread_spring_passes": "tooltip.thread_spring_passes",
    "thread_e": "tooltip.thread_e",
    "thread_l": "tooltip.thread_l",
    "parting_slice_strategy": "tooltip.parting_slice_strategy",
    "parting_slice_step": "tooltip.parting_slice_step",
    "parting_allow_undercut": "tooltip.parting_allow_undercut",
    "parting_finish_allow_x": "tooltip.parting_finish_allow_x",
    "parting_finish_allow_z": "tooltip.parting_finish_allow_z",
    "parting_undercut_mode": "tooltip.parting_undercut_mode",
    "parting_output_preference": "tooltip.parting_output_preference",
    "parting_undercut_tool": "tooltip.parting_undercut_tool",
    "parting_undercut_spindle": "tooltip.parting_undercut_spindle",
    "parting_undercut_feed": "tooltip.parting_undercut_feed",
    "parting_optional_stop_before_undercut": "tooltip.parting_optional_stop_before_undercut",
    "groove_depth": "tooltip.groove_depth",
    "groove_step_a": "tooltip.groove_step_a",
    "groove_retract": "tooltip.groove_retract",
    "groove_finish": "tooltip.groove_finish",
    "groove_reduced_feed_start_x": "tooltip.groove_reduced_feed_start_x",
    "groove_reduced_feed": "tooltip.groove_reduced_feed",
    "groove_reduced_rpm": "tooltip.groove_reduced_rpm"
}

COMBO_ITEM_REGISTRY = {
    "program_shape": [
        [
            "cylinder",
            "combo.program_shape.cylinder"
        ],
        [
            "tube",
            "combo.program_shape.tube"
        ],
        [
            "rectangle",
            "combo.program_shape.rectangle"
        ],
        [
            "polygon",
            "combo.program_shape.polygon"
        ]
    ],
    "program_retract_mode": [
        [
            "simple",
            "combo.program_retract_mode.simple"
        ],
        [
            "extended",
            "combo.program_retract_mode.extended"
        ],
        [
            "all",
            "combo.program_retract_mode.all"
        ]
    ],
    "program_chuck_size": [
        [
            "none",
            "combo.program_chuck_size.none"
        ],
        [
            "80",
            "combo.program_chuck_size.80"
        ],
        [
            "100",
            "combo.program_chuck_size.100"
        ],
        [
            "125",
            "combo.program_chuck_size.125"
        ],
        [
            "160",
            "combo.program_chuck_size.160"
        ],
        [
            "200",
            "combo.program_chuck_size.200"
        ],
        [
            "250",
            "combo.program_chuck_size.250"
        ]
    ],
    "program_machine_profile": [
        [
            "manual",
            "combo.program_machine_profile.manual"
        ],
        [
            "shop_125_standard",
            "combo.program_machine_profile.shop_125_standard"
        ],
        [
            "shop_100_soft",
            "combo.program_machine_profile.shop_100_soft"
        ],
        [
            "shop_200_boring",
            "combo.program_machine_profile.shop_200_boring"
        ]
    ],
    "program_chuck_part_type": [
        [
            "solid",
            "combo.program_chuck_part_type.solid"
        ],
        [
            "tube",
            "combo.program_chuck_part_type.tube"
        ]
    ],
    "program_chuck_grip_mode": [
        [
            "external",
            "combo.program_chuck_grip_mode.external"
        ],
        [
            "internal",
            "combo.program_chuck_grip_mode.internal"
        ]
    ],
    "program_chuck_profile": [
        [
            "standard_3jaw",
            "combo.program_chuck_profile.standard_3jaw"
        ],
        [
            "softjaws",
            "combo.program_chuck_profile.softjaws"
        ],
        [
            "boring",
            "combo.program_chuck_profile.boring"
        ]
    ],
    "program_spindle_mode": [
        [
            "fixed",
            "combo.program_spindle_mode.fixed"
        ],
        [
            "css",
            "combo.program_spindle_mode.css"
        ]
    ],
    "program_park_mode": [
        [
            "toolchange",
            "combo.program_park_mode.toolchange"
        ],
        [
            "end_position",
            "combo.program_park_mode.end_position"
        ]
    ],
    "program_toolchange_coords": [
        [
            "work",
            "combo.program_toolchange_coords.work"
        ],
        [
            "machine",
            "combo.program_toolchange_coords.machine"
        ]
    ],
    "program_park_coords": [
        [
            "work",
            "combo.program_park_coords.work"
        ],
        [
            "machine",
            "combo.program_park_coords.machine"
        ]
    ],
    "face_mode": [
        [
            "rough",
            "combo.face_mode.rough"
        ],
        [
            "finish",
            "combo.face_mode.finish"
        ],
        [
            "rough_finish",
            "combo.face_mode.rough_finish"
        ]
    ],
    "face_finish_direction": [
        [
            "outside_in",
            "combo.face_finish_direction.outside_in"
        ],
        [
            "inside_out",
            "combo.face_finish_direction.inside_out"
        ]
    ],
    "face_edge_type": [
        [
            "none",
            "combo.face_edge_type.none"
        ],
        [
            "chamfer",
            "combo.face_edge_type.chamfer"
        ],
        [
            "radius",
            "combo.face_edge_type.radius"
        ]
    ],
    "contour_coord_mode": [
        [
            "absolute",
            "combo.contour_coord_mode.absolute"
        ],
        [
            "incremental",
            "combo.contour_coord_mode.incremental"
        ]
    ],
    "contour_edge_type": [
        [
            "none",
            "combo.contour_edge_type.none"
        ],
        [
            "chamfer",
            "combo.contour_edge_type.chamfer"
        ],
        [
            "radius",
            "combo.contour_edge_type.radius"
        ]
    ],
    "parting_side": [
        [
            "outside",
            "combo.parting_side.outside"
        ],
        [
            "inside",
            "combo.parting_side.inside"
        ]
    ],
    "parting_coolant": [
        [
            "off",
            "combo.parting_coolant.off"
        ],
        [
            "on",
            "combo.parting_coolant.on"
        ]
    ],
    "parting_mode": [
        [
            "rough",
            "combo.parting_mode.rough"
        ],
        [
            "finish",
            "combo.parting_mode.finish"
        ]
    ],
    "parting_slice_strategy": [
        [
            "parallel_x",
            "combo.parting_slice_strategy.parallel_x"
        ],
        [
            "parallel_z",
            "combo.parting_slice_strategy.parallel_z"
        ]
    ],
    "parting_undercut_mode": [
        [
            "ignore",
            "combo.parting_undercut_mode.ignore"
        ],
        [
            "finish_only",
            "combo.parting_undercut_mode.finish_only"
        ],
        [
            "separate",
            "combo.parting_undercut_mode.separate"
        ],
        [
            "full",
            "combo.parting_undercut_mode.full"
        ]
    ],
    "parting_output_preference": [
        [
            "auto",
            "combo.parting_output_preference.auto"
        ],
        [
            "prefer_cycle",
            "combo.parting_output_preference.prefer_cycle"
        ],
        [
            "prefer_explicit",
            "combo.parting_output_preference.prefer_explicit"
        ]
    ],
    "thread_orientation": [
        [
            "external",
            "combo.thread_orientation.external"
        ],
        [
            "internal",
            "combo.thread_orientation.internal"
        ]
    ],
    "thread_hand": [
        [
            "right",
            "combo.thread_hand.right"
        ],
        [
            "left",
            "combo.thread_hand.left"
        ]
    ],
    "thread_relief_mode": [
        [
            "off",
            "combo.thread_relief_mode.off"
        ],
        [
            "suggest_din_relief",
            "combo.thread_relief_mode.suggest_din_relief"
        ]
    ],
    "thread_relief_norm": [
        [
            "din76_a",
            "combo.thread_relief_norm.din76_a"
        ],
        [
            "din76_b",
            "combo.thread_relief_norm.din76_b"
        ],
        [
            "din76_c",
            "combo.thread_relief_norm.din76_c"
        ]
    ],
    "thread_coolant": [
        [
            "off",
            "combo.thread_coolant.off"
        ],
        [
            "on",
            "combo.thread_coolant.on"
        ]
    ],
    "groove_process_type": [
        [
            "groove",
            "combo.groove_process_type.groove"
        ],
        [
            "parting",
            "combo.groove_process_type.parting"
        ]
    ],
    "groove_coolant": [
        [
            "off",
            "combo.groove_coolant.off"
        ],
        [
            "on",
            "combo.groove_coolant.on"
        ]
    ],
    "drill_coolant": [
        [
            "off",
            "combo.drill_coolant.off"
        ],
        [
            "on",
            "combo.drill_coolant.on"
        ]
    ],
    "drill_mode": [
        [
            "g81",
            "combo.drill_mode.g81"
        ],
        [
            "g82",
            "combo.drill_mode.g82"
        ],
        [
            "g83",
            "combo.drill_mode.g83"
        ],
        [
            "g73",
            "combo.drill_mode.g73"
        ],
        [
            "g84",
            "combo.drill_mode.g84"
        ]
    ],
    "key_mode": [
        [
            "axial_z",
            "combo.key_mode.axial_z"
        ],
        [
            "face_x",
            "combo.key_mode.face_x"
        ]
    ],
    "key_radial_side": [
        [
            "outside_shaft",
            "combo.key_radial_side.outside_shaft"
        ],
        [
            "inside_bore",
            "combo.key_radial_side.inside_bore"
        ]
    ],
    "key_coolant": [
        [
            "off",
            "combo.key_coolant.off"
        ],
        [
            "on",
            "combo.key_coolant.on"
        ]
    ],
    "program_language": [
        [
            "de",
            "combo.program_language.de"
        ],
        [
            "en",
            "combo.program_language.en"
        ],
        [
            "es",
            "combo.program_language.es"
        ]
    ]
}


def text_key_for_object(name: str) -> str | None:
    return UI_TEXT_KEYS.get(name)


def tooltip_key_for_object(name: str) -> str | None:
    return UI_TOOLTIP_KEYS.get(name)


def tab_title_key(name: str) -> str | None:
    return TAB_TITLE_KEYS.get(name)


def combo_items(name: str):
    return COMBO_ITEM_REGISTRY.get(name, [])
