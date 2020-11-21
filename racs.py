#!/usr/bin/env python
from tkinter import *
from tkinter import ttk
from const import *
import view_normal

############################################################
# 入退室管理システムの本体
############################################################
class Application(Tk):
    def __init__(self):
        Tk.__init__(self)
        # ウィンドウをスクリーンの中央に配置
        self.setting_window()
        # 画面設定(通常ユーザ画面)
        self.view = None
        self.switch_view(view_normal.ViewNormal)

    ############################################################
    # ウィンドウをスクリーンの中央に配置
    ############################################################
    def setting_window(self):
        w = 700                             # ウィンドウの横幅
        h = 440                             # ウィンドウの高さ
        sw = self.winfo_screenwidth()       # スクリーンの横幅
        sh = self.winfo_screenheight()      # スクリーンの高さ
        # ウィンドウをスクリーンの中央に配置
        self.geometry(str(w)+'x'+str(h)+'+'+str(int(sw/2-w/2))+'+'+str(int(sh/2-h/2)))
        # ウィンドウの最小サイズを指定
        self.minsize(w,h)
        self.title('入退室管理システム')

    ############################################################
    # 画面設定(通常ユーザ画面 or 管理ユーザ画面)
    ############################################################
    def switch_view(self, frame_class):
        view_new = frame_class(self)
        if self.view is not None:
            self.view.destroy()
        self.view = view_new
        self.view.pack()

if __name__ == "__main__":
    app = Application()
    app.mainloop()