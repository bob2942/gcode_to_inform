import numpy as np
from pathlib import Path
import datetime
import sys
from dataclasses  import dataclass
import argparse

#offset der auf alle coordinaten draufaddiert wird. vorallem rotation des tools muss definiert werden (x,y,z,Rx,Ry,Rz,e,f)
offset = np.array([0,0,0,-180,0,-180,0,0])
MAX_INSTRUCTIONS: int = int(9996) #10000 - NOP,END, start und end DOUT sowie const speed mode
#OUTPUT_GROUP: int = 1
#tool des roboters
#TOOL_N: int = 2
#userframe des roboters
#USER_N: int = 1
end_zhop: float = 10
OUTPUT_FOLDER = Path("")#Path("C:/Users/Jonathan/Nextcloud/Documents/IDD_HiWi")
Rx = 180
Ry = 0

@dataclass
class Settings:
    #slicing parameter
    file_name: str = "JOBFILE"
    layer_heigth: float = 3
    extrusion_width: float = 6
    flow: float = 1.0
    flow_to_rpm: float = 0.7#0.743
    #max geschwindigkeit des roboterarms
    max_speed: float = 100 #mm/s
    max_rpm: float = 414
    standart_speed: float = 900 #mm/min
    use_volumetric_e: bool = False
    user_n: int = 1
    tool_n: int = 2
    output_group: int = 1
        #to do
    #set tool
    #set userframe
    #set RX
    #set Ry


@dataclass
class PrintData:
    settings: Settings
    coords: np.ndarray

# funktion zur bestimmung der extruder z-rotation
def get_Rz(x,y,z) -> float:
    x_max = 900
    x_min = 10
    min_Rz = -150
    max_Rz = -90
    x = min(max(x,x_min), x_max)
    Rz = min_Rz + x*(max_Rz-min_Rz)/(x_max-x_min)
    return Rz
 
# extruder geschwindikeit berechnen
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

def get_extrude_speed_vol(coords: np.ndarray, settings: Settings) -> int:

    #distanz berechnen
    dist = np.sqrt( (coords[0,0]-coords[1,0])**2 + (coords[0,1]-coords[1,1])**2 + (coords[0,2]-coords[1,2])**2)
    
    #zeit zum fahren berechnen
    t = dist/min(coords[1,7]/60, settings.max_speed)

    vol_flow = coords[1,6]/t

    # fluss zu extruder RPM
    rpm = vol_flow*settings.flow_to_rpm

    # geschwindigkeits wert für den Arduino berechnen
    speed = rpm*254/settings.max_rpm
    return int(max(0,min(speed,254)))


def get_comandline_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", type=str, help="Gcode input filepath")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-o", "--output", type=Path, help="output folder path", default=OUTPUT_FOLDER)
    return parser.parse_args()

def save_to_inform(path: Path, data: PrintData):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        n = data.coords.shape[0]

        #write Header
        f.write(f'/JOB\n//NAME {path.stem}\n//POS\n///NPOS {n},0,0,0,0,0\n///TOOL {data.settings.tool_n}\n///USER {data.settings.user_n}\n///POSTYPE USER\n///RECTAN\n///RCONF 1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n')
        #write positions
        for i,coord in enumerate(data.coords):
            #get rotation in RZ um keine axenlimits zu erreichen
            coord[5] = get_Rz(coord[0],coord[1],coord[3])
            #override orientation
            coord[4] = Ry
            coord[3] = Rx
            f.write(f'C{i:05}={coord[0]:.3f},{coord[1]:.3f},{coord[2]:.3f},{coord[3]:.4f},{coord[4]:.4f},{coord[5]:.4f}\n')
        f.write(f'//INST\n///DATE {datetime.datetime.now().strftime(("%Y/%m/%d %H:%M"))}\n///ATTR SC,RW,RJ\n///GROUP1 RB1\nNOP\n')
        f.write(f'HPVELON\n') #constant speed

        if data.settings.use_volumetric_e:
            last_speed = -1
            for i in range(len(data.coords)):
                f.write(f'MOVL C{i:05} V={min(data.coords[i,7]/60, data.settings.max_speed):.1f}') 
                

                if i == n-1:
                    f.write('\n')
                    continue

                speed = get_extrude_speed_vol(data.coords[i:i+1], data.settings)
                if speed != last_speed:
                    f.write(f' +DOUT OG#({data.settings.output_group}) {speed} ADJT=0')
                f.write('\n')
        else:
            for i in range(n):
                f.write(f'MOVL C{i:05} V={min(data.coords[i,7]/60, data.settings.max_speed):.1f}') 
                #überprüfen
                if (i == (len(data.coords)-1)) or (data.coords[i+1,6] <= 0 and data.coords[i,6] <= 0):
                    f.write('\n')
                    continue
                elif (data.coords[i,7] != data.coords[i+1,7] and data.coords[i+1,6] > 0) or (data.coords[i,6] == 0 and data.coords[i+1,6] > 0) or i == 0:
                    f.write(f' +DOUT OG#({data.settings.output_group}) {get_extrude_speed(data.coords[i+1,7]/60, data.settings)} ADJT=0')
                elif data.coords[i+1,6] <= 0:
                    f.write(f' +DOUT OG#({data.settings.output_group}) 0 ADJT=0')
                f.write('\n')
        f.write('END\n')

def save_prog(path: Path, coords: np.ndarray, settings: Settings) -> None:
    # berechnen in wie vielen Informdateien aufgeteilt werden muss
    n = (coords.shape[0]//MAX_INSTRUCTIONS)
    r = (coords.shape[0]%MAX_INSTRUCTIONS)
    #pfad zum abspeichern
    path = path.parent / path.stem / path.name
    # abspeichern der Inform dateien mit bewegungen
    for i in range(n):
        save_to_inform(path.parent / (path.stem+"_"+str(i)+path.suffix), coords[i*MAX_INSTRUCTIONS:(i+1)*MAX_INSTRUCTIONS], settings)
    if r > 0:
        save_to_inform(path.parent / (path.stem+"_"+str(n)+path.suffix), coords[n*MAX_INSTRUCTIONS:(n+1)*MAX_INSTRUCTIONS], settings)
        n += 1
    # erstellen der INFORM datei zum aufruf der anderen inform dateien
    with open(path, "w") as f:
        f.write(f'/JOB\n//NAME {path.stem}\n')
        f.write(f'//INST\n///DATE {datetime.datetime.now().strftime(("%Y/%m/%d %H:%M"))}\n///ATTR SC,RW,RJ\n///GROUP1 RB1\nNOP\n')
        f.write(f'DOUT OG#({settings.output_group}) 0\n')
        for i in range(n):
            f.write(f'CALL JOB:{(path.stem+"_"+str(i))}\n')
        f.write(f'DOUT OG#({settings.output_group}) 255\n')
        f.write('END\n')

def parse_gcode(path: Path) -> PrintData:
    column_names = ["X", "Y", "Z", "U", "V", "W", "E", "F"]
    settings = Settings()
    # Einlesen des GCodes
    lines = []
    with open(path, 'r', encoding='UTF-8') as file: 
        lines = file.readlines()
    
    # array initialisieren zum aller anzufahrenden positionen
    coords=np.ndarray([len(lines), len(column_names)], dtype=np.float64)
    
    current_row = np.zeros(len(column_names))
    current_row[-1] = settings.standart_speed
    index = 0
    # jede Zeile einzelnt einlesen
    for i, line in enumerate(lines):

        # GCode befehle und Kommentare trennen 
        [gcode_line, *comment] = line.split(";", maxsplit=1)

        # Gcode befehl und Parameter trennen
        if len(gcode_line) > 1:
            [g_cmd, *param_strs] = gcode_line.split()
        else:
            g_cmd = ""
            param_strs = []

        #versuchen alle Parameter auszulesen und ein Dikonary daraus erstellen    
        try:
            params = {e[0]: float(e[1:]) for e in param_strs}
        except:
            params = {}

        # Bewegungs Befehle raus
        if g_cmd in ["G0", "G1"]:
            for col_id, col_name in enumerate(column_names):

                # vorherige werte über nehmen bis auf beim Extruder werte
                if col_name == "E":
                        current_row[col_id] = params.get(col_name, 0)
                else:
                    current_row[col_id] = params.get(col_name, current_row[col_id])

            # wenn nur neue feedrate gesetzt wird keine positionen abspeichern
            if (len(params) == 1 and "F" in params):
                continue
            # mehrfach anfahren gleicher position nicht mehr fach abspeichern
            if index > 0 and np.array_equal(coords[index-1,:-2], current_row[:-2]) :
                continue

            # neue position abspeichern
            coords[index] = current_row
            index += 1

        #wichtige einstellungen auslesen
        if comment:
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
            # if "layer_height" == print_param.strip():
            #     settings.layer_heigth = float(print_param_val[0].strip())
            # elif "extrusion_width" == print_param.strip():
            #     settings.extrusion_width = float(print_param_val[0].strip())
            # elif "extrusion_multiplier"  == print_param.strip():
            #     settings.flow = float(print_param_val[0].strip())
            # elif "file_name"  == print_param.strip():
            #     settings.file_name = str(print_param_val[0].strip())
            # elif "file_name"  == print_param.strip():
            #     settings.file_name = str(print_param_val[0].strip())

    #end position hinzufügen
    current_row[2] += end_zhop
    coords[index] = current_row
    index += 1
    return PrintData(settings, coords[:index])

def main() -> None:

    args = get_comandline_args()
    INPUT_PATH = Path(args.file_path)
    data = parse_gcode(INPUT_PATH) 
    path = args.output / (data.settings.file_name.upper() + ".JBI") # shift to uppercase
    save_prog(path, data.coords + offset, data.settings)
    if args.verbose:
        print(data.settings)
        input("Press enter")

if __name__ == "__main__":
    main()