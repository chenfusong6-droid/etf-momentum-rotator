# ETF动量轮动分析器

华泰柏瑞杯ETF AI交易巅峰赛辅助工具。基于华泰官方OpenClaw Skills，对沪深交易所上市ETF进行动量评分、技术面分析和轮动建议排序。

## 功能

| 工具 | 说明 |
|------|------|
| `rotate` | 动量轮动推荐 — 多因子评分排序 |
| `scan` | 行情扫描 — 批量查询实时行情 |
| `analyze` | 单只分析 — 技术面综合分析 |

## 安装

```bash
# 1. 放到OpenClaw Skills目录
mkdir -p ~/.openclaw/skills/etf-momentum-rotator
cp etf_momentum_rotator.py SKILL.md LICENSE ~/.openclaw/skills/etf-momentum-rotator/

# 2. 安装依赖
pip install requests

# 3. 配置API密钥
export HT_APIKEY="your_key_here"
# 或写入 ~/.htsc-skills/config
echo 'HT_APIKEY=your_key_here' > ~/.htsc-skills/config
```

## 使用

```bash
# 动量轮动推荐（默认18只比赛标的）
python3 etf_momentum_rotator.py rotate

# 指定ETF列表
python3 etf_momentum_rotator.py rotate --etf-list 510050,159919,588000

# 行情扫描
python3 etf_momentum_rotator.py scan --etf-list 510050,510300,510500

# 单只分析
python3 etf_momentum_rotator.py analyze --code 510050 --exchange SH
```

## 依赖

- Python 3.8+
- 华泰OpenClaw官方Skills（query-indicator, a-share-paper-trading等）
- HT_APIKEY 认证密钥

## 许可证

MIT
