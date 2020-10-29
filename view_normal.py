#/usr/bin/python3
# -*- coding: utf8 -*-
from tkinter import *
from tkinter import ttk
from const import *
import datetime
import csvcontrol
import felica
import view_admin

############################################################
# 通常ユーザ画面
############################################################
class ViewNormal(ttk.Frame):
    def __init__(self, master):
        self.active_timer = 3               # Felicaカードのセットが継続中タイマー
        self.delay_timer = 0                # 表示遅延タイマー
        self.idm = INVALID_IDM              # IDm
        self.flg_force_exit = True          # 強制退室処理フラグ(True:処理済 False:未処理)       
        
        # 登録者リストから読込
        self.member_list = csvcontrol.read_list(MEMBER_LIST)
        # print(self.member_list)     # for debug
        # 在室者リストから読込
        self.entry_list = csvcontrol.read_list(ENTRY_LIST)
        # print(self.entry_list)      # for debug
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
                                   font=('',50))
        self.label_day.pack(pady=(10,0))

        self.label_tim = ttk.Label(self,
                                   text='',
                                   font=('', 100))
        self.label_tim.pack()

        self.label_msg = ttk.Label(self,
                                   text='',
                                   font=('',30))
        self.label_msg.pack(pady=10)

        # 管理ユーザ画面に移動するボタン
        button = ttk.Button(self,
                            text="管理ユーザモード開始",
                            command=lambda: master.switch_view(view_admin.ViewAdmin))
        button.pack(pady=(10,0))

    ############################################################
    # 周期処理
    ############################################################
    def cycle_proc(self):
        # 現在時刻表示
        now_time = self.disp_now_time()
        # 強制退室処理
        self.force_exit(now_time)
        # Felicaカード読込処理
        idm = felica.read_felica()
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
                    csvcontrol.write_log_force_exit(now_time,self.entry_list)
                    # 在室者リストから削除
                    self.entry_list.clear()
                    # アプリ終了した場合に備えてバックアップを作成しておく
                    csvcontrol.write_list(self.entry_list, ENTRY_LIST)
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
        for member_index in range(len(self.member_list)):
            if self.idm == self.member_list[member_index][0]:
                is_member = True
                break
        
        # 在室者リストを検索
        is_entry = False
        for entry_index in range(len(self.entry_list)):
            if self.idm == self.entry_list[entry_index][0]:
                is_entry = True
                break

        if is_member:
            if is_entry:
                self.label_msg.config(text=self.member_list[member_index][2] + 'さんが退室しました。')
                csvcontrol.write_log(now_time, self.member_list, member_index, 'OUT')
                del self.entry_list[entry_index]
            else:
                self.label_msg.config(text=self.member_list[member_index][2] + 'さんが入室しました。')
                csvcontrol.write_log(now_time, self.member_list, member_index, 'IN')
                
                add_list = [self.member_list[member_index][0],          # Felica ID
                            str(self.member_list[member_index][1]),     # 社員No
                            self.member_list[member_index][2],          # 社員氏名
                           ]
                self.entry_list.append(add_list)
            # アプリ終了した場合に備えてバックアップを作成しておく
            csvcontrol.write_list(self.entry_list, ENTRY_LIST)
        else:
            if is_entry:
                self.label_msg.config(text='登録から既に削除されています。')
                del self.entry_list[entry_index]
                # アプリ終了した場合に備えてバックアップを作成しておく
                csvcontrol.write_list(self.entry_list, ENTRY_LIST)
            else:
                self.label_msg.config(text='未登録カードです。カードを登録してください。')

if __name__ == "__main__":
    root = Tk()
    view = ViewNormal(root)
    view.pack()
    view.mainloop()