#/usr/bin/python3
# -*- coding: utf8 -*-
from tkinter import *
from tkinter import ttk
from const import *
import csvcontrol
import felica

############################################################
# 管理ユーザ画面(一覧表示)
############################################################
class ViewAdminList(ttk.Frame):
    def __init__(self, list_kind, master):
        # リスト種別
        self.list_kind = list_kind
        # Felicaカード読取処理(管理ユーザモード)リトライ回数
        self.read_felica_retry = 0
        # 登録者(在室者)リストから読込
        self.list = csvcontrol.read_list(list_kind)
        # ウィジットを生成
        self.create_widgets(master)
        
    ############################################################
    # ウィジットを生成
    ############################################################
    def create_widgets(self, master):
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

        self.entry_idm = ttk.Entry(self, text='', width=18)
        self.entry_idm.grid(columnspan=2, row=1, column=3, padx=5, sticky=W)

        self.entry_num = ttk.Entry(self, text='', width=10)
        self.entry_num.grid(columnspan=2, row=2, column=3, padx=5, sticky=W)

        self.entry_nam = ttk.Entry(self, text='', width=18)
        self.entry_nam.grid(columnspan=2, row=3, column=3, padx=5, sticky=W)
  
        if self.list_kind == MEMBER_LIST:
            button_read = ttk.Button(self,
                                     text='Felicaから読込',
                                     command=self.read_felica_admin)
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
        self.entry_idm.configure(state='normal')
        self.entry_num.configure(state='normal')
        self.entry_nam.configure(state='normal')
        self.entry_idm.delete(0,'end')
        self.entry_num.delete(0,'end')
        self.entry_nam.delete(0,'end')
        # 選択された行をテキストボックスに表示
        for item in self.tree.selection():
            item_text = self.tree.item(item, 'values')
            self.entry_idm.insert('end', item_text[0])
            self.entry_num.insert('end', item_text[1])
            self.entry_nam.insert('end', item_text[2])

        # 在室者管理の場合は読み取り専用にする
        if self.list_kind == ENTRY_LIST:
            self.entry_idm.configure(state='readonly')
            self.entry_num.configure(state='readonly')
            self.entry_nam.configure(state='readonly')

        self.label_err.config(text='')

    ############################################################
    # Felicaカード読込処理
    ############################################################
    def read_felica_admin(self):
        # 事前にテキストボックスをクリア
        self.entry_idm.delete(0,'end')
        # Felicaカード読込実施
        idm = felica.read_felica()
        if idm != INVALID_IDM:
            self.label_err.config(text='Felicaカード読込成功')
            self.entry_idm.insert('end', idm)
            self.read_felica_retry = 0
        else:
            if self.read_felica_retry < 5:
                self.label_err.config(text='Felicaカード読込待ち')
                self.read_felica_retry += 1
                # リトライ処理
                self.after(1000,self.read_felica_admin)
            else:
                self.label_err.config(text='Felicaカード読込失敗')
                self.read_felica_retry = 0

    ############################################################
    # 管理ユーザモードにおける登録者リストの更新(追加)
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
                break

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

    ############################################################
    # 管理ユーザモードにおける登録者リストの更新(修正)
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
    # 管理ユーザモードにおける登録者リストの更新(削除)
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
    # 管理ユーザモードにおける一覧表のリフレッシュ
    ############################################################
    def refresh_list(self):
        # 一覧表示を更新
        self.tree.delete(*self.tree.get_children())
        
        for index in range(len(self.list)):
            self.tree.insert('','end',values=(self.list[index][0],
                                              self.list[index][1],
                                              self.list[index][2]))
        # CSVファイルを更新
        csvcontrol.write_list(self.list, self.list_kind)

if __name__ == "__main__":
    root = Tk()
    view = ViewAdminList(MEMBER_LIST, master=root)
    view.pack()
    view.mainloop()