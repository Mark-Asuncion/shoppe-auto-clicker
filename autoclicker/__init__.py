import win32gui
import win32process
import psutil
import re
from typing import List
import time
from pywinauto.application import Application
import signal
import sys

class MProcessInfo:
    def __init__(self, pid: int, win32gui_hwnd: int):
        self.pid = pid
        self.hwnd = win32gui_hwnd
        self.app: Application = Application().connect(process=self.pid)
    
    def __str__(self):
        return f"MProcessInfo(pid={self.pid}, hwnd={hex(self.hwnd)})"

    def __repr__(self):
        return self.__str__()
    
    def set_foreground(self):
        try:
            if self.app == None:
                return
            # if win32gui.GetWindowPlacement(self.hwnd) == win32con.SW_SHOWMINIMIZED:
            #     self.app.top_window().maximize()
            self.app.top_window().set_focus()
        except:
            print(f"{self.__str__()} Error MProcessInfo.set_foreground")

class Shoppee:
    def __init__(self):
        self.window_name = "Shoppee.*"
        self.app_name = ".*shoppee.exe"
    
    def should_click(process: MProcessInfo) -> bool:
        return False
    
    def click(process: MProcessInfo):
        pass

def find_windows(name_rgx: str, exe_path: str, ret_list: List[MProcessInfo]):
    def callback(hwnd, _extra):
        if not win32gui.IsWindowVisible(hwnd):
            return

        _, pid = win32process.GetWindowThreadProcessId(hwnd)  # Get Process ID
        try:
            process = psutil.Process(pid)  # Use psutil to query the process
            win_exe_path = process.exe()  # Get executable path
            win_text = win32gui.GetWindowText(hwnd)
            is_match = False
            # print(f"{win_text} {win_exe_path}")
            if len(name_rgx) != 0:
                if re.search(name_rgx, win_text) != None:
                    is_match = True
            if len(exe_path) != 0:
                if re.search(exe_path, win_exe_path) != None:
                    is_match = True
            
            if is_match:
                win32gui.EnumDesktopWindows
                ret_list.append(MProcessInfo(pid, hwnd))
        except:
            pass

    win32gui.EnumWindows(callback, None)

# for window in windows:
#     window.set_foreground()
#     time.sleep(1)

# w1 = windows[0].app.top_window()
# w1.child_window(class_name="Edit").type_keys("Hello f", with_spaces=True)
# print( w1.texts() )
# windows[0].app.top_window().dump_tree()

def set_ctrl_c_handler():
    def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        # handler exit here
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

def run_ev_loop(opts: dict):
    windows: List[MProcessInfo] = []
    find_windows(".*Notepad", ".*notepad.exe", windows)
    while True:
        print('.', end=" ")
        sys.stdout.flush()
        time.sleep(int(opts["sleep"]))
        pass