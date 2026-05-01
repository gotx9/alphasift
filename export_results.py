# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
from pathlib import Path

def extract_runs_to_excel():
    import pandas as pd
    
    runs_dir = Path(__file__).parent / "data" / "runs"
    excel_path = Path(__file__).parent / "data" / "results_history.xlsx"
    
    if not runs_dir.exists():
        print("No runs directory found.")
        return
    
    existing_run_ids = set()
    if excel_path.exists():
        df_existing = pd.read_excel(excel_path)
        existing_run_ids = set(df_existing["run_id"].tolist())
        print(f"Found {len(existing_run_ids)} existing records.")
    
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
        print("No new runs to export.")
        return
    
    df_new = pd.DataFrame(records)
    
    if excel_path.exists():
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new
    
    df_all.to_excel(excel_path, index=False, engine="openpyxl")
    
    print(f"\n{'='*50}")
    print(f"Export Complete")
    print(f"{'='*50}")
    print(f"  New runs exported: {new_count}")
    print(f"  Total records:     {len(df_all)}")
    print(f"  Output file:       {excel_path}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    extract_runs_to_excel()
