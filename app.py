import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from collections import defaultdict

st.set_page_config(page_title="特码智能分区分析器", layout="wide", page_icon="🎯")

st.title("🎯 特码智能分区分析器（iPhone完美版）")
st.markdown("**12种策略 · 当期计算 · 亏损绿色 · 近期统计**")

# 数据持久化 + 自动清理无效日期记录（彻底解决崩溃）
DATA_FILE = "lottery_history.json"
if "history" not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
            # 只保留有效日期记录，防止崩溃
            st.session_state.history = [
                r for r in raw 
                if isinstance(r.get("date"), str) and len(r["date"]) >= 8
            ]
    else:
        st.session_state.history = []

def save_history():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.history, f, ensure_ascii=False, indent=2)

# ==================== 导入历史TXT ====================
st.subheader("📥 导入历史TXT")
uploaded_file = st.file_uploader("选择你的历史数据TXT文件", type=["txt"], key="uploader")
if uploaded_file is not None:
    content = uploaded_file.getvalue().decode("utf-8")
    lines = content.splitlines()
    new_data = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if '-' in line and len(line) > 8:
            date = line
            i += 1
            if i < len(lines):
                next_line = lines[i].strip()
                if '期' in next_line:
                    try:
                        parts = next_line.split()
                        period = parts[0]
                        number = int(''.join(filter(str.isdigit, parts[-1])))
                        if 1 <= number <= 49:
                            new_data.append({"date": date, "period": period, "number": number})
                    except:
                        pass
        i += 1
    if new_data:
        existing = {d["date"] for d in st.session_state.history}
        added = [item for item in new_data if item["date"] not in existing]
        if added:
            st.session_state.history.extend(added)
            save_history()
            st.success(f"✅ 成功导入 {len(added)} 条记录！")
            st.rerun()

# ==================== 策略选择 ====================
strategy = st.selectbox("选择投注策略", [
    "近4期500","近5期500","近6期500","近7期500","近8期500","近9期500",
    "近4期200","近5期200","近6期200","近7期200","近8期200","近9期200"
])

n = int(strategy.split('近')[1].split('期')[0])
bet_low = 500 if '500' in strategy else 200
bet_high = 1000 if '500' in strategy else 1500
low_name = "500元区" if '500' in strategy else "200元区"
high_name = "1000元区" if '500' in strategy else "1500元区"

# 分析函数（仅增加容错，不改变任何原有逻辑）
def analyze_next(history, strategy_n):
    if not history:
        return [], [], list(range(1, 50))
    # 只使用有效日期记录
    valid_history = [r for r in history if isinstance(r.get("date"), str) and len(r["date"]) >= 8]
    sorted_history = sorted(valid_history, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), reverse=True)
    zero_zone = {sorted_history[0]["number"]} if sorted_history else set()
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

# ==================== 主表格（最新日期在最下方） ====================
if st.session_state.history:
    df_data = []
    cum_rebate = cum_profit = 0.0
    all_profits = []
    # 升序排序（容错版）
    valid_history = [r for r in st.session_state.history if isinstance(r.get("date"), str) and len(r["date"]) >= 8]
    sorted_history = sorted(valid_history, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))
    
    for i, row in enumerate(sorted_history):
        past = sorted_history[:i]
        zero, low, high = analyze_next(past, n)
        win_num = row["number"]
        bet_total = bet_low * len(low) + bet_high * len(high)
        rebate = bet_total * 0.03
        if win_num in low:
            win_amount = bet_low * 47.5
        elif win_num in high:
            win_amount = bet_high * 47.5
        else:
            win_amount = 0
        profit = win_amount - bet_total + rebate
        cum_rebate += rebate
        cum_profit += profit
        all_profits.append(profit)
        
        df_data.append({
            "日期": row["date"],
            "期号": row["period"],
            "特码": row["number"],
            "当期投注总额": bet_total,
            "当期反水": round(rebate),
            "当期盈亏": round(profit),
            "当期中奖额": round(win_amount),
            "累积反水": round(cum_rebate),
            "累积盈亏": round(cum_profit),
            "0元区": " | ".join(f"{n:02d}" for n in zero) + f" ({len(zero)}个)",
            low_name: " | ".join(f"{n:02d}" for n in low) + f" ({len(low)}个)",
            high_name: " | ".join(f"{n:02d}" for n in high) + f" ({len(high)}个)"
        })
    
    df = pd.DataFrame(df_data)

    # ==================== 新增：表头显示设置 ====================
    st.subheader("📋 表头显示设置")
    all_cols = list(df.columns)
    selected_cols = st.multiselect("选择要显示的列（可多选）", options=all_cols, default=all_cols, key="col_select")
    
    display_df = df[selected_cols]
    
    st.dataframe(display_df.style.map(lambda x: 'color: #00AA00; font-weight: bold' if isinstance(x, (int,float)) and x < 0 else '', subset=["当期盈亏"]),
                 use_container_width=True, height=650)

    # 近期统计
    st.subheader("📊 近期盈亏统计")
    cols = st.columns(6)
    for idx, p in enumerate([30,50,100,150,200,300]):
        if len(all_profits) >= p:
            s = sum(all_profits[-p:])
            color = "#00AA00" if s > 0 else "#e74c3c"
            cols[idx].metric(f"近{p}期", f"{s:,} 元")
            cols[idx].markdown(f"<span style='color:{color}'>{'盈利' if s>0 else '亏损' if s<0 else '持平'}</span>", unsafe_allow_html=True)

# 下一期分析
with st.expander("🚀 查看下一期智能分区", expanded=True):
    if st.session_state.history:
        zero, low, high = analyze_next(st.session_state.history, n)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("0元区 (禁注)", f"{len(zero)} 个")
            st.write(" | ".join(f"{n:02d}" for n in zero) or "无")
        with col2:
            st.metric(low_name, f"{len(low)} 个")
            st.write(" | ".join(f"{n:02d}" for n in low) or "无")
        with col3:
            st.metric(high_name, f"{len(high)} 个")
            st.write(" | ".join(f"{n:02d}" for n in high) or "无")
    else:
        st.info("请先导入数据或添加记录")

# 侧边栏手动添加 + 一键清除（已确保始终显示）
with st.sidebar:
    st.header("✍️ 手动添加新期")
    col1, col2 = st.columns(2)
    with col1:
        new_date = st.date_input("日期", value=datetime.today())
        new_period = st.text_input("期号", "XXX期")
    with col2:
        new_num = st.number_input("特码", 1, 49, 25)
    if st.button("✅ 添加记录"):
        st.session_state.history.append({
            "date": new_date.strftime("%Y-%m-%d"),
            "period": new_period,
            "number": int(new_num)
        })
        save_history()
        st.success("添加成功！")
        st.rerun()

    st.divider()
    if st.button("🗑️ **一键清除所有历史数据**", type="secondary"):
        if st.checkbox("我确定要删除所有数据（不可恢复）"):
            st.session_state.history = []
            save_history()
            st.success("✅ 已清除所有历史数据！")
            st.rerun()

st.caption("数据自动保存在 lottery_history.json · 可添加到主屏幕使用")
