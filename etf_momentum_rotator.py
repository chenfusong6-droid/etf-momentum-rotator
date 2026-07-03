#!/usr/bin/env python3
"""
ETF动量轮动分析器 - 华泰柏瑞杯ETF AI交易巅峰赛辅助工具

基于华泰官方OpenClaw Skills，对ETF进行动量评分、技术面分析和轮动建议排序。
使用前请配置 HT_APIKEY 环境变量。

安装: 放到 ~/.openclaw/skills/etf-momentum-rotator/
依赖: requests (pip install requests)
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import Optional

import requests


# ===== 比赛默认ETF池（华泰柏瑞杯18只标的） =====
DEFAULT_ETF_POOL = [
    {"code": "510050", "name": "上证50ETF", "exchange": "SH"},
    {"code": "510300", "name": "沪深300ETF", "exchange": "SH"},
    {"code": "510500", "name": "中证500ETF", "exchange": "SH"},
    {"code": "588000", "name": "科创50ETF", "exchange": "SH"},
    {"code": "159919", "name": "沪深300ETF易方达", "exchange": "SZ"},
    {"code": "159949", "name": "创业板50ETF", "exchange": "SZ"},
    {"code": "159915", "name": "创业板ETF", "exchange": "SZ"},
    {"code": "512100", "name": "中证1000ETF", "exchange": "SH"},
    {"code": "510880", "name": "红利ETF", "exchange": "SH"},
    {"code": "159928", "name": "消费ETF汇添富", "exchange": "SZ"},
    {"code": "159865", "name": "养殖ETF", "exchange": "SZ"},
    {"code": "512480", "name": "半导体ETF", "exchange": "SH"},
    {"code": "515050", "name": "5GETF", "exchange": "SH"},
    {"code": "159766", "name": "旅游ETF", "exchange": "SZ"},
    {"code": "510230", "name": "金融ETF国泰", "exchange": "SH"},
    {"code": "159845", "name": "中证1000ETF华夏", "exchange": "SZ"},
    {"code": "512880", "name": "证券ETF", "exchange": "SH"},
    {"code": "518880", "name": "黄金ETF", "exchange": "SH"},
]


# ===== 配置 =====

def _load_config_file() -> dict:
    config_path = Path.home() / ".htsc-skills" / "config"
    if not config_path.exists():
        return {}
    result = {}
    for line in config_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def get_ht_api_key() -> str:
    """获取HT_APIKEY，优先级：环境变量 > 配置文件"""
    return os.environ.get("HT_APIKEY") or _load_config_file().get("HT_APIKEY", "")


# ===== 华泰Skills调用封装 =====

def call_ht_skill(skill_name: str, tool: str, **kwargs) -> dict:
    """调用本地已安装的华泰OpenClaw Skill"""
    skills_root = Path.home() / ".openclaw" / "skills"
    skill_map = {
        "query-indicator": skills_root / "query-indicator" / "query_indicator.py",
        "financial-analysis": skills_root / "financial-analysis" / "financial_analysis.py",
        "a-share-paper-trading": skills_root / "a-share-paper-trading" / "a_share_paper_trading.py",
        "select-stock": skills_root / "select-stock" / "select_stock.py",
        "watchlist-management": skills_root / "watchlist-management" / "watchlist_management.py",
    }

    script = skill_map.get(skill_name)
    if not script or not script.exists():
        return {"ok": False, "error": f"Skill {skill_name} 未安装，请先安装华泰官方Skill包"}

    cmd = [sys.executable, str(script), tool]
    for k, v in kwargs.items():
        arg_name = "--" + k.replace("_", "-")
        cmd.extend([arg_name, str(v)])

    import subprocess
    try:
        env = os.environ.copy()
        env["HT_APIKEY"] = get_ht_api_key()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        if result.returncode != 0:
            return {"ok": False, "error": result.stderr[:500]}
        return json.loads(result.stdout)
    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_quote(code: str, exchange: str = "SH") -> dict:
    """获取单只ETF实时行情"""
    return call_ht_skill("a-share-paper-trading", "getQuote",
                          stock_code=code, exchange=exchange)


def get_positions() -> dict:
    """获取当前持仓"""
    return call_ht_skill("a-share-paper-trading", "getPositions")


def get_balance() -> dict:
    """获取账户余额"""
    return call_ht_skill("a-share-paper-trading", "getAccountBalance")


# ===== ETF分析逻辑 =====

def calc_momentum_score(quote: dict) -> float:
    """基于行情数据计算动量评分（0-100）"""
    data = quote.get("data", {})
    if not data:
        return 0

    change_pct = float(data.get("changePct", 0) or 0)
    volume_ratio = float(data.get("volumeRatio", 1) or 1)
    amount = float(data.get("amount", 0) or 0)

    # 涨跌幅评分（权重50%）
    change_score = min(50, max(-50, change_pct * 5)) + 50
    change_score = max(0, min(100, change_score))

    # 量比评分（权重30%）
    vol_score = min(100, max(0, volume_ratio * 20))

    # 成交额评分（权重20%）
    amount_score = min(100, max(0, amount / 1_0000_0000 * 5))

    # 综合得分
    score = change_score * 0.50 + vol_score * 0.30 + amount_score * 0.20
    return round(min(100, max(0, score)), 1)


def format_etf_pool(etf_list_str: Optional[str] = None) -> list:
    """解析ETF列表，默认返回比赛池"""
    if not etf_list_str:
        return DEFAULT_ETF_POOL

    codes = [c.strip().upper() for c in etf_list_str.split(",")]
    result = []
    for code in codes:
        # 自动判断交易所：6开头SH，0/1/3开头SZ
        if code.startswith("6") or code.startswith("51"):
            exchange = "SH"
        else:
            exchange = "SZ"
        result.append({"code": code, "name": code, "exchange": exchange})
    return result


# ===== 工具实现 =====

def tool_rotate(etf_list: Optional[str] = None, top_n: int = 5) -> dict:
    """动量轮动推荐"""
    pool = format_etf_pool(etf_list)
    results = []

    for etf in pool:
        quote = get_quote(etf["code"], etf["exchange"])
        data = quote.get("data", {})

        if not data or not data.get("lastPrice"):
            continue

        score = calc_momentum_score(quote)
        results.append({
            "code": etf["code"],
            "name": etf.get("name", data.get("stockName", "")),
            "exchange": etf["exchange"],
            "price": data.get("lastPrice"),
            "change_pct": f"{data.get('changePct', 0):+.2f}%",
            "volume_ratio": round(float(data.get("volumeRatio", 0) or 0), 2),
            "amount": f"{float(data.get('amount', 0) or 0):.0f}",
            "momentum_score": score,
        })

    # 按动量评分排序
    results.sort(key=lambda x: x["momentum_score"], reverse=True)

    return {
        "ok": True,
        "data": {
            "total_scanned": len(results),
            "top_n": top_n,
            "rotation": results[:top_n],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": "动量评分基于涨跌幅(50%)+量比(30%)+成交额(20%)，仅供参考不构成投资建议",
        }
    }


def tool_scan(etf_list: str) -> dict:
    """行情扫描"""
    pool = format_etf_pool(etf_list)
    results = []

    for etf in pool:
        quote = get_quote(etf["code"], etf["exchange"])
        data = quote.get("data", {})
        results.append({
            "code": etf["code"],
            "name": data.get("stockName", etf.get("name", "")),
            "price": data.get("lastPrice"),
            "open": data.get("openPrice"),
            "high": data.get("highPrice"),
            "low": data.get("lowPrice"),
            "change_pct": f"{data.get('changePct', 0):+.2f}%",
            "volume": data.get("volume"),
            "amount": data.get("amount"),
        })

    return {"ok": True, "data": {"results": results, "count": len(results)}}


def tool_analyze(code: str, exchange: str = "SH") -> dict:
    """单只ETF技术面分析"""
    quote = get_quote(code, exchange)
    data = quote.get("data", {})

    if not data:
        return {"ok": False, "error": f"无法获取 {code} 行情数据"}

    score = calc_momentum_score(quote)

    return {
        "ok": True,
        "data": {
            "code": code,
            "name": data.get("stockName", ""),
            "price": data.get("lastPrice"),
            "change_pct": f"{data.get('changePct', 0):+.2f}%",
            "open": data.get("openPrice"),
            "high": data.get("highPrice"),
            "low": data.get("lowPrice"),
            "pre_close": data.get("preClosePrice"),
            "volume": data.get("volume"),
            "amount": data.get("amount"),
            "volume_ratio": round(float(data.get("volumeRatio", 0) or 0), 2),
            "amplitude": f"{data.get('amplitude', 0):.2f}%",
            "momentum_score": score,
            "analysis": (
                "偏强" if score >= 60 else
                "偏弱" if score <= 40 else
                "中性"
            ),
        }
    }


# ===== CLI入口 =====

TOOLS = {
    "rotate": {"func": tool_rotate, "help": "动量轮动推荐"},
    "scan": {"func": tool_scan, "help": "行情扫描"},
    "analyze": {"func": tool_analyze, "help": "单只ETF分析"},
}


def main():
    parser = argparse.ArgumentParser(
        description="ETF动量轮动分析器 - 华泰柏瑞杯辅助工具"
    )
    parser.add_argument("tool", choices=list(TOOLS.keys()), help="工具名称")
    parser.add_argument("--etf-list", default=None, help="ETF代码列表（逗号分隔）")
    parser.add_argument("--top-n", type=int, default=5, help="返回前N只推荐（默认5）")
    parser.add_argument("--code", default=None, help="ETF代码（用于analyze）")
    parser.add_argument("--exchange", default="SH", help="交易所 SH/SZ（默认SH）")

    args = parser.parse_args()

    # 检查API Key
    if not get_ht_api_key():
        result = {"ok": False, "error": "HT_APIKEY 未配置。请设置环境变量或写入 ~/.htsc-skills/config"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    tool_info = TOOLS[args.tool]
    func = tool_info["func"]

    try:
        if args.tool == "rotate":
            result = func(etf_list=args.etf_list, top_n=args.top_n)
        elif args.tool == "scan":
            if not args.etf_list:
                result = {"ok": False, "error": "scan 工具需要 --etf-list 参数"}
            else:
                result = func(etf_list=args.etf_list)
        elif args.tool == "analyze":
            if not args.code:
                result = {"ok": False, "error": "analyze 工具需要 --code 参数"}
            else:
                result = func(code=args.code, exchange=args.exchange)
        else:
            result = {"ok": False, "error": f"未知工具: {args.tool}"}
    except Exception as e:
        result = {"ok": False, "error": str(e)}

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
