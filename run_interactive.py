# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

STRATEGIES = {
    "1": ("dual_low", "双低选股", "低PE+低PB，适合价值投资"),
    "2": ("quality_value", "优质价值", "估值合理、流动性好、波动可控"),
    "3": ("volume_breakout", "放量突破", "成交量放大突破关键阻力位"),
    "4": ("capital_heat", "资金热度", "资金活跃但未过热的动量候选"),
    "5": ("oversold_reversal", "超跌反转", "跌幅可控且流动性仍在的修复候选"),
    "6": ("shrink_pullback", "缩量回踩", "均线多头趋势中回踩确认支撑"),
    "7": ("balanced_alpha", "综合发现", "多因子均衡，LLM友好，推荐"),
}


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    print()
    print("=" * 50)
    print("       AlphaSift Interactive Mode")
    print("       AlphaSift 交互式启动器")
    print("=" * 50)
    print()


def select_strategy():
    print("Step 1: Select Strategy / 选择策略")
    print("-" * 50)
    print()
    for key, (name, cn_name, desc) in STRATEGIES.items():
        print(f"  [{key}] {name:18} - {cn_name} ({desc})")
    print()
    
    while True:
        choice = input("Enter your choice (1-7) / 请选择 (1-7): ").strip()
        if choice in STRATEGIES:
            name, cn_name, desc = STRATEGIES[choice]
            print(f"\n✓ Selected / 已选择: {name} ({cn_name})")
            return name
        print("Invalid choice, please try again / 无效选择，请重试")


def select_llm():
    print()
    print("Step 2: LLM Ranking / LLM 排序")
    print("-" * 50)
    print("  [1] Yes / 是 - Use LLM for ranking / 使用 LLM 排序")
    print("  [2] No  / 否 - Skip LLM, faster / 跳过 LLM，更快")
    print()
    
    choice = input("Enter your choice (1-2) [default=1]: ").strip()
    if choice == "" or choice == "1":
        print("\n✓ LLM ranking: ENABLED / 已启用")
        return ""
    else:
        print("\n✓ LLM ranking: DISABLED / 已禁用")
        return "--no-llm"


def select_dsa():
    print()
    print("Step 3: DSA Deep Analysis / DSA 深度分析")
    print("-" * 50)
    print("  [1] Yes / 是 - Enable DSA deep analysis / 启用 DSA 深度分析")
    print("  [2] No  / 否 - Skip DSA, use local scorecard only / 跳过 DSA，仅使用本地评分")
    print()
    
    choice = input("Enter your choice (1-2) [default=2]: ").strip()
    if choice == "1":
        print("\n✓ DSA deep analysis: ENABLED / 已启用")
        return "--post-analyzer dsa"
    else:
        print("\n✓ DSA deep analysis: DISABLED / 已禁用 (local scorecard only)")
        return ""


def select_output_count():
    print()
    print("Step 4: Output Count / 输出数量")
    print("-" * 50)
    output_count = input("Max output candidates / 最大输出数量 [default=5]: ").strip()
    output_count = output_count if output_count.isdigit() else "5"
    print(f"  ✓ Max output: {output_count} candidates / {output_count} 只")
    return output_count


def get_alphasift_executable():
    venv_exe = os.path.join(os.path.dirname(sys.executable), "alphasift.exe")
    if os.path.exists(venv_exe):
        return venv_exe
    venv_script = os.path.join(os.path.dirname(sys.executable), "Scripts", "alphasift.exe")
    if os.path.exists(venv_script):
        return venv_script
    return "alphasift"


def build_command(strategy, use_llm, use_dsa, output_count):
    exe = get_alphasift_executable()
    parts = [
        f'"{exe}"', "screen", strategy,
        use_llm, use_dsa, "--save-run", "--explain",
        f"--max-output {output_count}"
    ]
    return " ".join(p for p in parts if p)


def print_summary(strategy, use_llm, use_dsa, output_count):
    print()
    print("=" * 50)
    print("           Execution Summary / 执行摘要")
    print("=" * 50)
    print(f"  Strategy / 策略:      {strategy}")
    print(f"  LLM Ranking / LLM:    {'Disabled / 禁用' if use_llm else 'Enabled / 启用'}")
    print(f"  DSA Analysis / DSA:   {'Enabled / 启用' if use_dsa else 'Disabled / 禁用'}")
    print(f"  Save Result / 保存:   Yes / 是 (自动)")
    print(f"  Max Output / 输出:    {output_count}")
    print("=" * 50)


def export_to_excel():
    import pandas as pd
    
    project_dir = Path(__file__).parent
    runs_dir = project_dir / "data" / "runs"
    excel_path = project_dir / "data" / "results_history.xlsx"
    
    if not runs_dir.exists():
        return None, 0
    
    existing_run_ids = set()
    if excel_path.exists():
        df_existing = pd.read_excel(excel_path)
        existing_run_ids = set(df_existing["run_id"].tolist())
    
    records = []
    new_count = 0
    
    for json_file in sorted(runs_dir.glob("*.json")):
        run_id = json_file.stem
        
        if run_id in existing_run_ids:
            continue
        
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        strategy = data.get("strategy", "")
        snapshot_count = data.get("snapshot_count", 0)
        after_filter_count = data.get("after_filter_count", 0)
        
        file_mtime = os.path.getmtime(json_file)
        analysis_time = datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M:%S")
        
        picks = data.get("picks", [])
        
        for pick in picks:
            dsa_summary = pick.get("post_analysis_summaries", {}).get("dsa", "")
            dsa_advice = pick.get("deep_analysis_operation_advice", "")
            dsa_prediction = pick.get("deep_analysis_trend_prediction", "")
            
            record = {
                "run_id": run_id,
                "analysis_time": analysis_time,
                "strategy": strategy,
                "snapshot_count": snapshot_count,
                "after_filter_count": after_filter_count,
                "rank": pick.get("rank", 0),
                "code": pick.get("code", ""),
                "name": pick.get("name", ""),
                "final_score": round(pick.get("final_score", 0), 2),
                "price": pick.get("price", 0),
                "change_pct": pick.get("change_pct", 0),
                "pe_ratio": round(pick.get("pe_ratio", 0) or 0, 2),
                "pb_ratio": round(pick.get("pb_ratio", 0) or 0, 2),
                "turnover_rate": round(pick.get("turnover_rate", 0) or 0, 2),
                "llm_score": pick.get("llm_score", 0),
                "llm_confidence": pick.get("llm_confidence", 0),
                "llm_sector": pick.get("llm_sector", ""),
                "llm_theme": pick.get("llm_theme", ""),
                "llm_thesis": pick.get("llm_thesis", ""),
                "ranking_reason": pick.get("ranking_reason", ""),
                "risk_summary": pick.get("risk_summary", ""),
                "dsa_status": pick.get("deep_analysis_status", ""),
                "dsa_advice": dsa_advice,
                "dsa_prediction": dsa_prediction,
                "dsa_summary": dsa_summary[:200] if dsa_summary else "",
            }
            records.append(record)
        
        new_count += 1
    
    if not records:
        return excel_path, 0
    
    df_new = pd.DataFrame(records)
    
    if excel_path.exists():
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new
    
    df_all.to_excel(excel_path, index=True, engine="openpyxl")
    
    return excel_path, new_count


def main():
    clear_screen()
    print_header()
    
    strategy = select_strategy()
    use_llm = select_llm()
    use_dsa = select_dsa()
    output_count = select_output_count()
    
    cmd = build_command(strategy, use_llm, use_dsa, output_count)
    
    print_summary(strategy, use_llm, use_dsa, output_count)
    print()
    print(f"Command / 命令:\n  {cmd}")
    print()
    
    confirm = input("Start analysis? / 开始分析? (y/n) [default=y]: ").strip().lower()
    if confirm not in ("", "y"):
        print("\nAnalysis cancelled. / 分析已取消。")
        input("\nPress Enter to exit / 按回车键退出...")
        return
    
    print()
    print("Starting AlphaSift analysis... / 开始分析...")
    print("=" * 50)
    print()
    
    try:
        subprocess.run(cmd, shell=True, check=False)
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted. / 分析已中断。")
    
    print()
    print("=" * 50)
    print("           Analysis Complete / 分析完成")
    print("=" * 50)
    print()
    
    print("Exporting results to Excel... / 导出结果到 Excel...")
    excel_path, new_count = export_to_excel()
    
    if excel_path and new_count > 0:
        print()
        print("=" * 50)
        print("           Excel Export Complete / Excel 导出完成")
        print("=" * 50)
        print(f"  New records:    {new_count}")
        print(f"  Excel path:     {excel_path}")
        print("=" * 50)
        print()
        print(f"✓ Excel file saved to / Excel 已保存至:")
        print(f"  {excel_path}")
    elif excel_path:
        print("  No new runs to export. / 没有新运行需要导出。")
        print(f"  Excel path: {excel_path}")
    
    print()
    print("Thank you for using AlphaSift! / 感谢使用!")
    input("\nPress Enter to exit / 按回车键退出...")


if __name__ == "__main__":
    main()
