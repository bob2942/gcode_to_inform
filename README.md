# how to use


```
\<path to python instalation\> \<path to cmd_gcode_to_inform\> \<Gcode Path\> \<optional arguments\>
```

to use as a postprocessing script in prusaslicer 
## avalible argumets
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
; use_volumetric_e = <0/1>
```
sets E-Axis to volumetric.

``` 
; use_relative_e_distances = <0/1>
```
if disabled (0) script will therminate and suggest user to turn on this slicing setting. This sript only works with relative E distance.

```
; arc_fitting = <enabled/disabled>
```
arc moves are not suportet only linear moves. if enabled sript will terminate with suggestion to turn off this slicing feature.


# arduino code

## Code Parameters
define the correct values for your setup of STEPS_PER_REVOLUTION and MAX_RPM. Make sure that the MAX_RPM is equal to the parameter in the gcode_to_inform script. ACCEL changes the accelarition off the stepper.
```
#define STEPS_PER_REVOLUTION 3200 // steps/mm bei 16 microsteps und 1:1 Übersetzung
#define ACCEL 5000   // steps/s^2
#define MAX_RPM 414 // max RPM
```

The direction off the stepper movment can be changend by definig the keyword FORWARD or BACKWARD.
```
#define FORWARD
```
or
```
#define BACKWARD
```
## Arduino mega with board
Connect the Outputs from the Robot in the following manner. If you ar not using the PCB the digital Pin number is given.
```
RoboPin -> Arduino Mega Pin/GPIO/Board Pin
O1 -> D22/PA0/O1
O2 -> D23/PA1/O2
O3 -> D24/PA2/O3
O4 -> D25/PA3/O4
O5 -> D26/PA4/O5
O6 -> D27/PA5/O6
O7 -> D28/PA6/O7
O8 -> D29/PA7/O8
```

connect the pins for the stepper driver
```
Arduino Mega Pin/GPIO/Board Pin -> Stepperdriver
D6/PH3/Step -> Step
D5/PE3/Dir -> Dir
D4/PG5/En -> Enable
```

Connect the heater+ pin to relay wich powers the temperatur controllers. At the end of a print or if the value 255 is send the arduino will cut the power to the componets wich are connnected
```
Arduino Mega Pin/GPIO/Board Pin -> Relay
D3/PE5/Heat+ -> Realy+
```

##Arduino Nano

Connect the Outputs from the Robot in the following manner. If you ar not using the PCB the digital Pin number is given.
```
RoboPin -> Arduino Nano Pin/GPIO
O1 -> A0/PC0
O2 -> A1/PC1
O3 -> A2/PC2
O4 -> A3/PC3
O5 -> A4/PC4
O6 -> A5/PC5
O7 -> D3/PD3
O8 -> D4/PD4
```

connect the pins for the stepper driver
```
Arduino Nano Pin/GPIO-> Stepperdriver
D9/PB1 -> Step
D8/PB0 -> Dir
D7/PD7 -> Enable
```

Connect the heater+ pin to relay wich powers the temperatur controllers. At the end of a print or if the value 255 is send the arduino will cut the power to the componets wich are connnected
```
Arduino Nano Pin/GPIO -> Relay
D6/PD6 -> Realy+
```
