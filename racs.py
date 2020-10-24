#/usr/bin/python3
# -*- coding: utf8 -*-
from tkinter import *
from tkinter import ttk
from enum import Enum
import nfc
import os
import datetime
import csv

############################################################
# 定数
############################################################
MEMBER_LIST = 'member_list.csv'
ENTRY_LIST = 'entry_list.csv'
INVALID_IDM = '0'

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
        self.switch_view(ViewNormal)

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

############################################################
# 通常ユーザ画面
############################################################
class ViewNormal(ttk.Frame):
    def __init__(self, master):
        self.active_timer = 3               # Felicaカードのセットが継続中タイマー
        self.delay_timer = 0                # 表示遅延タイマー
        self.idm = INVALID_IDM              # IDm
        self.flg_force_exit = True          # 強制退室処理フラグ(True:処理済 False:未処理)       
        
        self.csv = CsvControl()
        # 登録者リストから読込
        self.member_list = self.csv.read_list(MEMBER_LIST)
        # print(self.member_list)     # for debug
        # 在室者リストから読込
        self.entry_list = self.csv.read_list(ENTRY_LIST)
        # print(self.entry_list)      # for debug
        # NFC(Felica)リーダー
        self.felica = Felica()
        # ウィジットを生成
        self.create_widgets(master)
        # 100ms後に遅れて入退室監視処理を開始
        self.after(100,self.cycle_proc)

    ############################################################
    # ウィジットを生成
    ############################################################
    def create_widgets(self, master):
        ttk.Frame.__init__(self, master)
        self.label_day = ttk.Label(self,
                                   text='',
                                   font=('', 18))
        self.label_day.pack(pady=(30,0))

        self.label_tim = ttk.Label(self,
                                   text='',
                                   font=('', 60))
        self.label_tim.pack()

        self.label_msg = ttk.Label(self,
                                   text='',
                                   font=('',18))
        self.label_msg.pack(pady=30)

        # 管理ユーザ画面に移動するボタン
        button = ttk.Button(self,
                            text="管理者モード開始",
                            command=lambda: master.switch_view(ViewAdmin))
        button.pack(pady=(110,0))

    ############################################################
    # 周期処理
    ############################################################
    def cycle_proc(self):
        # 現在時刻表示
        now_time = self.disp_now_time()
        # 強制退室処理
        self.force_exit(now_time)
        # Felicaカード読込処理
        idm = self.felica.read_felica()
        # Felicaカードタッチ判定
        if self.touch_felica(idm):
            # 入退室判定処理
            self.room_access(now_time)
        
        # 周期処理の実現
        self.after(1000,self.cycle_proc)

    ############################################################
    # 現在時刻表示
    ############################################################
    def disp_now_time(self):
        now_time = datetime.datetime.now()
        self.label_day.config(text=now_time.strftime('%Y-%m-%d'))
        self.label_tim.config(text=now_time.strftime('%H:%M:%S'))
        return now_time

    ############################################################
    # 強制退室処理
    ############################################################
    def force_exit(self, now_time):
        # AM6:00以降
        if now_time.hour >= 6:
            if self.flg_force_exit:
                # 基本的にはここを通る。初期値をTrueにしているため、起動直後もここを通る。
                # 夜中の24時を過ぎて、かつAM6:00まで起動していた場合に在室者リストを削除する。
                pass
            else:
                self.flg_force_exit = True
                if len(self.entry_list) > 0:
                    # 強制退室処理時のログ書込
                    self.csv.write_log_force_exit(now_time,self.entry_list)
                    # 在室者リストから削除
                    self.entry_list.clear()
                    # アプリ終了した場合に備えてバックアップを作成しておく
                    self.csv.write_list(self.entry_list, ENTRY_LIST)
        # AM0:00～AM5:59 
        else:
            if self.flg_force_exit:
                self.flg_force_exit = False
            else:
                # AM6:00になるまでは在室者リストを削除しない
                pass

    ############################################################
    # Felicaカードタッチ判定
    ############################################################
    def touch_felica(self, idm):
        touch_ok = False

        # Felicaカード読込成功
        if idm != INVALID_IDM:
            self.delay_timer = 0
            # 新たなカードタッチ(同じカードでも可能)
            if self.active_timer == 0:
                self.active_timer += 1
                touch_ok = True
            # 同じカードでのカードタッチ
            else:
                # 前回異なるカードでのカードタッチ
                if self.idm != idm:
                    self.active_timer = 0
                    touch_ok = True
                # 同じカードでの連続タッチ
                else:
                    # 同じカードを3秒連続タッチ
                    if self.active_timer >= 3:
                        self.label_msg.config(text='カードを離してください。')
                    else:
                        self.active_timer += 1

            self.idm = idm
        # Felicaカード読込失敗
        else:
            if self.active_timer >= 3:
                self.label_msg.config(text='カードをタッチしてください。')
            else:   
                if self.delay_timer >= 3:
                    self.label_msg.config(text='カードをタッチしてください。')
                else:
                    self.delay_timer += 1

            self.active_timer = 0

        # print('active_timer: ' + str(self.active_timer))    # for debug
        # print('delay_timer: ' + str(self.delay_timer))      # for debug

        return touch_ok
            
    ############################################################
    # 入退室判定処理
    ############################################################
    def room_access(self, now_time):
        # 登録済のIDを検索
        is_member = False
        for member_index in len(self.member_list):
            if self.idm == self.member_list[member_index][0]:
                is_member = True
                break
        
        # 在室者リストを検索
        is_entry = False
        for entry_index in len(self.entry_list):
            if self.idm == self.entry_list[entry_index][0]:
                is_entry = True
                break

        if is_member:
            if is_entry:
                self.label_msg.config(text=self.member_list[member_index][2] + 'さんが退室しました。')
                self.csv.write_log(now_time, self.member_list, member_index, 'OUT')
                del self.entry_list[entry_index]
            else:
                self.label_msg.config(text=self.member_list[member_index][2] + 'さんが入室しました。')
                self.csv.write_log(now_time, self.member_list, member_index, 'IN')
                
                add_list = [self.member_list[index][0],          # Felica ID
                            str(self.member_list[index][1]),     # 社員No
                            self.member_list[index][2],          # 社員氏名
                           ]
                self.entry_list.append(add_list)
            # アプリ終了した場合に備えてバックアップを作成しておく
            self.csv.write_list(self.entry_list, ENTRY_LIST)
        else:
            if is_entry:
                self.label_msg.config(text='登録から既に削除されています。')
                del self.entry_list[entry_index]
                # アプリ終了した場合に備えてバックアップを作成しておく
                self.csv.write_list(self.entry_list, ENTRY_LIST)
            else:
                self.label_msg.config(text='未登録カードです。カードを登録してください。')

############################################################
# 管理ユーザ画面
############################################################
class ViewAdmin(ttk.Frame):
    def __init__(self, master):
         # ウィジットを生成
        self.create_widgets(master)

    ############################################################
    # ウィジットを生成
    ############################################################
    def create_widgets(self, master):
        ttk.Frame.__init__(self, master)
        note = ttk.Notebook(self, width=680, height=335, padding=10)
        self.note_mem = ViewAdminList(MEMBER_LIST, master=note)
        self.note_ent = ViewAdminList(ENTRY_LIST, master=note)
        note.add(self.note_mem, text='登録者管理')
        note.add(self.note_ent, text='在室者管理')
        note.pack()
        # タブが選択された場合の処理
        note.bind('<<NotebookTabChanged>>', self.tab_changed)

        button = ttk.Button(self,
                            text='管理者モード終了',
                            command=lambda: master.switch_view(ViewNormal))
        button.pack(pady=(10,0))

    ############################################################
    # タブが選択された場合の処理
    ############################################################
    def tab_changed(self, event):
        note = event.widget
        name = note.tab(note.select(), 'text')
        
        if name == '登録者管理':
            tab = self.note_mem
        elif name == '在室者管理':
            tab = self.note_ent
        else:
            pass
        
        # 一覧表示を更新
        tab.tree.delete(*tab.tree.get_children())
        for index in range(len(tab.list)):
            tab.tree.insert('','end',values=(tab.list[index][0],
                                             tab.list[index][1],
                                             tab.list[index][2]))
        # テキストボックスをクリア
        tab.entry_idm.delete(0,'end')
        tab.entry_num.delete(0,'end')
        tab.entry_nam.delete(0,'end')

        tab.label_err.config(text='')

############################################################
# 管理ユーザ画面(一覧表示)
############################################################
class ViewAdminList(ttk.Frame):
    def __init__(self, list_kind, master):
        # リスト種別
        self.list_kind = list_kind
        # Felicaカード読取処理(管理者モード)リトライ回数
        self.read_felica_retry = 0
        # NFC(Felica)リーダー
        self.felica = Felica()
        # 登録者(在室者)リストから読込
        self.csv = CsvControl()
        self.list = self.csv.read_list(list_kind)
        # ウィジットを生成
        self.create_widgets(list_kind, master)
        
    ############################################################
    # ウィジットを生成
    ############################################################
    def create_widgets(self, list_kind, master):
        ttk.Frame.__init__(self, master)
        # 一覧表示
        self.tree = ttk.Treeview(self)
        # 列インデックスの作成
        self.tree['columns'] = (1,2,3)
        self.tree['height'] = 14
        # 表スタイルの設定(headingsはツリー形式ではない、通常の表形式)
        self.tree['show'] = 'headings'
        # 各列の設定(インデックス,オプション(今回は幅を指定))
        self.tree.column(1,width=150)
        self.tree.column(2,width=70)
        self.tree.column(3,width=150)
        # 各列のヘッダー設定(インデックス,テキスト)
        self.tree.heading(1,text='Felica ID')
        self.tree.heading(2,text='社員番号')
        self.tree.heading(3,text='社員氏名')

        # 登録者(在室者)リストから表示するデータを取り出し、一覧表示
        # print(len(self.list))     # for debug
        for index in range(len(self.list)):
            self.tree.insert('','end',values=(self.list[index][0],
                                              self.list[index][1],
                                              self.list[index][2]))

        self.tree.grid(rowspan=6, row=0, column=0, padx=(10,0), pady=(10,0))

        #スクロールバー
        scroll = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        scroll.grid(rowspan=6, row=0, column=1, padx=(0,0), pady=(10,0), sticky='ns')
        self.tree["yscrollcommand"] = scroll.set

        # 一覧表示にて選択された行の内容をテキストボックスに表示
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        label_idm = ttk.Label(self, text='Felica ID')
        label_idm.grid(row=1, column=2, padx=5, pady=10)

        label_num = ttk.Label(self, text='社員番号')
        label_num.grid(row=2, column=2, padx=5, pady=10)

        label_nam = ttk.Label(self, text='社員氏名')
        label_nam.grid(row=3, column=2, padx=5, pady=10)

        idm = StringVar()
        self.entry_idm = ttk.Entry(self, textvariable=idm, width=18)
        self.entry_idm.grid(columnspan=2, row=1, column=3, padx=5, sticky=W)

        num = StringVar()
        self.entry_num = ttk.Entry(self, textvariable=num, width=10)
        self.entry_num.grid(columnspan=2, row=2, column=3, padx=5, sticky=W)

        nam = StringVar()
        self.entry_nam = ttk.Entry(self, textvariable=nam, width=18)
        self.entry_nam.grid(columnspan=2, row=3, column=3, padx=5, sticky=W)

        if list_kind == MEMBER_LIST:
            button_read = ttk.Button(self,
                                     text='Felicaから読込',
                                     command=self.read_felica)
            button_read.grid(columnspan=2, row=0, column=3, padx=5, pady=(10,0), sticky=W)
            
            button_add = ttk.Button(self,
                                    text='追加',
                                    command=self.add_list)
            button_add.grid(row=4, column=2, padx=5, pady=10)

            button_chg = ttk.Button(self,
                                    text='修正',
                                    command=self.chg_list)
            button_chg.grid(row=4, column=3, padx=5, pady=10)

        button_del = ttk.Button(self,
                                text='削除',
                                command=self.del_list)
        button_del.grid(row=4, column=4, padx=5, pady=10)

        self.label_err = ttk.Label(self, text='', foreground='red')
        self.label_err.grid(columnspan=3, row=5, column=2, padx=5, pady=5)

    ############################################################
    # 一覧表示にて選択された行の内容をテキストボックスに表示
    ############################################################
    def on_tree_select(self, event):
        # テキストボックスを事前にクリア
        self.entry_idm.delete(0,'end')
        self.entry_num.delete(0,'end')
        self.entry_nam.delete(0,'end')
        # 選択された行をテキストボックスに表示
        for item in self.tree.selection():
            item_text = self.tree.item(item, 'values')
            self.entry_idm.insert('end', item_text[0])
            self.entry_num.insert('end', item_text[1])
            self.entry_nam.insert('end', item_text[2])

        self.label_err.config(text='')

    ############################################################
    # Felicaカード読込処理
    ############################################################
    def read_felica(self):
        # 事前にテキストボックスをクリア
        self.entry_idm.delete(0,'end')
        # Felicaカード読込実施
        idm = self.felica.read_felica()
        if idm != INVALID_IDM:
            self.label_err.config(text='Felicaカード読込成功')
            self.entry_idm.insert('end', idm)
            self.read_felica_retry = 0
        else:
            if self.read_felica_retry < 5:
                self.label_err.config(text='Felicaカード読込待ち')
                self.read_felica_retry += 1
                # リトライ処理
                self.after(1000,self.read_felica)
            else:
                self.label_err.config(text='Felicaカード読込失敗')
                self.read_felica_retry = 0

    ############################################################
    # 管理者モードにおける登録者リストの更新(追加)
    ############################################################
    def add_list(self):
        idm = self.entry_idm.get()
        num = self.entry_num.get()
        nam = self.entry_nam.get()
        is_exec = True

        for index in range(len(self.list)):
            if self.list[index][0] == idm:
                self.label_err.config(text='登録済です。何もしません。')
                is_exec = False

        if idm == '' or num == '' or nam == '':
            self.label_err.config(text='空白あり。全ての項目に入力してください。')
            is_exec = False

        if is_exec:
            add_list = [idm,    # Felica ID
                        num,    # 社員No
                        nam,    # 社員氏名
                       ]
            self.list.append(add_list)

           # 一覧表のリフレッシュ
            self.refresh_list()

            self.label_err.config(text='追加に成功しました。')
        else:
            self.label_err.config(text='追加に失敗しました。')

    ############################################################
    # 管理者モードにおける登録者リストの更新(修正)
    ############################################################
    def chg_list(self):
        idm = self.entry_idm.get()
        num = self.entry_num.get()
        nam = self.entry_nam.get()
        is_exec = False

        for index in range(len(self.list)):
            if self.list[index][0] == idm:
                if idm == '' or num == '' or nam == '':
                    self.label_err.config(text='空白あり。全ての項目に入力してください。')
                    is_exec = False
                else:
                    is_exec = True
                break
            
        if is_exec:
            self.list[index][1] = num   # 社員No
            self.list[index][2] = nam   # 社員氏名

            # 一覧表のリフレッシュ
            self.refresh_list()

            self.label_err.config(text='修正に成功しました。')
        else:
            self.label_err.config(text='修正に失敗しました。\nIDを修正する場合は新規に追加して下さい。')


    ############################################################
    # 管理者モードにおける登録者リストの更新(削除)
    ############################################################
    def del_list(self):
        idm = self.entry_idm.get()
        num = self.entry_num.get()
        nam = self.entry_nam.get()
        is_exec = False

        for index in range(len(self.list)):
            if self.list[index][0] == idm:
                if self.list[index][1] == num:
                    if self.list[index][2] == nam:
                        is_exec = True
                        break

        if is_exec:
            del self.list[index]

            # 一覧表のリフレッシュ
            self.refresh_list()

            self.label_err.config(text='削除に成功しました。')
        else:
            self.label_err.config(text='削除に失敗しました。')

    ############################################################
    # 管理者モードにおける一覧表のリフレッシュ
    ############################################################
    def refresh_list(self):
        # 一覧表示を更新
        self.tree.delete(*self.tree.get_children())
        
        for index in range(len(self.list)):
            self.tree.insert('','end',values=(self.list[index][0],
                                                self.list[index][1],
                                                self.list[index][2]))
        # CSVファイルを更新
        self.csv.write_list(self.list, self.list_kind)


############################################################
# CSVファイル制御
############################################################
class CsvControl:
    def __init__(self):
        pass

    ############################################################
    # リスト(登録者 or 在室者)から読込
    ############################################################
    def read_list(self, kind):
        if os.path.isfile(kind):
            with open(kind, 'r', encoding='utf-8') as csvfile:
                file = csv.reader(csvfile)
                list = [row for row in file]
        else:
            list = []
        return list

    ############################################################
    # リスト(登録者 or 在室者)への書込
    ############################################################
    def write_list(self, list, kind):
        with open(kind, 'w', newline='', encoding='utf-8') as csvfile:
            file = csv.writer(csvfile)
            file.writerows(list)

    ############################################################
    # 入退室時のログ書込
    ############################################################
    def write_log(self, now_time, list, index, in_out_info):
        # ログファイルはWindows PCで開くことを想定しているためS-JISでエンコードする。
        with open(now_time.strftime('%Y-%m') + '.csv', 'a', newline='', encoding='shift_jis') as csvfile:
            file = csv.writer(csvfile)
            file.writerow([list[index][0],                  # Felica ID
                           str(list[index][1]),             # 社員No
                           list[index][2],                  # 社員氏名
                           now_time.strftime('%Y-%m-%d'),   # 年月日
                           now_time.strftime('%H:%M:%S'),   # 時刻
                           in_out_info])                    # 入退室情報

    ############################################################
    # 強制退室処理時のログ書込
    ############################################################
    def write_log_force_exit(self, now_time, list):
        # ログファイルはWindows PCで開くことを想定しているためS-JISでエンコードする。
        with open(now_time.strftime('%Y-%m') + '.csv', 'a', newline='', encoding='shift_jis') as csvfile:
            file = csv.writer(csvfile)

            for index in len(list):
                file.writerow([list[index][0],                  # Felica ID
                               str(list[index][1]),             # 社員No
                               list[index][2],                  # 社員氏名
                               now_time.strftime('%Y-%m-%d'),   # 年月日
                               now_time.strftime('%H:%M:%S'),   # 時刻
                               'FORCE_EXIT'])                   # 入退室情報

############################################################
# NFC(Felica)リーダー
############################################################
class Felica:
    def __init__(self):
        pass

    ############################################################
    # Felicaカード読込処理
    ############################################################
    def read_felica(self):
        # for debug
        clf = nfc.ContactlessFrontend('usb')
        target = nfc.clf.RemoteTarget('212F')   # Felica
        res = clf.sense(target)

        # Felicaカード読込成功
        if not res is None:
            tag = nfc.tag.activate(clf, res)
            idm = tag.idm.hex()
            print('IDm : ' + idm)
        else:
            idm = INVALID_IDM

        clf.close()
        # for debug
        #idm = INVALID_IDM  # for debug
        return idm

if __name__ == "__main__":
    app = Application()
    app.mainloop()