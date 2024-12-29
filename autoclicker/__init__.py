import win32gui
import win32process
import psutil
import re
from typing import List
import time
from pywinauto.application import Application
from pywinauto.controls.uiawrapper import UIAWrapper
import signal
import os
import sys
import datetime

VERSION="1.0.0"
APP_NAME="AutoClicker"

class MLogger:
    logs_dir = ""
    @staticmethod
    def print(v: str):
        d = datetime.datetime.now()
        s = f"[ {d} ] {v}"
        if len(MLogger.logs_dir) != 0:
            today = d.strftime(r"%Y-%m-%d")
            if not os.path.exists(MLogger.logs_dir):
                os.mkdir(MLogger.logs_dir)

            logs_f = os.path.join(
                MLogger.logs_dir,
                f"{today}.txt"
            )
            with open(logs_f, 'a') as f:
                f.write(s + '\n')

        print(s)
        sys.stdout.flush()
    # def stderr(v: str):
    #     d = datetime.datetime.now()
    #     print(f"{d}:: {v}", file=sys.stderr)
    #     sys.stdout.flush()

class MProcessInfo:
    def __init__(self, pid: int, win32gui_hwnd: int):
        self.pid = pid
        self.hwnd = win32gui_hwnd
        try:
            self.app: Application = Application(backend="uia").connect(process=self.pid, timeout=10)
        except:
            MLogger.print("Cannot connect to pid {self.pid} exiting with status 1")
            sys.exit(1)

    
    def __str__(self):
        return f"MProcessInfo(pid={self.pid}, hwnd={hex(self.hwnd)})"

    def __repr__(self):
        return self.__str__()

    # def set_foreground(self):
    #     try:
    #         if self.app == None:
    #             return
    #         # if win32gui.GetWindowPlacement(self.hwnd) == win32con.SW_SHOWMINIMIZED:
    #         #     self.app.top_window().maximize()
    #         self.app.top_window().set_focus()
    #     except:
    #         print(f"{self.__str__()} Error MProcessInfo.set_foreground")

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
    # Logs condition for dbl click
    logs_condition = ".*because it is being used by another process."
    
    @staticmethod
    def find_child_windows(app: Application, windows: List[any]) -> bool:
        for window in app.windows():
            if re.match(Shopee.window_name, window.window_text()) != None:
                windows.append(window)

    @staticmethod
    def _find_relevant_childs(windows: UIAWrapper, childs: List[UIAWrapper], matches=[]):
        if len(matches) == 0:
            matches = Shopee.search_text

        for child in  windows.children():
            spl = child.window_text().splitlines()
            for t in matches:
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
            Shopee.logs_condition
        ]
        childs = []
        Shopee._find_relevant_childs(window, childs)
        for c in childs:
            # print(f"\tChild: {c.window_text()[0:30]}")
            win_text = c.window_text()

            if win_text.lower() in checks[0]:
                MLogger.print(f"Found {win_text}")
                return 2

            spl = win_text.splitlines()
            if len(spl) > 1 and re.match(logs_match, spl[0].strip()) != None:
                t = spl[len(spl)-1]
                if re.match(checks[1], t) != None:
                    MLogger.print(f"Found {t}")
                    return 2
        return 0
    
    @staticmethod
    def click(window: UIAWrapper, click_amnt: int, delay=0.5):
        if click_amnt <= 0:
            return

        childs = []
        # NOTE: modify this line if Shopee.search_text is also modified
        Shopee._find_relevant_childs(window, childs, Shopee.search_text[4:])
        
        if len(childs) == 0:
            MLogger.print(f"Button not found on window '{window.window_text()}'")
            return

        MLogger.print(f"Found button with text '{childs[0].window_text()}'. Clicking the button {click_amnt} time/s")
        while True:
            childs[0].click_input()
            click_amnt-=1

            if click_amnt <= 0:
                break
            time.sleep(delay)

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
                ret.append(MProcessInfo(pid, hwnd))
        except:
            pass

    win32gui.EnumWindows(callback, None)

def set_ctrl_c_handler():
    def signal_handler(sig, frame):
        MLogger.print("Process stopped by Ctrl+C")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

def run_ev_loop(opts: dict):
    window: List[MProcessInfo] = []
    MLogger.logs_dir = opts["logs_dir"]

    MLogger.print(f"Logs located at {opts["logs_dir"]}")
    MLogger.print(f"Press Ctrl+C to stop the process")

    find_window(Shopee.window_name, Shopee.app_name, window)
    while True:
        if len(window) == 0:
            MLogger.print(f"Window with name {Shopee.window_name} or exe path {Shopee.app_name} not found")
            window.clear()
            find_window(Shopee.window_name, Shopee.app_name, window)
            time.sleep(int(opts["sleep"]))
            continue

        if window[0].app == None or not window[0].app.is_process_running():
            MLogger.print(f"Application is not running. Cannot automate retrying in {opts["sleep"]}s")
            window.clear()
            find_window(Shopee.window_name, Shopee.app_name, window)
            time.sleep(int(opts["sleep"]))
            continue

        app = window[0].app
        windows: List[UIAWrapper] = []
        Shopee.find_child_windows(app, windows)

        to_clicks = []
        for c_win in windows:
            # uncomment this to force double click
            # to_clicks.append([c_win,2])
            # continue
            MLogger.print(f"Checking window '{c_win.window_text()}'")
            click_amnt = Shopee.should_click(c_win)
            to_clicks.append([c_win,click_amnt])
            MLogger.print(f"Done checking window '{c_win.window_text()}'")

        for info in to_clicks:
            if info[1] <= 0:
                continue
            MLogger.print(f"Setting window '{info[0]}' to foreground")
            info[0].set_focus()
            MLogger.print(f"Starting click on window '{info[0]}'")
            Shopee.click(info[0], info[1])

        time.sleep(int(opts["sleep"]))