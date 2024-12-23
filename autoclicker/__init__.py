import win32gui
import win32process
import psutil
import re
from typing import List
import time
from pywinauto.application import Application
from pywinauto.controls.uiawrapper import UIAWrapper
import signal
import sys
import datetime

class MLogger:
    logs_dir = ""
    @staticmethod
    def print(v: str):
        d = datetime.datetime.now()
        print(f"{d}:: {v}")
        sys.stdout.flush()
    
    def stderr(v: str):
        d = datetime.datetime.now()
        print(f"{d}:: {v}", file=sys.stderr)
        sys.stdout.flush()

class MProcessInfo:
    def __init__(self, pid: int, win32gui_hwnd: int):
        self.pid = pid
        self.hwnd = win32gui_hwnd
        self.app: Application = Application(backend="uia").connect(process=self.pid, timeout=10)
    
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

CLICK_SINGLE=1
CLICK_DOUBLE=2

class Shopee:
    window_name = "Shopee.*"
    app_name = ".*Shopee FlashSale.exe"
    search_text = [
        # Timer
        r"\d{2}:\d{2}:\d{2}\.\d",
        "Success",
        "Failed",
        # Logs
        r"^\[.*\].*$",
        
        # Buttons
        "Stop",
        "Start",
    ]
    
    @staticmethod
    def find_child_windows(app: Application, windows: List[any]) -> bool:
        for window in app.windows():
            if re.match(Shopee.window_name, window.window_text()) != None:
                windows.append(window)

    @staticmethod
    def _find_relevant_childs(windows: UIAWrapper, childs: List[UIAWrapper]):
        for child in  windows.children():
            spl = child.window_text().splitlines()
            for t in Shopee.search_text:
                if re.match(t, child.window_text()) != None:
                    # print(f"Appending {t} {child.window_text()[0:50]}")
                    childs.append(child)
                    break
                if len(spl) > 1 and re.match(t, spl[0].strip()) != None:
                    # print(f"Appending {t} {child.window_text()[0:50]}")
                    childs.append(child)
                    break

    @staticmethod
    def should_click(window: UIAWrapper) -> int:
        logs_match = Shopee.search_text[3]

        checks = [
            ["success", "failed"],
            ""
        ]
        childs = []
        Shopee._find_relevant_childs(window, childs)
        for c in childs:
            print(f"\tChild: {c.window_text()[0:30]}")
            win_text = c.window_text()

            if win_text.lower() in checks[0]:
                return CLICK_DOUBLE

            spl = win_text.splitlines()
            if len(spl) > 1 and re.match(logs_match, spl[0].strip()) != None:
                t = spl[len(spl)-1]
                # print(f"Last: {t} Len: {len(spl)}")
                return 0
                if re.match(checks[1], t) != None:
                    return CLICK_DOUBLE
            # print(f"{c.control_id()} {c.friendly_class_name()} {c.window_text()[0:30]}")
        return 0
    
    @staticmethod
    def click(window: UIAWrapper, click_amnt: int):
        pass

def find_window(name_rgx: str, exe_path: str, ret: List[MProcessInfo]):
    def callback(hwnd, _extra):
        if len(ret) != 0:
            return
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
                ret.append(MProcessInfo(pid, hwnd))
        except:
            pass

    win32gui.EnumWindows(callback, None)

def set_ctrl_c_handler():
    def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        # handler exit here
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

def run_ev_loop(opts: dict):
    window: List[MProcessInfo] = []
    # find exactly one window
    # loop through the windows with name_regex
    # do the process
    MLogger.logs_dir = opts["logs_dir"]
    MLogger.print(f"Logs located at {opts["logs_dir"]}")
    MLogger.print(f"Press Ctrl+C to stop the process")
    while True:
        if len(window) == 0:
            find_window(Shopee.window_name, Shopee.app_name, window)
            continue

        app = window[0].app
        windows: List[UIAWrapper] = []
        Shopee.find_child_windows(app, windows)

        for window in windows:
            MLogger.print(f"Setting '{window.window_text()}' to foreground")
            window.set_focus()
            click_amnt = Shopee.should_click(window)
            MLogger.print(f"Done '{window.window_text()}'")


        break
        sys.stdout.flush()
        time.sleep(int(opts["sleep"]))
        pass