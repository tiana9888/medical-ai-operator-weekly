#!/usr/bin/env python3
"""Read-only structural review of a complete Markdown weekly. Not fact checking."""
import argparse
import json
import re
from pathlib import Path

SECTIONS = [
    "本周一句判断", "本周最重要的3个信号", "本周深度分析",
    "一周事件速览", "给经营者的本周行动建议",
]
CLOSING = [
    "如果本期内容对您有帮助，欢迎点赞、推荐，或转发给有需要的同事与朋友；",
    "您有任何医疗AI专业观察与见解，欢迎联系《医疗AI经营者周报》编辑组。",
]


def check(text):
    errors, warnings = [], []
    lines = [re.sub(r"^\s*#{1,6}\s*", "", s).strip().replace("**", "") for s in text.splitlines()]
    normalized = [re.sub(r"\s+", "", s) for s in lines]
    positions = []
    for i, title in enumerate(SECTIONS, 1):
        pattern = rf"^0{i}[｜|]{re.escape(title)}(?:[:：].*)?$"
        found = [n for n, s in enumerate(normalized) if re.match(pattern, s)]
        if len(found) != 1:
            errors.append(f"栏目0{i}应出现一次，实际{len(found)}次")
        positions.append(found[0] if found else None)
    endings = [n for n, s in enumerate(normalized) if s == "结语"]
    if len(endings) != 1:
        errors.append("结语标题应出现一次")
    valid = all(p is not None for p in positions) and len(endings) == 1
    if valid:
        bounds = positions + endings
        if bounds != sorted(bounds) or len(set(bounds)) != 6:
            errors.append("五栏目与结语顺序错误")
        else:
            signal = normalized[positions[1] + 1:positions[2]]
            labels = [re.match(r"^信号([一二三四五六七八九十]+)[:：｜|]", s) for s in signal]
            labels = [m.group(1) for m in labels if m]
            if labels != ["一", "二", "三"]:
                errors.append("信号须依次为一、二、三且各出现一次")
            joined = "\n".join(signal)
            if joined.count("编辑点评：") < 3 or joined.count("来源与延伸阅读：") < 3:
                errors.append("三个信号未各配置点评与来源行")
            deep = lines[positions[2] + 1:positions[3]]
            if not any(re.match(r"^\|?\s*:?-{3,}", s) for s in deep):
                warnings.append("深度分析未检测到Markdown表格，请确认存在有效比较表")
            brief = normalized[positions[3] + 1:positions[4]]
            n_events = sum(bool(re.match(r"^【.+?】", s)) for s in brief)
            if not 3 <= n_events <= 5:
                warnings.append(f"速览检测到{n_events}条，通常为3—5条")
            if "\n".join(brief).count("来源与延伸阅读：") < n_events:
                errors.append("速览来源行少于事件条数")
            action = "\n".join(normalized[positions[4] + 1:endings[0]])
            roles = [r"医院管理者", r"药企", r"医疗AI(?:企业|公司)经营者", r"体检", r"投资人"]
            matches = [re.search(r, action) for r in roles]
            if not all(matches):
                errors.append("行动建议未覆盖全部五类角色")
            elif [m.start() for m in matches] != sorted(m.start() for m in matches):
                errors.append("行动建议角色顺序错误")
    for sentence in CLOSING:
        if sentence not in text:
            errors.append("缺少固定互动话术：" + sentence)
    if not re.search(r"《医疗AI经营者周报》第\d{3,}期[:：]", "\n".join(normalized)):
        errors.append("未检测到带期数的标准主标题")
    if re.search(r"\[(?:期数|本期|待填|发布日期|主体|分类|事件标题|发布方)[^\]]*\]|\bTODO\b", text):
        errors.append("检测到未替换的模板占位符")
    for word in ["彻底", "颠覆", "必然", "全球首个", "零风险"]:
        if word in text:
            warnings.append(f"人工检查强断言：{word}")
    return {
        "structural_pass": not errors,
        "errors": errors,
        "warnings": warnings,
        "characters_excluding_whitespace": len(re.sub(r"\s", "", text)),
        "fact_verification": "未执行：须另核原始来源、医疗边界与经营推断",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", type=Path)
    args = parser.parse_args()
    result = check(args.draft.read_text(encoding="utf-8"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["structural_pass"] else 1)


if __name__ == "__main__":
    main()
