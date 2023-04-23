import sympy,sys,math,os,ctypes,msvcrt,random,threading

HEIGHT = os.get_terminal_size().lines-1
WIDTH = os.get_terminal_size().columns

WIN_COL="\033[47m"
WIN_TEXT_COL="\033[30m"
BLACK_BG = "\033[40m"
UNDERLINE = "\033[4m"

HELP="HELP\n\nz: x scale in\nx: x scale out\nc: y scale in\nv: y scale out\nw: move up\ns: move down\na: move left\nd: move right\nr: reset scale\nh: show help\nf: select new function\nq: quit\n\npress any key to continue..."
ENTER_FUNCTION_BOX="Enter function to plot:\n (e.g. 4*sin(x) or 2*x^2 + 4*x + 1)\n ~"
ENTER_VARIABLE_BOX="Enter variable to plot:\n(e.g. x or y)\n ~"
ENTER_NUM_FUNS_BOX="Enter number of functions to plot:\n ~"

FRAME = []

ORIGIN = [WIDTH//2,HEIGHT//2 + 10]
XSCALE=1
YSCALE=1

class _CursorInfo(ctypes.Structure):
    _fields_ = [("size", ctypes.c_int),("visible", ctypes.c_byte)]

def clear_frame():
    global FRAME
    FRAME = [[" " for i in range(WIDTH)] for j in range(HEIGHT)]

def draw_axes():
    global FRAME
    for i in range(WIDTH):
        if (ORIGIN[1] > 0 and ORIGIN[1] < HEIGHT):
            FRAME[ORIGIN[1]][i] = "-"
    for i in range(1,HEIGHT):
        if (ORIGIN[0] > 0 and ORIGIN[0] < WIDTH):
            FRAME[i][ORIGIN[0]] = "|"
    if ORIGIN[0] > 0 and ORIGIN[0] < WIDTH and ORIGIN[1] > 0 and ORIGIN[1] < HEIGHT:
        FRAME[ORIGIN[1]][ORIGIN[0]] = "O"

def random_ansi_color():
    return "\033[3" + str(random.randint(1,8)) + "m"

def plot_function(f,var,col="\033[32m"):
    global FRAME
    for i in range(WIDTH):
        try:
            x = (i - ORIGIN[0]) / 8 / XSCALE
            y = f.subs(var,x)
            y = ORIGIN[1] - y * 8 * YSCALE
            if y < HEIGHT and y > 0:
                FRAME[int(y)][i] = col+"*"+"\033[0m"
        except:
            pass
    pstr = f'f({var}) = {f} | scale (x,y) : ({round(XSCALE,3)},{round(YSCALE,3)}) | h for help'
    for i in range(len(pstr)):
        FRAME[0][i] = pstr[i]
    
def closeto(a,b):
    return abs(a-b) < 0.1

def print_frame(offset=(0,0)):
    global FRAME
    for i in range(HEIGHT):
        for j in range(WIDTH):
            sys.stdout.write(FRAME[i][j])
        sys.stdout.write("\n")
    if (offset == (0,0)):
        sys.stdout.write('\033[H')
    else:
        sys.stdout.write(f'\033[{offset[1]+1};{offset[0]}H')

def hide_cursor():
    ci = _CursorInfo()
    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
    ci.visible = False
    ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))

def await_get_input(istt=""):
    print(istt,end="")
    input_char = msvcrt.getch()
    try:
        return input_char.decode("utf-8")
    except:
        return " "

def boxify(text):
    lines = text.split("\n")
    max_len = 0
    for line in lines:
        if len(line) > max_len:
            max_len = len(line)
    box= WIN_COL+" "*(max_len+4)+"\033[0m\n"
    for line in lines:
        box += WIN_COL+WIN_TEXT_COL+"  "+line+"\033[0m"+WIN_COL+" "*(max_len-len(line)+2)+BLACK_BG+" \033[0m\n"
    box+= WIN_COL+" "*(max_len+4)+BLACK_BG+" \033[0m\n"
    box += " "+BLACK_BG+" "*(max_len+4)+"\033[0m\n"
    return box

def center_on_screen(string):
    global WIDTH
    global HEIGHT
    return [WIDTH//2 - (len(string.split('\n')[0]))//2 + 4, HEIGHT//2 - len(string.split('\n'))//2]
    
def put_on_frame(text,pos):
    global FRAME
    lines = text.split("\n")
    # out=(0,0)
    for i in range(len(lines)):
        for j in range(len(lines[i])):
            FRAME[pos[1]+i][pos[0]+j] = lines[i][j]
    #         if lines[i][j] == '~':
    #             out=(pos[0]+j,pos[1]+i)
    # return out

def fparse(string):
    return string.replace("pi",str(math.pi)).replace("e",str(math.e))

def get_input_in_box(string):
    clear_frame()
    print_frame()
    iloc=string.find("~")
    newf=""
    k=""
    while (True):            
        if k == "\x08":
            if len(newf) > 0:
                newf = newf[:-2]
        newbox=string[:iloc]+"| "+newf+" |"+string[iloc+len(newf):]
        fbox=boxify(newbox)
        put_on_frame(fbox,center_on_screen(fbox))
        print_frame()
        k=await_get_input()
        if k == "\n" or k == "\r" or k == "\r\n":
            break
        newf+=k
    return newf

def sizeChangedThread():
    global WIDTH
    global HEIGHT
    while True:
        h=os.get_terminal_size().lines-1
        w=os.get_terminal_size().columns
        if h != HEIGHT or w != WIDTH:
            WIDTH = w
            HEIGHT = h

def guess_fun_var(f):
    # get the frequency of each letter in the function
    freqs = {}
    for c in f:
        if c in freqs:
            freqs[c] += 1
        else:
            if str(c).lower() in "uvwxyz":
                freqs[c] = 1
    # get the most frequent letter
    max_freq = 0
    max_char = ""
    for c in freqs:
        if freqs[c] > max_freq:
            max_freq = freqs[c]
            max_char = c
    # return the most frequent letter
    return max_char

def main():
    global ORIGIN
    global YSCALE
    global XSCALE
    global ENTER_FUNCTION_BOX
    os.system("title plot")
    if len(sys.argv) < 2:
        # print("Usage: plot.py \"<function>\" <variable>")
        # print("Example: plot.py \"sin(x+2)+cos(x/2)\" x")
        # sys.exit(1)
        f = [sympy.sympify(fparse(get_input_in_box(ENTER_FUNCTION_BOX))) for i in range (int(get_input_in_box(ENTER_NUM_FUNS_BOX)))]
        var = guess_fun_var(f)
    else:
        f = [sympy.sympify(fparse(sys.argv[1]))]
    if len(sys.argv) > 2:
        var = sys.argv[2]
    else:
        var = guess_fun_var(str(f[0]))
    hide_cursor()
    colors = [random_ansi_color() for i in range(len(f))]
    # clear_frame()
    # plot_function(f,var,color)
    # draw_axes() 
    # print_frame()
    # threading.Thread(target=sizeChangedThread).start()
    while True:
        clear_frame()
        o=0
        for t in f:
            plot_function(t,var,colors[o%len(colors)])
            o+=1
        draw_axes() 
        print_frame()
        c = await_get_input("")
        if c == "q":
            g = get_input_in_box("Are you sure you want to quit? (y/n)\n~")
            if g == "y":
                sys.exit(0)
        elif c == "z":
            XSCALE*=1.1
        elif c == "x":
            XSCALE/=1.1
        elif c == "c":
            YSCALE*=1.1
        elif c == "v":
            YSCALE/=1.1
        elif c == "w":
            ORIGIN[1] -= 1
        elif c == "s":
            ORIGIN[1] += 1
        elif c == "a":
            ORIGIN[0] -= 1
        elif c == "d":
            ORIGIN[0] += 1
        elif c == "r":
            ORIGIN = [WIDTH//2,HEIGHT//2 + 10]
            XSCALE = 1
            YSCALE = 1
        elif c == "h":
            clear_frame()
            print_frame()
            hbox=boxify(HELP)
            put_on_frame(hbox,center_on_screen(hbox))
            print_frame()
            await_get_input("")
        elif c == "f":
            newf=get_input_in_box(ENTER_FUNCTION_BOX)
            var=get_input_in_box(ENTER_VARIABLE_BOX)
            if newf == "":
                pass
            if var == "":
                var="x"
            try:
                f.append(sympy.sympify(fparse(newf)))
            except:
                print("Invalid function")
                pass
            colors.append(random_ansi_color())

if __name__ == "__main__":
    main()

