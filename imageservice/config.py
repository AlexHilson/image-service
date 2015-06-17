import iris

max_val = 255 # maximum data value (i.e. 8 bit uint)
thredds_server = "http://ec2-52-16-245-62.eu-west-1.compute.amazonaws.com:8080/thredds/dodsC/testLab/"
img_data_server = "http://ec2-52-16-246-202.eu-west-1.compute.amazonaws.com:9000/molab-3dwx-ds/media/"
source_files = "*.nc"
topog_file = "/Users/niall/Data/ukv/ukv_orog.pp"
sea_level = 3 # minimum altitude number

# profiles are namespaces which contain setting for different analysis types
profiles = {
"default": {"data_constraint": iris.Constraint(model_level_number=lambda v: v.point < 60),
		 "extent": [-13.62, 6.406, 47.924, 60.866],
		 "regrid_shape": [400, 400, 35],
		 "field_width": 2048,
		 "field_height": 2048},
"ukv": {"data_constraint": iris.Constraint(model_level_number=lambda v: v.point < 60),
		 "extent": [-13.62, 6.406, 47.924, 60.866],
		 "regrid_shape": [400, 400, 35],
		 "field_width": 2048,
		 "field_height": 2048}
} # End of models