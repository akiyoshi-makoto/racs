#/usr/bin/python3
# -*- coding: utf8 -*-
from tkinter import *
from tkinter import ttk
from const import *
import view_normal
import view_admin_list

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
        self.note_mem = view_admin_list.ViewAdminList(MEMBER_LIST, master=note)
        self.note_ent = view_admin_list.ViewAdminList(ENTRY_LIST, master=note)
        note.add(self.note_mem, text='登録者管理')
        note.add(self.note_ent, text='在室者管理')
        note.pack()
        # タブが選択された場合の処理
        note.bind('<<NotebookTabChanged>>', self.tab_changed)

        button = ttk.Button(self,
                            text='管理ユーザモード終了',
                            command=lambda: master.switch_view(view_normal.ViewNormal))
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

if __name__ == "__main__":
    root = Tk()
    view = ViewAdmin(root)
    view.pack()
    view.mainloop()