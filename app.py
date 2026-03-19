import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

# 数据路径适配
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(base_path, "lottery_history.json")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse_txt_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    data = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '-' in line and len(line) > 8:
            date = line
            i += 1
            if i < len(lines):
                next_line = lines[i]
                if '期' in next_line:
                    try:
                        parts = next_line.split()
                        period = parts[0]
                        number = int(''.join(filter(str.isdigit, parts[-1])))
                        if 1 <= number <= 49:
                            data.append({"date": date, "period": period, "number": number})
                    except:
                        pass
        i += 1
    return data

def get_date_key(record):
    try:
        return datetime.strptime(record["date"], "%Y-%m-%d")
    except:
        return datetime(1900, 1, 1)

def analyze_next(history, strategy_n=4):
    if not history:
        return [], [], list(range(1, 50))
    
    sorted_history = sorted(history, key=get_date_key, reverse=True)
    zero_zone = set()
    
    if sorted_history:
        zero_zone.add(sorted_history[0]["number"])
    
    recent_10 = sorted_history[:10]
    appear = defaultdict(list)
    for idx, rec in enumerate(recent_10):
        appear[rec["number"]].append(idx)
    for num, pos in appear.items():
        if len(pos) >= 2 and min(pos) <= 5:
            zero_zone.add(num)
    
    for i in range(len(sorted_history)-1):
        if sorted_history[i]["number"] == sorted_history[i+1]["number"] and i <= 9:
            zero_zone.add(sorted_history[i]["number"])
            break
    
    recent_n = [sorted_history[i]["number"] for i in range(min(strategy_n, len(sorted_history)))]
    low_zone = [n for n in recent_n if n not in zero_zone]
    
    all_nums = set(range(1, 50))
    high_zone = sorted(all_nums - zero_zone - set(low_zone))
    
    return sorted(zero_zone), low_zone, high_zone

class LotteryAnalyzer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎯 特码智能分区分析器（12策略完整版）")
        self.geometry("1780x980")
        self.history = load_data()
        self.strategy_n = 4
        self.bet_low = 500
        self.bet_high = 1000
        self.low_text = "500元区 (中注)"
        self.high_text = "1000元区 (重点)"
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # 策略切换（12个选项）
        strategy_frame = ttk.LabelFrame(main_frame, text="切换策略", padding=8)
        strategy_frame.pack(fill="x", pady=5)
        ttk.Label(strategy_frame, text="投注策略：").pack(side="left", padx=5)
        self.strategy_combo = ttk.Combobox(strategy_frame, 
            values=["近4期500", "近5期500", "近6期500", "近7期500", "近8期500", "近9期500",
                    "近4期200", "近5期200", "近6期200", "近7期200", "近8期200", "近9期200"], 
            state="readonly", width=15)
        self.strategy_combo.set("近4期500")
        self.strategy_combo.pack(side="left", padx=5)
        self.strategy_combo.bind("<<ComboboxSelected>>", self.change_strategy)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="📥 导入历史txt", command=self.import_txt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 刷新表格", command=self.refresh_table).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ 删除选中", command=self.delete_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🚀 分析下一期", command=self.show_analysis, style="Accent.TButton").pack(side="right", padx=5)
        
        # 历史表格
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill="both", expand=True)
        
        self.tree = ttk.Treeview(table_frame, columns=("date", "period", "number", 
            "bet_total", "rebate", "profit", "win_amount", "cum_rebate", "cum_profit",
            "zero", "low_zone", "high_zone"), show="headings", height=22)
        
        self.tree.heading("date", text="日期")
        self.tree.heading("period", text="期号")
        self.tree.heading("number", text="特码")
        self.tree.heading("bet_total", text="当期投注总额")
        self.tree.heading("rebate", text="当期反水")
        self.tree.heading("profit", text="当期盈亏")
        self.tree.heading("win_amount", text="当期中奖额")
        self.tree.heading("cum_rebate", text="累积反水")
        self.tree.heading("cum_profit", text="累积盈亏")
        self.tree.heading("zero", text="0元区 (禁注)")
        self.tree.heading("low_zone", text=self.low_text)
        self.tree.heading("high_zone", text=self.high_text)
        
        self.tree.column("date", width=115, minwidth=115, stretch=False)
        self.tree.column("period", width=75, minwidth=75, stretch=False)
        self.tree.column("number", width=55, minwidth=55, stretch=False)
        self.tree.column("bet_total", width=120, minwidth=120, stretch=False)
        self.tree.column("rebate", width=100, minwidth=100, stretch=False)
        self.tree.column("profit", width=100, minwidth=100, stretch=False)
        self.tree.column("win_amount", width=120, minwidth=120, stretch=False)
        self.tree.column("cum_rebate", width=100, minwidth=100, stretch=False)
        self.tree.column("cum_profit", width=100, minwidth=100, stretch=False)
        self.tree.column("zero", width=160, minwidth=160, stretch=False)
        self.tree.column("low_zone", width=180, minwidth=180, stretch=False)
        self.tree.column("high_zone", width=1550, minwidth=1550, stretch=False)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=self.hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # 亏损绿色
        self.tree.tag_configure("loss", foreground="#00AA00")
        
        # 粗黑分割线
        style = ttk.Style()
        style.configure("Treeview", background="#ffffff", foreground="#000000", borderwidth=5, relief="solid")
        style.configure("Treeview.Heading", background="#d0d0d0", foreground="#000000", borderwidth=5, relief="raised")
        
        # 强制拉条
        self.tree.bind("<Configure>", self.force_scrollbar)
        self.tree.bind("<ButtonRelease-1>", self.force_scrollbar)
        
        # 近期盈亏统计
        stat_frame = ttk.LabelFrame(main_frame, text="近期盈亏统计", padding=10)
        stat_frame.pack(fill="x", pady=8)
        self.stat_labels = {}
        periods = [30, 50, 100, 150, 200, 300]
        for idx, p in enumerate(periods):
            lbl = ttk.Label(stat_frame, text=f"近{p}期盈亏: 等待数据", font=("微软雅黑", 11))
            lbl.grid(row=idx//3, column=idx%3, padx=25, pady=6, sticky="w")
            self.stat_labels[p] = lbl
        
        # 手动添加
        add_frame = ttk.LabelFrame(main_frame, text="✍️ 手动添加新期", padding=10)
        add_frame.pack(fill="x", pady=10)
        ttk.Label(add_frame, text="日期:").grid(row=0, column=0, padx=5)
        self.date_entry = ttk.Entry(add_frame, width=15)
        self.date_entry.grid(row=0, column=1, padx=5)
        self.date_entry.insert(0, "2026-03-15")
        
        ttk.Label(add_frame, text="期号:").grid(row=0, column=2, padx=5)
        self.period_entry = ttk.Entry(add_frame, width=10)
        self.period_entry.grid(row=0, column=3, padx=5)
        self.period_entry.insert(0, "074期")
        
        ttk.Label(add_frame, text="特码:").grid(row=0, column=4, padx=5)
        self.num_entry = ttk.Entry(add_frame, width=8)
        self.num_entry.grid(row=0, column=5, padx=5)
        self.num_entry.insert(0, "25")
        
        ttk.Button(add_frame, text="添加并保存", command=self.add_record).grid(row=0, column=6, padx=15)
        
        self.style = ttk.Style()
        self.style.configure("Accent.TButton", foreground="white", background="#0078D4")
        
        self.refresh_table()

    def force_scrollbar(self, event=None):
        self.tree.configure(xscrollcommand=self.hsb.set)
        self.after(10, lambda: self.tree.configure(xscrollcommand=self.hsb.set))
        self.after(50, lambda: self.tree.configure(xscrollcommand=self.hsb.set))
        self.after(100, lambda: self.tree.xview_moveto(0))

    def change_strategy(self, event):
        selected = self.strategy_combo.get()
        self.strategy_n = int(selected.split('近')[1].split('期')[0])
        if '500' in selected:
            self.bet_low = 500
            self.bet_high = 1000
            self.low_text = "500元区 (中注)"
            self.high_text = "1000元区 (重点)"
        else:
            self.bet_low = 200
            self.bet_high = 1500
            self.low_text = "200元区 (中注)"
            self.high_text = "1500元区 (重点)"
        
        # 动态更新列标题
        self.tree.heading("low_zone", text=self.low_text)
        self.tree.heading("high_zone", text=self.high_text)
        self.refresh_table()

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.history:
            return
        
        sorted_data = sorted(self.history, key=get_date_key)
        cum_rebate = 0.0
        cum_profit = 0.0
        all_profits = []
        
        for i in range(len(sorted_data)):
            past = sorted_data[:i]
            zero_list, low_list, high_list = analyze_next(past, self.strategy_n)
            
            win_num = sorted_data[i]["number"]
            
            bet_total = self.bet_low * len(low_list) + self.bet_high * len(high_list)
            rebate = bet_total * 0.03
            
            if win_num in low_list:
                win_amount = self.bet_low * 47.5
            elif win_num in high_list:
                win_amount = self.bet_high * 47.5
            else:
                win_amount = 0
            
            profit = win_amount - bet_total + rebate
            cum_rebate += rebate
            cum_profit += profit
            all_profits.append(profit)
            
            zero_str = " | ".join(f"{n:02d}" for n in zero_list)
            low_str = " | ".join(f"{n:02d}" for n in low_list)
            high_str = " | ".join(f"{n:02d}" for n in high_list)
            
            tags = ("loss",) if profit < 0 else ()
            
            self.tree.insert("", "end", values=(
                sorted_data[i].get("date", ""),
                sorted_data[i].get("period", ""),
                sorted_data[i].get("number", ""),
                f"{bet_total:.0f}",
                f"{rebate:.0f}",
                f"{profit:.0f}",
                f"{win_amount:.0f}",
                f"{cum_rebate:.0f}",
                f"{cum_profit:.0f}",
                f"{zero_str} ({len(zero_list)}个)",
                f"{low_str} ({len(low_list)}个)",
                f"{high_str} ({len(high_list)}个)"
            ), tags=tags)
        
        # 更新近期盈亏统计
        for p in [30, 50, 100, 150, 200, 300]:
            if len(all_profits) >= p:
                recent_sum = sum(all_profits[-p:])
                color = "green" if recent_sum > 0 else "red" if recent_sum < 0 else "black"
                self.stat_labels[p].config(text=f"近{p}期盈亏: {recent_sum:.0f} 元", foreground=color)
            else:
                self.stat_labels[p].config(text=f"近{p}期盈亏: 数据不足", foreground="gray")
        
        self.force_scrollbar()

    # 导入、添加、删除保持不变
    def import_txt(self):
        file = filedialog.askopenfilename(title="选择历史txt", filetypes=[("文本文件", "*.txt")])
        if not file: return
        new_data = parse_txt_file(file)
        if not new_data:
            messagebox.showerror("失败", "解析失败")
            return
        existing = {d["date"] for d in self.history}
        added = [item for item in new_data if item["date"] not in existing]
        if added:
            self.history.extend(added)
            save_data(self.history)
            messagebox.showinfo("成功", f"导入 {len(added)} 条")
            self.refresh_table()

    def add_record(self):
        try:
            date = self.date_entry.get().strip()
            period = self.period_entry.get().strip()
            number = int(self.num_entry.get().strip())
            if 1 <= number <= 49:
                self.history.append({"date": date, "period": period, "number": number})
                save_data(self.history)
                messagebox.showinfo("成功", "添加成功")
                self.refresh_table()
                self.num_entry.delete(0, tk.END)
        except:
            messagebox.showerror("错误", "特码请输入数字")

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选中一行")
            return
        if messagebox.askyesno("确认", "确定删除？"):
            for item in selected:
                date = self.tree.item(item)["values"][0]
                self.history = [rec for rec in self.history if rec.get("date") != date]
            save_data(self.history)
            self.refresh_table()

    def show_analysis(self):
        if not self.history:
            messagebox.showwarning("警告", "请先导入数据")
            return
        zero, low_list, high_list = analyze_next(self.history, self.strategy_n)
        
        win = tk.Toplevel(self)
        win.title("🔮 下一期智能分区")
        win.geometry("1200x650")
        
        f0 = ttk.LabelFrame(win, text=f"❌ 0元区 (禁注) (共 {len(zero)} 个)", padding=15)
        f0.pack(side="left", fill="both", expand=True, padx=8)
        tk.Label(f0, text=" | ".join(f"{n:02d}" for n in zero) if zero else "无", font=("微软雅黑", 15)).pack(pady=15)
        
        f_low = ttk.LabelFrame(win, text=f"🟠 {self.low_text} [近{self.strategy_n}期] (共 {len(low_list)} 个)", padding=15)
        f_low.pack(side="left", fill="both", expand=True, padx=8)
        tk.Label(f_low, text=" | ".join(f"{n:02d}" for n in low_list) if low_list else "无", font=("微软雅黑", 15)).pack(pady=15)
        
        f_high = ttk.LabelFrame(win, text=f"🟢 {self.high_text} (共 {len(high_list)} 个)", padding=15)
        f_high.pack(side="left", fill="both", expand=True, padx=8)
        
        text_high = tk.Text(f_high, height=10, wrap="word", font=("微软雅黑", 13))
        text_high.insert("end", " | ".join(f"{n:02d}" for n in high_list))
        text_high.config(state="disabled")
        text_high.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = LotteryAnalyzer()
    app.mainloop()
