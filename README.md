# how to use
```
\<path to python instalation\> \<path to cmd_gcode_to_inform\> \<Gcode Path\> \<optional arguments\>
```


## avalible commands
```
-h
```
show help


```
-v
```
shows all arguments used in the code if available there ar read out off the gcode if not defaults are used

```
-o <path>
```
Specify an outputfolder where the inform files are safed



# gcode parameters

GCode parameters can bes set by adding them to the custom end Gcode in prusaslicer. They follow the pattern
```
; <parameter_name> = <value>
```

## avalible gcode parameters
```
; file_name = <name of the Informfile>
```
sets the name of the created inform files default "JOBFILE".

```
; flow_to_rpm = <value>
```
sets the calculation factor for flowrate in mm^3/s to extruder RPM.

```
; max_speed = <value>
```
sets the maximum allowd movement speed of the robot in mm/s. All movmentspeeds are caped py this value.

```
; max_rpm = <value>
```
maximum rotation speed off the extruder. This value musst be equal with the one set in the Arduino main.cpp file to ensure proper funktion

```
; user_n = <value>
```
set the Yaskawa user frame used for printing

```
; tool_n = <value>
```
sets tool number used
```
; output_group = <value>
```
sets outputgroup used for comunication with the ardino

```
; offset_x = <value>
; offset_y = <value>
; offset_z = <value>
; offset_Rx = <value>
; offset_Ry = <value>
; offset_Rz = <value>
```
adds an offset to all positions for the specified axis.

## gcode parameters set by the slicer
```
; layer_heigth = <value>
```
sets the layerheigth in mm used. This parameter is automaticly set by the slicer.
```
; extrusion_width = <value>
```
sets the extrusionwidth in mm used. This parameter is automaticly set by the slicer.

```
; flow = <value>
```
extrusionmultiplyer

```  
use_volumetric_e = <0/1>
```
sets E-Axis to volumetric.

# arduino code
