# 策略文件说明

本目录存放选股策略 YAML 文件。

## 文件格式

每个 `.yaml` 文件定义一个选股策略，包含 `screening:` 段描述筛选规则。

详见 [策略编写指南](../docs/strategy-guide.md)。

## 可用策略

| 文件 | 名称 | 分类 | 说明 |
|------|------|------|------|
| `shrink_pullback.yaml` | 缩量回踩 | trend | 设计保留中，待日 K 特征支持完成后重新开放 |
| `dual_low.yaml` | 双低选股 | value | 低 PE + 低 PB 稳健筛选 |
| `volume_breakout.yaml` | 放量突破 | trend | 放量突破关键阻力位 |
