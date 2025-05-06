to_minutes_ignore = lambda t: (lambda parts: int(parts[0]) * 60 + int(parts[1]) if len(parts) > 2 else None)(t.split(':')) if t else None
to_seconds = lambda t: (lambda parts: int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]) if len(parts) == 3 else None)(t.split(':')) if t else None
min2sec = lambda x: x * 60 if x else x
sec2min = lambda x: x / 60 if x else x
um2nm = lambda x : x * 1000 if x else x
str2int = lambda s: int(s.strip()) if isinstance(s, str) and s.strip().isdigit() else -1
choice = lambda e: e if isinstance(e, bool) else (e.strip() if isinstance(e, str) and e.strip() else None)
to_bool = lambda x: True if x == "Yes" else (False if x == "No" else None)


cams2nomad = {
    "Labeling and Cleaning" :{
        "m_def" : "fabrication_facilities.schema_packages.transform.LabelingCleaning",
		"mapping" : {
		    "wafer_cleaning_rca_required":"",
		    "wafer_label_position":"labeled_face",
		    "wafer_label_name":"wafers_lables",
		    "wafer_cleaning_DI_ultrasound_required":"Ultrasound",
		    "wafer_cleaning_piranha_required":"piranha_cleaning",
		    "wafer_cleaning_dipHF_required":"dip_hf",
		    "wafer_cleaning_rinse_spin__driyer_required":"rinse_and_dry_",
            "recipe_name":"",
		},
		"transformations" : {
            "wafer_cleaning_rca_required":choice,
            "wafer_cleaning_DI_ultrasound_required":choice,
            "wafer_cleaning_piranha_required":choice,
            "wafer_cleaning_dipHF_required":choice,
            "wafer_cleaning_rinse_spin__driyer_required":choice,
		}
	},
    "Stripping" :{
        "m_def" : "fabrication_facilities.schema_packages.remove.Stripping",
		"mapping" : {
		    "stripping_type":"stripping_type",
		    "short_name":"material_to_remove",
		    "duration_target":"duration",
		    "removing_temperature":"temperature",
		    "ultrasound_required":"ultrasaund",
            "recipe_name":"",
		},
		"transformations" : {
   		    "ultrasound_required":choice,
			"duration_target": min2sec,
            # by default only minutes are mapped to nomad, if we want second also, try this:
			#"duration_target": lambda x: x * 60 + step_specific_info["duration_s"] if x else x,
		}
	},
    "Wet Etching" :{
        "m_def" : "fabrication_facilities.schema_packages.remove.WetEtching",    
		"mapping" : {
		    "etching_type":"",
		    "short_name":"material_to_etch",
		    "duration_target":"In_Time",
		    "depth_target":"In_thickness",
		    "duration_measured":"Out_duration",
		    "depth_measured":"Out_thickness",
		    "etching_solution":"etchant_solution",
            "recipe_name":"",  
		},
		"transformations" : {
			"duration_target": to_minutes_ignore,
			"duration_measured": to_minutes_ignore,
		}
	},
    "Coating" :{
        "m_def" : "fabrication_facilities.schema_packages.add.Spin_Coating",    
		"mapping" : {
		    "dewetting_duration":"De_wetting",
		    "dewetting_temperature":"", # const value = 110, see here below
		    "exposure_duration":"Exposure_time",
		    "exposure_required":"exposure",
		    "hdms_required":"hmds",
			"baking_required":"bake",
			"baking_duration":"bake_time",
			"baking_temperature":"bake_temp",
            "exposure_intensity": "lamp_flow",
		    "peb_required":"peb",
		    "peb_duration":"peb_time",
		    "peb_temperature":"peb_temperature",
		    "short_name":"photoresist",
            "recipe_name":"",
		},
		"transformations" : {
			"peb_duration": to_minutes_ignore,
			"baking_duration": to_minutes_ignore,
            "dewetting_temperature": lambda _ : 110,
			"exposure_required":to_bool,
			"hdms_required":choice,
			"baking_required":choice,
			"peb_required":choice,

		}
	},
    "Wet Cleaning" :{
        "m_def" : "fabrication_facilities.schema_packages.remove.WetCleaning",    
		"mapping" : {
		    "removing_solution_proportions":"",
		    "removing_solution":"solution_type",
		    "removing_temperature":"temperature",
		    "removing_duration":"duration",		 
            "recipe_name":"",   
		},
		"transformations" : {}
	},
    "Starting Materials" :{
        "m_def" : "fabrication_facilities.schema_packages.fabrication_utilities.StartingMaterial",    
		"mapping" : {
		    "wafer_diameter":"",
		    "wafer_quantity":"Wafer_n",
		    "wafer_resistivity":"resistivity",
		    "wafer_orientation":"orientation",
		    "wafer_thickness":"thickness",
		    "wafer_surface_finish":"finishing",
		    "wafer_doping":"",
		    "short_name":"type",
		    "manufacturer_name":"manufacture",
		    # CODE?
            # se si aggiunge il 'material' esso matcha con 'short_name', e 'type' va assegnato a 'chemical_formula'
		},
		"transformations" : {
			"wafer_resistivity": str2int,
		}
	},
    "LPCVD deposition" :{
        "m_def" : "fabrication_facilities.schema_packages.add.ICP_CVD",    
		"mapping" : {
		    "short_name":"deposited_material",
		    "job_number":"process_number",
		    "thickness_target":"In_Thikness",
		    "thickness_measured":"Out_Thickness",
		    "duration_measured":"Out_Time",
		    "deposition_rate_obtained":"",
		    "recipe_name":"recipe_name",
		},
		"transformations" : {}
	},
    "Track" :{
        "m_def" : "fabrication_facilities.schema_packages.transform.Track",    
		"mapping" : {
			"dewetting_duration":"DeWetting",
            "dewetting_temperature":"",
            "developing_duration":"Dev",
            "exposure_duration":"Expo",
            "mask_aligner_name":"aligner",
            "alignment_type":"alignment_type",
            "exposure_mask_contact_type":"contact_type",
            "hdms_required":"hmds",
            "exposure_intensity":"lamp_flow",
            "exposure_duration":"",
            "mask_name":"mask_name",
            "mask_set_name":"set_mask_name",
            "short_name":"photoresist",
            "mask_target":"target_mask",
            "thickness_target":"photoresist_thiknes",
            "peb_required":"peb",
            "peb_temperature":"PEB_TEMP",
            "peb_duration":"PEB_TIME",
            "hardbake_required":"hardbake",
            "hardbake_duration":"harbake_time",
            "hardbake_temperature":"hardbake_temp",
            "softbake_temperature":"sftbake_temp",
            "softbake_duration":"softbake_time",
            "softbake_required":"softbake",
            "developing_rinse_spin_dryer_required":"water_rinse_and_spin_dryer",
		    "recipe_name":"",
		},
		"transformations" : {
            "dewetting_temperature": lambda _ : 110,
			"peb_duration": to_minutes_ignore,
			"softbake_temperature": to_minutes_ignore,
			"hardbake_temperature": to_minutes_ignore,
            "hdms_required":choice,
            "peb_required":choice,
            "hardbake_required":choice,
            "softbake_required":choice,
		}
	},
    "Track 2" :{
        "m_def" : "fabrication_facilities.schema_packages.transform.Track",    
		"mapping" : {
			"dewetting_duration":"DeWetting",
            "dewetting_temperature":"",
            "developing_duration":"Dev",
            "exposure_duration":"Expo",
            "mask_aligner_name":"aligner",
            "alignment_type":"alignment_type",
            "exposure_mask_contact_type":"contact_type",
            "hdms_required":"hmds",
            "exposure_intensity":"lamp_flow",
            "exposure_duration":"",
            "mask_name":"mask_name",
            "mask_set_name":"set_mask_name",
            "short_name":"photoresist",
            "mask_target":"target_mask",
            "thickness_target":"photoresist_thiknes",
            "peb_required":"peb",
            "peb_temperature":"PEB_TEMP",
            "peb_duration":"PEB_TIME",
            "hardbake_required":"hardbake",
            "hardbake_duration":"harbake_time",
            "hardbake_temperature":"hardbake_temp",
            "softbake_temperature":"sftbake_temp",
            "softbake_duration":"softbake_time",
            "softbake_required":"softbake",
            "developing_rinse_spin_dryer_required":"water_rinse_and_spin_dryer",
		    "recipe_name":"",
		},
		"transformations" : {
            "dewetting_temperature": lambda _ : 110,
			"peb_duration": to_minutes_ignore,
			"softbake_temperature": to_minutes_ignore,
			"hardbake_temperature": to_minutes_ignore,
            "hdms_required":choice,
            "peb_required":choice,
            "hardbake_required":choice,
            "softbake_required":choice,
		}
	},
    "RIE" :{
        "m_def" : "fabrication_facilities.schema_packages.remove.RIE",    
		"mapping" : {
            "depth_target":"In_depth",
            "duration_target":"In_time",
            "depth_measured":"Out_depth",
            "duration_measured":"Out_duration",
            "short_name":"etched_material",
			"job_number":"process_number",
		    "recipe_name":"recipe",
		    "chamber_pressure":"",
		    "gas_name":"",
		    "etching_rate_obtained":"",
		},
		"transformations" : {}
	},
    "RIE Metal" :{
        "m_def" : "fabrication_facilities.schema_packages.remove.RIE",    
		"mapping" : {
            "depth_target":"required_depth",
            "duration_target":"In_time",
            "depth_measured":"Out_depth",
            "duration_measured":"Out_time",
            "short_name":"material",
			"job_number":"process_number",
		    "recipe_name":"recipe",
		    "chamber_pressure":"",
		    "gas_name":"",
		    "etching_rate_obtained":"",
		},
		"transformations" : {}
	},
    "RIE PlasmaPro" :{
        "m_def" : "fabrication_facilities.schema_packages.remove.RIE",    
		"mapping" : {
            "depth_target":"depth_IN",
            "duration_target":"time_IN",
            "depth_measured":"depth_OUT",
            "duration_measured":"time_OUT",
            "short_name":"etched_material",
			"job_number":"process_number",
		    "recipe_name":"recipe",
		    "chamber_pressure":"",
		    "gas_name":"",
		    "etching_rate_obtained":"",
		},
		"transformations" : {
            "depth_target":um2nm,
            "depth_measured":um2nm,
            "duration_target":to_seconds,
            "duration_measured":to_seconds,
		}
	},
    "Thermal oxidation" :{
        "m_def" : "fabrication_facilities.schema_packages.transform.ThermalOxidation",    
		"mapping" : {
            "oxidation_type":"oxidation_type",
            "thickness_target":"In_Thickness",
            "thickness_measured":"Out_Thickness",
            "duration_measured":"Out_duration",
            "temperature_final_target":"process_tempere",
			"job_number":"process_number",
		    "recipe_name":"recipe_name",
		    "gas_flow":"",
		    "short_name":"", #gas used
		},
		"transformations" : {
			"duration_measured": min2sec,
		}
	},
    "LTO Densification" :{
        "m_def" : "fabrication_facilities.schema_packages.transform.LTODensification",    
		"mapping" : {
            "densification_type":"lto_densification_type",
            "temperature_target":"densification_temperature",
            "duration_measured":"densification_duration",         
            "thickness_measured":"Out_Thickness",
			"job_number":"process_number",
		    "recipe_name":"recepi_name",
		    "gas_flow":"",
		    "short_name":"", #gas used
		},
		"transformations" : {}
	},
    "Sputtering" :{# non serve
        "m_def" : "fabrication_facilities.schema_packages.add.Sputtering",    
		"mapping" : {
		    "short_name":"material",
            "duration_measured":"duration",         
            "thickness_measured":"thickness",
            "thickness_target":"",
            "chuck_temperature":"temperature",
            "power":"power",
            "delay_between_stack_layers":"waiting_time",
			"job_number":"",
            "duration_target":"",
		    "recipe_name":"",
            "deposition_rate_obtained":"",
		},
		"transformations" : {
            "delay_between_stack_layers": to_minutes_ignore,
		}
	},
    "Sputtering-2" :{
        "m_def" : "fabrication_facilities.schema_packages.add.Sputtering",    
		"mapping" : {
		    "short_name":"deposition_material",
            "duration_measured":"Out_time",         
            "thickness_measured":"Out_thickness",
            "thickness_target":"In_thickness",
            "chuck_temperature":"substrate_temperature",
            "power":"deposition_power_",
            "delay_between_stack_layers":"waiting_time",
			"job_number":"process_number",
            "duration_target":"",
		    "recipe_name":"",
            "deposition_rate_obtained":"",
		},
		"transformations" : {
            "delay_between_stack_layers": to_minutes_ignore,
		}
	},
    "Sputtering KSE" :{
        "m_def" : "fabrication_facilities.schema_packages.add.Sputtering",    
		"mapping" : {
            "power":"dep_power",
		    "short_name":"deposited_material",
            "chuck_temperature":"sub_temp",         
            "thickness_target":"thickness_IN",
            "thickness_measured":"thickness_OUT",
            "duration_target":"time_IN",
            "delay_between_stack_layers":"wait_time",
            
            # "":"dep_step",
            # "":"mov_freq",
            # "":"sample_movimentation",
            
			"job_number":"",
		    "recipe_name":"",
            "deposition_rate_obtained":"",
		},
		"transformations" : {
            "delay_between_stack_layers": to_minutes_ignore,
		}
	},
    "SOG" :{
        "m_def" : "fabrication_facilities.schema_packages.add.SOG",    
		"mapping" : {
		    "short_name":"subatrate_material",
            "thickness_measured":"",
            "thickness_target":"desired_thickness",
            "pre_cleaning":"pre_cleaning",
            "dewetting_duration":"De_wetting",
		    "dewetting_temperature":"", # const value = 110, see here below      
		},
		"transformations" : {
            "dewetting_temperature": lambda _ : 110,
			#"wafer_label_name": lambda x: x.upper() if x else x
		}
	},
    "DRIE" :{
        "m_def" : "fabrication_facilities.schema_packages.remove.DRIE",    
		"mapping" : {
            "short_name":"etched_material",
            "duration_target":"In_duration",
            "duration_measured":"Out_duration",
            "depth_target":"In_Depth",
            "depth_measured":"Out_Deppth",
			"job_number":"process_number",
		    "recipe_name":"drie_type", #?
		    "etching_rate_obtained":"",
		},
		"transformations" : {
            "depth_target" : um2nm,
            "depth_measured" : um2nm,
            "duration_target" : sec2min,
            "duration_measured" : sec2min,
		}
	},
    "DRIE Cobra" :{
        "m_def" : "fabrication_facilities.schema_packages.remove.DRIE",    
		"mapping" : {
            "short_name":"etched_materia",
            "duration_target":"IN_time",
            "duration_measured":"OYT_time",
            "depth_target":"IN_depth",
            "depth_measured":"OUT_depth",
		    "recipe_name":"recipe",
			"job_number":"",
		    "etching_rate_obtained":"",
		},
		"transformations" : {
            "depth_target" : um2nm,
            "depth_measured" : um2nm,
            "duration_target" : sec2min,
            "duration_measured" : sec2min,
		}
	},
    "Silicon Wet Micromachining" :{
        "m_def" : "fabrication_facilities.schema_packages.remove.WetEtching",    
		"mapping" : {
		    "etching_solution":"solution_type",
		    "etching_solution_proportions":"solution_concentration",
		    "duration_target":"estimated_duration",
		    "depth_target":"In_depth",
		    "duration_measured":"Out_duration",
		    "depth_measured":"Out_depth",
            "recipe_name":"",  
		},
		"transformations" : {
            "depth_target" : um2nm,
            "depth_measured" : um2nm,
		}
	},
    "Bonding" :{
        "m_def" : "fabrication_facilities.schema_packages.add.Bonding",    
		"mapping" : {
			"wafer_bonding_type":"bonding_type",
			"job_number":"process_number",
			"alignment_required":"ba6_alignement_required",
			"wafer_stack_1_name":"load_sequence_i_wafer",
			"wafer_stack_2_name":"load_sequence_ii_wafer",
			"wafer_space_required":"spacers",
			"alignment_target_mask_name":"target_mask",
			"alignment_viewfinder_mask_name":"viewfinder_mask",
            "recipe_name":"sb6_recipe",  
			"alignment_max_error":"", # nanometri
			"wafer_bonded_name":"",
		},
		"transformations" : {
            "alignment_required":choice,
            "wafer_space_required":choice,
		}
	},
    "Annealing" :{
        "m_def" : "fabrication_facilities.schema_packages.transform.Annealing",    
		"mapping" : {
			"short_name":"material",
			"temperature_start":"starting_temperature",
			"temperature_final_target":"final_temperature",
			"duration_measured":"duration",
			"gas_formula":"",
			"gas_percentage":"oxigen_",
			"temperature_final_measured":"",
			"temperature_ramp_up_rate":"",
			"temperature_ramp_down_rate":"",
			"job_number":"process_number",
            "recipe_name":"recipe",
		},
		"transformations" : {
            "gas_formula": lambda _ : "O2",
		}
	},
    "Metal Annealing" :{
        "m_def" : "fabrication_facilities.schema_packages.transform.Annealing",    
		"mapping" : {
			"short_name":"annealed_material_",
			"duration_measured":"annealing_duration",
			"temperature_final_target":"annealing_temperature",        
			# "temperature_start":"",
			# "gas_formula":"",
			# "gas_percentage":"",
			# "temperature_final_measured":"",
			# "temperature_ramp_up_rate":"",
			# "temperature_ramp_down_rate":"",
			# "job_number":"process_number",
            # "recipe_name":"recipe",
		},
		"transformations" : {}
	},
    "Observation end Measurement" :{
        "m_def" : "fabrication_facilities.schema_packages.fabrication_utilities.ObservationMeasurements",    
		"mapping" : {
			"activity_type":"activity_type",
			"duration_target":"estimeted_time",
			"short_name":"equipment_used",
			"thickness_measurements":"",
			"electrical_measurements":"",
			"image_name":"",
		},
		"transformations" : {}
	},
    "SOD" :{
        "m_def" : "fabrication_facilities.schema_packages.transform.SOD",    
		"mapping" : {
			"short_name":"sod_tipe",
			"spin_dipHF_duration":"HF",
			"dipping_HFsolution_proportions":"", # cost, vedi sotto
			"water_rinse_required":"Water_Rinse",        
			"spin_dryer_required":"spin_dryer",        
			"peb_duration":"peb_duration",        
			"peb_temperature":"",        
			"spin_frequency":"spinner_speed",        
			"spin_dispensed_volume":"sod_amount",        

		},
		"transformations" : {
            "dipping_HFsolution_proportions": lambda _ : '1:50',
            "peb_duration": to_minutes_ignore,
			"water_rinse_required":choice,        
			"spin_dryer_required":choice,        
		}
	},
    "Dicing" :{
        "m_def" : "fabrication_facilities.schema_packages.transform.Dicing",    
		"mapping" : {
			"blade_name":"dicing_blade",
			"depth_target":"dicing_depth",
			"protective_film_required":"double_dicing_film",
            
            "spindle_frequency":"", # rpm
            "dicing_feed_rate":"", # mm/s
            "depth_step_1":"", # um 
            "depth_step_2":"", # um
            "depth_step_3":"", # um
            "edge_chipping_measured":"", # um
			"recipe_name":"",  # ---------------------  associargli 'dicing_map'?
		},
		"transformations" : {
            "protective_film_required":choice,
		}
	},
    "Doping" :{
        "m_def" : "fabrication_facilities.schema_packages.transform.Doping",    
		"mapping" : {
			"doping_type":"doping_type",
			"duration_target":"duration",
			"temperature_target":"temperature",
			"surface_resistance_measured":"", # ohm/sq
			"job_number":"process_number",
			"recipe_name":"doping_recipe",
		},
		"transformations" : {}
	},
    "Electron Gun KSE" :{
        "m_def" : "fabrication_facilities.schema_packages.add.ElectronGun",    
		"mapping" : {
			"chamber_pressure":"cambi_vac",
			"short_name":"deposited_material",
			"thickness_target":"thickness_IN",
			"thickness_measured":"thickness_OUT",
			"duration_target":"time_IN",
			"spin_frequency ":"rot_speed",
			"gun_voltage_measured":"",
			"gun_current_measured":"",
			"job_number":"process_number",
			"recipe_name":"doping_recipe",
		},
		"transformations" : {}
	},
    "Electron Gun" :{
        "m_def" : "fabrication_facilities.schema_packages.add.ElectronGun",    
		"mapping" : {
			"chamber_pressure":"chamber_vacuum",
			"short_name":"deposited_material",
			"thickness_target":"In_thickness",
			"thickness_measured":"Out_thickness",
			"duration_target":"In_duration",
			"spin_frequency ":"rot_speed",
			"gun_voltage_measured":"",
			"gun_current_measured":"",            
			"job_number":"process_number",
			"recipe_name":"doping_recipe",
		},
		"transformations" : {
			"chamber_pressure": str2int,
		}
	},
}


