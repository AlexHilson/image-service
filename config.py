import iris

max_val = 255
thredds_server = "/Users/niall/Data/PretendTHREDDS/"
img_data_server = "http://ec2-52-16-246-202.eu-west-1.compute.amazonaws.com:9000/molab-3dwx-ds/media/"
source_files = "*.pp"
topog_file = "/Users/niall/Data/ukv/ukv_orog.pp"

anals = {
"default": {"data_constraint": iris.Constraint(model_level_number=lambda v: v.point < 60),
		 "extent": [-13.62, 6.406, 47.924, 60.866],
		 "regrid_shape": [400, 400, 35],
		 "field_width": 4096,
		 "field_height": 4096},
"ukv": {"data_constraint": iris.Constraint(model_level_number=lambda v: v.point < 60),
		 "extent": [-13.62, 6.406, 47.924, 60.866],
		 "regrid_shape": [400, 400, 35],
		 "field_width": 4096,
		 "field_height": 4096}
} # End of models