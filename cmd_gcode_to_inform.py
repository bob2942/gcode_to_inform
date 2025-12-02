import numpy as np
from pathlib import Path
import datetime
import sys
from dataclasses  import dataclass
import argparse

MAX_INSTRUCTIONS: int = int(9996) #10000 - NOP,END, start und end DOUT sowie const speed mode
#OUTPUT_GROUP: int = 1
#tool des roboters
#TOOL_N: int = 2
#userframe des roboters
#USER_N: int = 1
OUTPUT_FOLDER = Path("")#Path("C:/Users/Jonathan/Nextcloud/Documents/IDD_HiWi")

@dataclass
class Settings:
    #slicing parameter
    file_name: str = "JOBFILE"
    layer_heigth: float = 3
    extrusion_width: float = 6
    flow: float = 1.0
    flow_to_rpm: float = 0.7
    max_speed: float = 100 #mm/s
    max_rpm: float = 414
    use_volumetric_e: bool = False
    user_n: int = 1
    tool_n: int = 2
    output_group: int = 1
    offset_x: float = 0
    offset_y: float = 0
    offset_z: float = 0
    offset_Rx: float = 0
    offset_Ry: float = 0
    offset_Rz: float = 0

@dataclass
class PrintData:
    settings: Settings
    coords: np.ndarray

#change Rz rotation based on position change this funktion how you needed
def get_Rz(x,y,z) -> float:
    x_max = 900
    x_min = 10
    min_Rz = -150
    max_Rz = -90
    x = min(max(x,x_min), x_max)
    Rz = min_Rz + x*(max_Rz-min_Rz)/(x_max-x_min)
    return Rz
 
# calculate extruder speed
def get_extrude_speed(feedrate: float, settings: Settings) -> int:

    #cap to max feedrate
    feedrate = min(feedrate, settings.max_speed)
    # volumetrischen fluss berechnen
    vol_flow = ((0.25*np.pi*settings.layer_heigth**2 + (settings.extrusion_width-settings.layer_heigth)*settings.layer_heigth)*feedrate)*settings.flow
    # fluss zu extruder RPM
    rpm = vol_flow*settings.flow_to_rpm
    #print(f'rpm: {rpm}, flow: {vol_flow}')

    # geschwindigkeits wert für den Arduino berechnen
    speed = rpm*254/settings.max_rpm
    return int(max(0,min(speed,254)))

# calculate extruder speed volumetric e
def get_extrude_speed_vol(coords: np.ndarray, settings: Settings) -> int:
    # caculate distance
    dist = np.sqrt( (coords[0,0]-coords[1,0])**2 + (coords[0,1]-coords[1,1])**2 + (coords[0,2]-coords[1,2])**2)
    
    # calculate time
    t = dist/min(coords[1,7]/60, settings.max_speed)

    try:
        # calculate volumetric flow
        vol_flow = coords[1,6]/t
    except:
        return 0
    
    # flow to rpm
    rpm = vol_flow*settings.flow_to_rpm #*settings.flow

    # calculate 8bit value to controll the exruder
    speed = rpm*254/settings.max_rpm
    return int(max(0,min(speed,254)))

def get_comandline_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", type=str, help="Gcode input filepath")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-o", "--output", type=Path, help="output folder path", default=OUTPUT_FOLDER)
    parser.add_argument("--standart_speed", type=float, help=" movement speed that is used when no speed has been set previosly", default= 900)
    return parser.parse_args()

def save_to_inform(path: Path, coords: np.ndarray, settings: Settings, last_pos : np.ndarray = np.array([0,0,0,0,0,0,0,0])):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        n = coords.shape[0]

        #write Header
        f.write(f'/JOB\n//NAME {path.stem}\n//POS\n///NPOS {n},0,0,0,0,0\n///TOOL {settings.tool_n}\n///USER {settings.user_n}\n///POSTYPE USER\n///RECTAN\n///RCONF 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n')
        #write positions
        for i,coord in enumerate(coords):
            # override Rz rotation based on position maby nedet to reach the hole printvolume
            # uncomend if needet
            #coord[5] =get_Rz(coord[0],coord[1],coord[3])


            f.write(f'C{i:05}={coord[0]:.3f},{coord[1]:.3f},{coord[2]:.3f},{coord[3]:.4f},{coord[4]:.4f},{coord[5]:.4f}\n')
        f.write(f'//INST\n///DATE {datetime.datetime.now().strftime(("%Y/%m/%d %H:%M"))}\n///ATTR SC,RW,RJ\n///GROUP1 RB1\nNOP\n')
        f.write(f'HPVELON\n') #constant speed

        # if using voloumetric e
        if settings.use_volumetric_e:
            last_speed = -1

            #set extruder speed for first move
            if coords[0,6] > 0:
                speed = get_extrude_speed_vol(np.array([last_pos, coords[0,:]]), settings)
                f.write(f'DOUT OG#({settings.output_group}) {speed}\n')
                last_speed = speed
            else:
                f.write(f'DOUT OG#({settings.output_group}) 0\n')

            for i in range(len(coords)):
                # go to position
                f.write(f'MOVL C{i:05} V={min(coords[i,7]/60, settings.max_speed):.1f}') 
                
                # if its the last move dont set new extruder speed
                if i == n-1:
                    f.write('\n')
                    continue

                # calulate extruder speed
                speed = get_extrude_speed_vol(coords[i:i+2], settings)

                # set new extruder speed if it is different from previous
                if speed != last_speed:
                    f.write(f' +DOUT OG#({settings.output_group}) {speed} ADJT=0')
                    last_speed = speed
                f.write('\n')
        else:
            #set speed for first move
            if coords[0,6] > 0:
                f.write(f'DOUT OG#({settings.output_group}) {get_extrude_speed(coords[0,7]/60, settings)}\n')
            else:
                f.write(f'DOUT OG#({settings.output_group}) 0 \n')


            for i in range(n):
                # go to position
                f.write(f'MOVL C{i:05} V={min(coords[i,7]/60, settings.max_speed):.1f}') 
                #überprüfen und kann bestimmt schöner gemacht werden
                # set new extruder speed if needed
                if (i == (len(coords)-1)) or (coords[i+1,6] <= 0 and coords[i,6] <= 0):
                    f.write('\n')
                    continue
                elif (coords[i,7] != coords[i+1,7] and coords[i+1,6] > 0) or (coords[i,6] <= 0 and coords[i+1,6] > 0) or i == 0:
                    f.write(f' +DOUT OG#({settings.output_group}) {get_extrude_speed(coords[i+1,7]/60, settings)} ADJT=0')
                elif coords[i+1,6] <= 0:
                    f.write(f' +DOUT OG#({settings.output_group}) 0 ADJT=0')
                f.write('\n')
        f.write('END\n')

def save_prog(path: Path, coords: np.ndarray, settings: Settings) -> None:
    # calculate how many inform files are needed
    n = (coords.shape[0]//MAX_INSTRUCTIONS)
    r = (coords.shape[0]%MAX_INSTRUCTIONS)

    #safe path
    path = path.parent / path.stem / path.name

    # create and save iform files with moves
    last_pos = coords[0]
    for i in range(n):
        save_to_inform(path.parent / (path.stem+"_"+str(i)+path.suffix), coords[i*MAX_INSTRUCTIONS:(i+1)*MAX_INSTRUCTIONS], settings, last_pos)
        last_pos = coords[(i+1)*MAX_INSTRUCTIONS-1]
    if r > 0:
        save_to_inform(path.parent / (path.stem+"_"+str(n)+path.suffix), coords[n*MAX_INSTRUCTIONS:(n+1)*MAX_INSTRUCTIONS], settings, last_pos)
        n += 1

    # creates main inform file to call previosly created move-inform files
    with open(path, "w") as f:
        f.write(f'/JOB\n//NAME {path.stem}\n')
        f.write(f'//INST\n///DATE {datetime.datetime.now().strftime(("%Y/%m/%d %H:%M"))}\n///ATTR SC,RW,RJ\n///GROUP1 RB1\nNOP\n')
        f.write(f'DOUT OG#({settings.output_group}) 0\n')
        for i in range(n):
            f.write(f'CALL JOB:{(path.stem+"_"+str(i))}\n')

        # set output pins to 255 to disable heaters and stepper motor
        f.write(f'DOUT OG#({settings.output_group}) 255\n')
        f.write('END\n')

def parse_gcode(path: Path, standart_speed: float = 900) -> PrintData:

    #parameters to read in
    column_names = ["X", "Y", "Z", "U", "V", "W", "E", "F"]

    # init variables
    settings = Settings()
    end_zhop: float = 10

    # Read in GCodes
    lines = []
    with open(path, 'r', encoding='UTF-8') as file: 
        lines = file.readlines()
    
    # initilise array to save coordinates
    coords=np.ndarray([len(lines), len(column_names)], dtype=np.float64)
    
    current_row = np.zeros(len(column_names))
    current_row[-1] = standart_speed
    index = 0
    # read GCodeline by line
    for i, line in enumerate(lines):

        # seperate GCode command from commets
        [gcode_line, *comment] = line.split(";", maxsplit=1)

        # split GCode commends from parameters
        if len(gcode_line) > 1:
            [g_cmd, *param_strs] = gcode_line.split()
        else:
            g_cmd = ""
            param_strs = []

        #try to read in Parameters an create a dictonary   
        try:
            params = {e[0]: float(e[1:]) for e in param_strs}
        except:
            params = {}

        # move command
        if g_cmd in ["G0", "G1"]:
            for col_id, col_name in enumerate(column_names):

                # set to previous value if no new value ist given exept for the E axis
                if col_name == "E":
                        current_row[col_id] = params.get(col_name, 0)
                else:
                    current_row[col_id] = params.get(col_name, current_row[col_id])

            # dont save new position if only feedrate changed
            if (len(params) == 1 and "F" in params):
                continue
            # dont save duplicate positions
            if index > 0 and np.array_equal(coords[index-1,:-2], current_row[:-2]) :
                continue

            # save new position
            coords[index] = current_row
            index += 1

        # read importen parameters from the gcode comments
        if comment:
            # split parameter name und value
            [print_param, *print_param_val] = comment[0].split("=", maxsplit=1)
            match print_param.strip():
                case "layer_height":
                    settings.layer_heigth = float(print_param_val[0].strip())
                case "extrusion_width":
                    settings.extrusion_width = float(print_param_val[0].strip())
                case "extrusion_multiplier":
                    settings.flow = float(print_param_val[0].strip())
                case "file_name":
                    settings.file_name = str(print_param_val[0].strip())
                case "flow_to_rpm":
                    settings.flow_to_rpm = float(print_param_val[0].strip())
                case "use_volumetric_e":
                    if int(print_param_val[0].strip()) == 0:
                        settings.use_volumetric_e = False
                    else:
                        settings.use_volumetric_e = True
                case "user_n":
                    settings.user_n = int(print_param_val[0].strip())
                case "tool_n":
                    settings.tool_n = int(print_param_val[0].strip())
                case "output_group":
                    settings.output_group = int(print_param_val[0].strip())
                case "offset_Rx":
                    settings.offset_Rx = float(print_param_val[0].strip())
                case "offset_Ry":
                    settings.offset_Ry = float(print_param_val[0].strip())
                case "offset_Rz":
                    settings.offset_Rz = float(print_param_val[0].strip())
                case "offset_x":
                    settings.offset_x = float(print_param_val[0].strip())
                case "offset_y":
                    settings.offset_y  = float(print_param_val[0].strip())
                case "offset_z":
                    settings.offset_z  = float(print_param_val[0].strip())
                case "end_zhop":
                    end_zhop = float(print_param_val[0].strip())
                case "use_relative_e_distances":
                    if int(print_param_val[0].strip()) == 0:
                        print("enable relative e distance")
                        input("Press Enter")
                        sys.exit(1)
                case "arc_fitting":
                    if print_param_val[0].strip() != "disabled":
                        print("disable arc_fitting")
                        input("Press Enter")
                        sys.exit(1)
           
    #end position hinzufügen
    current_row[2] += end_zhop
    coords[index] = current_row
    index += 1
    return PrintData(settings, coords[:index])

def main() -> None:

    args = get_comandline_args()
    INPUT_PATH = Path(args.file_path)
    data = parse_gcode(INPUT_PATH, args.standart_speed) 
    if args.verbose:
        print(data.settings)
    path = args.output / (data.settings.file_name.upper() + ".JBI") # shift to uppercase
    save_prog(path, data.coords + np.array([data.settings.offset_x, data.settings.offset_y, data.settings.offset_z, data.settings.offset_Rx, data.settings.offset_Ry, data.settings.offset_Rz, 0, 0]), data.settings)
    #if args.verbose:
    #    print(data.settings)
    #    input("Press enter")
    print("file written to ", {path})
    input("Press enter")

if __name__ == "__main__":
    main()