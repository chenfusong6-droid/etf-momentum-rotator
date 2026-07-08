---
name: etf-momentum-rotator
description: ETF动量轮动分析器。对沪深交易所上市ETF进行动量评分、技术面分析和轮动建议排序，适用于华泰柏瑞杯ETF AI交易巅峰赛。
user-invocable: true
metadata:
  openclaw:
    emoji: 🔄
    skillKey: etf-momentum-rotator
    author: NaifuOS
    requires:
      bins: ["python3"]
      env: ["HT_APIKEY"]
---

# ETF动量轮动分析器 Skill

对指定ETF池进行动量评分、技术面分析和轮动建议排序。适用于华泰柏瑞杯ETF AI交易巅峰赛的18只标的。

## 策略核心：多因子动量评分

本Skill的核心是一个三因子动量评分模型：

| 因子 | 权重 | 说明 |
|------|:----:|------|
| 涨跌幅 | 50% | 近期价格动能，捕捉趋势方向 |
| 量比 | 30% | 成交量变化，确认动能有效性 |
| 成交额 | 20% | 资金参与度，过滤流动性不足标的 |

评分归一化到0-100区间，得分越高代表短期动量越强。每日运行可识别资金正在流入的ETF板块，实现行业轮动。

## 工具

### `rotate` — 动量轮动推荐
对ETF候选列表进行多维度动量评分，输出按综合得分排序的轮动推荐表。

**参数：**
- `etf-list` (可选): 逗号分隔的ETF代码列表，默认使用比赛18只标的
- `top-n` (可选): 返回前N只推荐，默认5只

**输出：** 按动量得分排名的ETF列表，含价格、涨跌幅、成交量变化、动量得分

**执行：** `python3 etf_momentum_rotator.py rotate [--etf-list <codes>] [--top-n <N>]`

### `scan` — 行情扫描
快速扫描指定ETF的实时行情数据。

**参数：**
- `etf-list` (必填): 逗号分隔的ETF代码列表

**输出：** 各ETF的实时价格、涨跌幅、成交量、成交额

**执行：** `python3 etf_momentum_rotator.py scan --etf-list <codes>`

### `analyze` — 单只ETF分析
对单只ETF进行技术面综合分析。

**参数：**
- `code` (必填): ETF代码
- `exchange` (可选): 交易所，默认SH

**输出：** 技术面指标、资金流向简析

**执行：** `python3 etf_momentum_rotator.py analyze --code <code> [--exchange <SH|SZ>]`
