#!/usr/bin/env python3
"""Generate content-specific benchmark artwork.

Each benchmark has an explicit visual scene.  Shared primitives keep the set
coherent, while the object mix and topology describe the actual task instead
of routing broad subcategories into generic charts.

Run:
    python3 tools/gen_images.py --force   # redraw every asset
    python3 tools/gen_images.py --check   # validate coverage and freshness
"""

import json
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "benchmarks"
OUT = ROOT / "static" / "images" / "benchmarks"
FORCE = "--force" in sys.argv
CHECK = "--check" in sys.argv

W, H = 480, 360
BG = "#f4f7fb"
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#dbe4ee"
PANEL = "#ffffff"
PALE = "#94a3b8"
DOMAIN_PALETTES = {
    "agent": ("#2563eb", "#7c3aed"),
    "aigc": ("#7c3aed", "#db2777"),
    "llm": ("#0f766e", "#2563eb"),
    "multimodal": ("#4f46e5", "#c026d3"),
}


def V(name, desc, layout, *objects):
    return {"name": name, "desc": desc, "layout": layout, "objects": objects}


# Explicit coverage is intentional: a new benchmark must choose what it depicts.
VISUAL_SPECS = {
    "acadreason": V("ACADREASON", "A research question gathering papers, citations, and cross-disciplinary evidence into a synthesis.", "orbit", ("paper", "papers"), ("citation", "citations"), ("search", "search"), ("report", "synthesis")),
    "artifactsbench": V("ArtifactsBench", "Executable visual code moving from an editor into an interactive browser artifact and visual checks.", "flow", ("code", "editor"), ("browser", "artifact"), ("cursor", "interact"), ("check", "visual QA")),
    "autokaggle": V("AutoKaggle", "Raw tables moving through feature engineering and modeling into a validated Kaggle submission.", "flow", ("table", "raw data"), ("features", "features"), ("model", "model"), ("submission", "valid CSV")),
    "automv": V("AutoMV", "A song waveform aligned to storyboard shots and evaluated with a professional music-video rubric.", "merge", ("waveform", "song"), ("video", "storyboard"), ("rubric", "12 criteria")),
    "chinese_safetyqa": V("Chinese SafetyQA", "Chinese safety questions grounded in policy and culture sources, checked for factuality and harmlessness.", "merge", ("qa", "中文问题"), ("culture", "sources"), ("shield", "safe facts")),
    "chinese_simpleqa": V("Chinese SimpleQA", "A short Chinese factual question traced to an authoritative source and a concise answer.", "flow", ("qa", "问题"), ("citation", "source"), ("answer", "短答案")),
    "cii_bench": V("CII-Bench", "A Chinese image interpreted through cultural context, metaphor, and emotion.", "flow", ("image", "image"), ("culture", "culture"), ("meaning", "implication")),
    "code_simpleqa": V("CodeSimpleQA", "English and Chinese programming questions grounded in documentation and code facts.", "merge", ("code", "API facts"), ("language", "EN / 中文"), ("qa", "1,498 QA")),
    "codeeditorbench": V("CodeEditorBench", "Existing code revised through a visible diff and accepted by execution tests.", "flow", ("code", "before"), ("diff", "+ / − diff"), ("check", "tests pass")),
    "codetracer": V("CodeTracer", "An execution trace with the first faulty state located and verified.", "flow", ("code", "program"), ("trace", "states"), ("target", "fault"), ("check", "located")),
    "conceptmath": V("ConceptMath", "Bilingual math problems mapped to a concept tree that exposes a weak concept.", "merge", ("language", "双语"), ("concept", "concepts"), ("diagnostic", "weak spot")),
    "cot_error_detection": V("Long CoT Error Detection", "A long chain of reasoning with the earliest incorrect step detected and marked.", "flow", ("trace", "long CoT"), ("break", "first error"), ("critic", "detect")),
    "criticlean": V("CriticLean", "A Lean proof containing a faulty step, reviewed by a critic and rechecked by the compiler.", "flow", ("proof", "Lean proof"), ("critic", "critic"), ("checker", "Lean check")),
    "dr3_eval": V("DR3-Eval", "Multimodal evidence processed in a sealed environment into a cited, reproducible research report.", "merge", ("multimodal", "evidence"), ("sandbox", "sealed env"), ("report", "cited report")),
    "edgebench": V("EdgeBench", "An agent learning from real environment interactions over a long training horizon.", "timeline", ("environment", "environment"), ("clock", "12–72 h"), ("chart", "learning"), ("check", "competence")),
    "finder": V("FINDER", "A research query expanded into sources, a structured evidence checklist, and an analyst report.", "flow", ("search", "query"), ("citation", "sources"), ("checklist", "419 checks"), ("report", "report")),
    "formalmath": V("FormalMATH", "A natural-language theorem translated into a Lean goal, proof steps, and a compiler-checked result.", "flow", ("theorem", "theorem"), ("proof", "Lean proof"), ("checker", "verified")),
    "fullstack_bench": V("FullStack Bench", "A browser frontend connected through an API to a database and verified end to end.", "merge", ("browser", "frontend"), ("api", "API"), ("database", "database"), ("check", "E2E tests")),
    "hellobench": V("HelloBench", "A long generated document held together by a coherence thread while repetition is detected.", "split", ("scroll", "long text"), ("coherence", "coherence"), ("loop", "repetition")),
    "if_vidcap": V("IF-VidCap", "Video frames and explicit format constraints producing an instruction-following caption.", "merge", ("video", "video"), ("constraints", "constraints"), ("caption", "caption ✓")),
    "ii_bench": V("II-Bench", "Visible image objects leading to implied emotion, intent, and social meaning.", "split", ("image", "surface"), ("meaning", "implication")),
    "inverse_ifeval": V("Inverse IFEval", "A direct instruction overriding a conflicting learned prior and passing constraint checks.", "flow", ("prior", "prior"), ("instruction", "instruction"), ("check", "followed")),
    "iv_bench": V("IV-Bench", "A reference image grounding evidence from a long video before a reasoning answer.", "merge", ("reference", "reference"), ("video", "long video"), ("answer", "reasoning")),
    "kor_bench": V("KOR-Bench", "Novel symbolic rules applied through a reasoning chain without relying on memorized knowledge.", "flow", ("rules", "novel rules"), ("trace", "reason"), ("answer", "answer")),
    "korgym": V("KORGym", "An agent inferring changing game rules, acting on a board, and learning from the result.", "cycle", ("rules", "rules"), ("game", "game"), ("agent", "agent"), ("score", "feedback")),
    "lime": V("LIME", "A large multimodal sample pool filtered for leakage, easiness, and low diagnostic value.", "flow", ("samplewall", "sample pool"), ("funnel", "recurate"), ("benchmark", "compact set")),
    "longform_rewardbench": V("Long-form RewardBench", "Two long responses compared by a reward judge across five task families.", "compare", ("scroll", "response A"), ("scale", "reward judge"), ("scroll", "response B")),
    "m2rc_eval": V("M2RC-Eval", "Repository files and sibling context filling a missing code region and passing tests.", "merge", ("repo", "repository"), ("missing", "completion"), ("check", "tests")),
    "mammoth2": V("MAmmoTH2", "Web documents mined and refined into roughly ten million instruction-response pairs for training.", "flow", ("web", "web data"), ("funnel", "mine + refine"), ("pairs", "~10M pairs"), ("model", "reasoning LM")),
    "mceval": V("McEval", "Code generation, completion, and explanation evaluated across forty programming languages.", "orbit", ("language", "40 languages"), ("code", "generate"), ("missing", "complete"), ("qa", "explain")),
    "mm_browsecomp": V("MM-BrowseComp", "A browsing agent combining web pages, images, charts, and video evidence into one answer.", "orbit", ("web", "web"), ("image", "image"), ("video", "video"), ("answer", "answer")),
    "mt_bench_101": V("MT-Bench-101", "A multi-turn conversation carrying a growing checklist of fine-grained instructions across turns.", "flow", ("chat", "turn 1"), ("constraints", "constraints"), ("chat", "later turns"), ("check", "retained")),
    "mt_video_bench": V("MT-Video-Bench", "Multiple conversational turns pointing to different moments in the same video.", "orbit", ("video", "video"), ("chat", "turn 1"), ("chat", "turn 2"), ("chat", "turn 3")),
    "mtu_bench": V("MTU-Bench", "Single and multi-turn requests orchestrating one or many tools in four evaluation settings.", "matrix", ("chat", "single turn"), ("tools", "single tool"), ("constraints", "multi turn"), ("orchestrate", "multi tool")),
    "multi_docker_eval": V("Multi-Docker-Eval", "A Compose specification instantiating connected containers that pass health checks.", "flow", ("compose", "compose.yml"), ("containers", "services"), ("network", "network"), ("check", "healthy")),
    "mvu_eval": V("MVU-Eval", "Evidence retrieved and compared across several videos before producing an answer.", "merge", ("video", "video A"), ("video", "video B"), ("compare", "retrieve"), ("answer", "answer")),
    "nl2repo_bench": V("NL2Repo-Bench", "A natural-language specification expanding into source files, tests, and repository configuration.", "flow", ("spec", "SPEC"), ("repo", "src / config"), ("checklist", "tests")),
    "omni_math": V("Omni-MATH", "Algebra, geometry, and number theory problems organized across Olympiad difficulty levels.", "merge", ("algebra", "algebra"), ("geometry", "geometry"), ("number", "number theory"), ("medal", "Olympiad")),
    "omnibench": V("OmniBench", "Text, image, and audio inputs combined by one tri-modal reasoning model.", "merge", ("text", "text"), ("image", "image"), ("audio", "audio"), ("answer", "joint answer")),
    "omnicap_if": V("OmniCap-IF", "Video and audio evidence constrained by format and content instructions before captioning.", "merge", ("video", "video"), ("audio", "audio"), ("constraints", "instructions"), ("caption", "caption")),
    "omnivideobench": V("OmniVideoBench", "Synchronized visual and audio streams queried together for video understanding.", "merge", ("video", "visual"), ("audio", "audio"), ("qa", "joint QA")),
    "opencodeinterpreter": V("OpenCodeInterpreter", "A code model generating, executing, reading terminal feedback, and repairing its answer.", "cycle", ("code", "generate"), ("terminal", "execute"), ("diff", "repair"), ("check", "pass")),
    "opencoder": V("OpenCoder", "Raw code cleaned into a reproducible corpus, training recipe, and open model checkpoints.", "flow", ("web", "raw code"), ("funnel", "clean + dedup"), ("dataset", "RefineCode"), ("model", "checkpoints")),
    "oprover": V("OProver", "Retrieved Lean proofs feeding an attempt, compiler feedback, and iterative repair loop.", "cycle", ("search", "retrieve"), ("proof", "attempt"), ("checker", "compiler"), ("diff", "repair")),
    "ouro": V("Ouro", "A shared transformer block looping at variable depth to allocate latent compute per token.", "cycle", ("token", "token"), ("layers", "shared block"), ("loop", "× depth"), ("chart", "allocation")),
    "owl": V("OWL", "An IT alert traced through server state and a runbook into a verified operational fix.", "flow", ("server", "systems"), ("alert", "alert"), ("runbook", "runbook"), ("check", "resolved")),
    "roleagent": V("RoleAgent", "A script converted into persona memory, role dialogue, and evaluator feedback.", "flow", ("script", "script"), ("persona", "memory"), ("chat", "role play"), ("check", "evaluate")),
    "rolellm": V("RoleLLM", "Character knowledge, speaking style, and persona traits conditioning role-play dialogue.", "merge", ("book", "knowledge"), ("style", "style"), ("persona", "persona"), ("chat", "dialogue")),
    "safedialbench": V("SafeDialBench", "Escalating multi-turn jailbreak attempts consistently blocked by a conversational safety policy.", "flow", ("chat", "dialogue"), ("attack", "jailbreak"), ("shield", "defend"), ("check", "ASR ↓")),
    "scalelong": V("ScaleLong", "Evidence distributed across short, medium, and hour-scale video spans before retrieval.", "timeline", ("video", "seconds"), ("clock", "minutes"), ("clock", "hours"), ("answer", "retrieve")),
    "supergpqa": V("SuperGPQA", "Expert questions spanning hundreds of academic disciplines and long-tail subject knowledge.", "orbit", ("book", "disciplines"), ("qa", "expert QA"), ("taxonomy", "285 fields"), ("answer", "overall")),
    "swe_compass": V("SWE-Compass", "A software issue moving through repository navigation, agent edits, and test verification.", "orbit", ("issue", "issue"), ("repo", "repository"), ("agent", "coding agent"), ("check", "tests")),
    "t2av_compass": V("T2AV-Compass", "A text prompt generating synchronized video and audio evaluated for alignment.", "merge", ("text", "prompt"), ("video", "video"), ("audio", "audio"), ("sync", "alignment")),
    "tablebench": V("TableBench", "A reasoning path crossing table rows and columns before calculation and verification.", "flow", ("table", "complex table"), ("path", "reasoning"), ("formula", "calculate"), ("answer", "verify")),
    "tvir": V("TVIR", "Cited text and visual evidence assembled into an interleaved research report.", "merge", ("citation", "sources"), ("image", "figures"), ("text", "text"), ("report", "report")),
    "usb": V("USB", "Text, image, and audio safety attacks evaluated through one unified risk shield.", "merge", ("text", "text"), ("image", "image"), ("audio", "audio"), ("shield", "unified safety")),
    "vidcapbench": V("VidCapBench", "A video caption scored for aesthetics, content, motion, and physical understanding.", "orbit", ("video", "video"), ("rubric", "aesthetics"), ("rubric", "motion"), ("rubric", "physics")),
    "vidic": V("ViDiC", "Two similar videos compared frame by frame to describe their precise differences.", "compare", ("video", "video A"), ("diff", "differences"), ("video", "video B")),
    "web_compass": V("WebCompass", "Browser artifacts generated, edited, and repaired before specification and interaction checks.", "flow", ("browser", "generate"), ("browser", "edit"), ("browser", "repair"), ("check", "verify")),
    "workflow_gym": V("Workflow-GYM", "A professional brief carried through planning, GUI actions, verification, and a finished deliverable.", "flow", ("brief", "brief"), ("ui", "GUI actions"), ("checklist", "verify"), ("submission", "deliverable")),
    "worldtravel": V("WorldTravel", "A travel route checked against dates, tickets, hotels, timing, and feasibility constraints.", "orbit", ("map", "route"), ("calendar", "dates"), ("ticket", "tickets"), ("hotel", "hotel"), ("check", "feasible")),
    "yue": V("YuE", "Lyrics expanded into structured song sections with aligned vocal and accompaniment tracks.", "flow", ("lyrics", "lyrics"), ("stage", "song form"), ("waveform", "vocal + music"), ("music", "full song")),
}


def txt(x, y, value, size=11, fill=MUTED, anchor="middle", weight=500):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
            f'font-family="IBM Plex Mono, Menlo, monospace" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}">{escape(str(value))}</text>')


def short(value, n=15):
    return value if len(value) <= n else value[:n - 1] + "…"


def box(x, y, w=82, h=60, stroke=LINE, fill=PANEL, r=10):
    return f'<rect x="{x-w/2:g}" y="{y-h/2:g}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.7"/>'


def icon(kind, x, y, label, accent, variant):
    """Draw one semantic object centered at x/y; labels are secondary to shape."""
    p = []
    left, top = x - 34, y - 27
    if kind in {"paper", "citation", "report", "runbook", "script", "lyrics", "spec", "brief", "dataset", "pairs", "answer", "caption", "instruction", "checklist"}:
        p.append(f'<path d="M {left+8} {top} H {left+52} L {left+66} {top+14} V {top+54} H {left+8} Z" fill="{PANEL}" stroke="{accent}" stroke-width="2"/>')
        p.append(f'<path d="M {left+52} {top} V {top+14} H {left+66}" fill="none" stroke="{accent}" stroke-width="2"/>')
        lines = 3 if kind not in {"checklist", "citation"} else 4
        for j in range(lines):
            yy = top + 19 + j * 9
            if kind == "checklist":
                p.append(f'<rect x="{left+15}" y="{yy-4}" width="5" height="5" rx="1" fill="{accent}"/>')
                x1 = left + 26
            elif kind == "citation":
                p.append(txt(left + 17, yy + 1, str(j + 1), 7, accent))
                x1 = left + 26
            else:
                x1 = left + 15
            p.append(f'<line x1="{x1}" y1="{yy}" x2="{left+56-j*3}" y2="{yy}" stroke="{PALE}" stroke-width="2" opacity=".75"/>')
    elif kind in {"code", "terminal", "browser", "diff", "table", "compose", "ui", "web", "alert"}:
        p.append(box(x, y, 82, 58, accent if kind in {"diff", "alert"} else LINE, PANEL, 8))
        p.append(f'<line x1="{x-41}" y1="{y-14}" x2="{x+41}" y2="{y-14}" stroke="{LINE}" stroke-width="1.5"/>')
        p.extend([f'<circle cx="{x-29+i*9}" cy="{y-21}" r="2.2" fill="{accent if i == 0 else LINE}"/>' for i in range(3)])
        if kind == "table":
            for j in range(1, 3):
                p.append(f'<line x1="{x-30+j*20}" y1="{y-8}" x2="{x-30+j*20}" y2="{y+21}" stroke="{PALE}" opacity=".55"/>')
            for j in range(1, 3):
                p.append(f'<line x1="{x-29}" y1="{y-8+j*10}" x2="{x+29}" y2="{y-8+j*10}" stroke="{PALE}" opacity=".55"/>')
        elif kind == "diff":
            p.append(txt(x - 21, y + 5, "−", 18, "#ff806e", weight=700))
            p.append(txt(x + 21, y + 5, "+", 18, "#45d6a5", weight=700))
            p.append(f'<line x1="{x}" y1="{y-8}" x2="{x}" y2="{y+20}" stroke="{LINE}"/>')
        elif kind == "terminal":
            p.append(txt(x - 28, y + 5, "$", 14, accent, anchor="start", weight=700))
            p.append(f'<line x1="{x-13}" y1="{y+2}" x2="{x+27}" y2="{y+2}" stroke="{PALE}" stroke-width="2"/>')
        elif kind == "browser" or kind == "web":
            p.append(f'<rect x="{x-27}" y="{y-5}" width="54" height="25" rx="3" fill="none" stroke="{PALE}" opacity=".75"/>')
            p.append(f'<circle cx="{x-16}" cy="{y+5}" r="5" fill="{accent}" opacity=".7"/>')
        elif kind == "alert":
            p.append(txt(x, y + 11, "!", 28, "#ff806e", weight=700))
        else:
            for j, ww in enumerate((46, 57, 35)):
                p.append(f'<line x1="{x-28}" y1="{y-4+j*9}" x2="{x-28+ww}" y2="{y-4+j*9}" stroke="{accent if j == variant % 3 else PALE}" stroke-width="3" opacity=".8"/>')
    elif kind in {"repo", "taxonomy", "concept"}:
        p.append(f'<circle cx="{x-25}" cy="{y-17}" r="7" fill="{accent}"/>')
        for j, (dx, dy) in enumerate(((10, -17), (10, 4), (34, 18))):
            p.append(f'<path d="M {x-18} {y-17} H {x-4} V {y+dy} H {x+dx-7}" fill="none" stroke="{LINE}" stroke-width="2"/>')
            p.append(f'<rect x="{x+dx-7}" y="{y+dy-7}" width="24" height="14" rx="4" fill="{PANEL}" stroke="{PALE}"/>')
    elif kind in {"video", "image", "reference"}:
        p.append(f'<rect x="{x-38}" y="{y-25}" width="76" height="50" rx="7" fill="{PANEL}" stroke="{accent}" stroke-width="2"/>')
        if kind == "video":
            for dx in (-30, -15, 0, 15, 30):
                p.append(f'<rect x="{x+dx-3}" y="{y-22}" width="6" height="5" rx="1" fill="{LINE}"/>')
                p.append(f'<rect x="{x+dx-3}" y="{y+17}" width="6" height="5" rx="1" fill="{LINE}"/>')
            p.append(f'<path d="M {x-8} {y-10} L {x+14} {y} L {x-8} {y+10} Z" fill="{accent}"/>')
        else:
            p.append(f'<circle cx="{x-18}" cy="{y-9}" r="6" fill="{accent}"/>')
            p.append(f'<path d="M {x-30} {y+16} L {x-8} {y-5} L {x+5} {y+8} L {x+20} {y-7} L {x+31} {y+16} Z" fill="{PALE}" opacity=".65"/>')
            if kind == "reference":
                p.append(f'<path d="M {x+24} {y-28} l 9 9 -9 9 -9-9z" fill="{accent}"/>')
    elif kind in {"waveform", "audio", "music"}:
        for j in range(11):
            xx = x - 34 + j * 7
            hh = 9 + ((j * 13 + variant * 7) % 27)
            p.append(f'<rect x="{xx}" y="{y-hh/2:g}" width="4" height="{hh}" rx="2" fill="{accent if j % 3 == 0 else PALE}" opacity=".85"/>')
        if kind == "music":
            p.append(txt(x + 29, y - 17, "♪", 20, accent, weight=700))
    elif kind in {"check", "checker", "submission", "score", "medal"}:
        p.append(f'<circle cx="{x}" cy="{y}" r="27" fill="{accent}" opacity=".16" stroke="{accent}" stroke-width="2"/>')
        if kind == "medal":
            p.append(f'<path d="M {x-12} {y-31} L {x-3} {y-12} L {x+4} {y-31} M {x+6} {y-31} L {x+11} {y-12}" stroke="{accent}" stroke-width="5"/>')
            p.append(txt(x, y + 8, "1", 20, INK, weight=700))
        else:
            p.append(f'<path d="M {x-13} {y} L {x-3} {y+10} L {x+16} {y-13}" fill="none" stroke="{accent}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
    elif kind in {"search", "critic", "target"}:
        p.append(f'<circle cx="{x-5}" cy="{y-5}" r="22" fill="{PANEL}" stroke="{accent}" stroke-width="3"/>')
        p.append(f'<line x1="{x+10}" y1="{y+11}" x2="{x+29}" y2="{y+28}" stroke="{accent}" stroke-width="6" stroke-linecap="round"/>')
        if kind == "critic":
            p.append(txt(x - 5, y + 3, "!", 20, "#ff806e", weight=700))
        elif kind == "target":
            p.append(f'<circle cx="{x-5}" cy="{y-5}" r="9" fill="none" stroke="#ff806e" stroke-width="2"/><circle cx="{x-5}" cy="{y-5}" r="3" fill="#ff806e"/>')
    elif kind in {"shield", "sandbox"}:
        p.append(f'<path d="M {x} {y-31} L {x+29} {y-19} V {y+2} C {x+29} {y+22} {x+11} {y+31} {x} {y+37} C {x-11} {y+31} {x-29} {y+22} {x-29} {y+2} V {y-19} Z" fill="{accent}" opacity=".18" stroke="{accent}" stroke-width="2"/>')
        p.append(f'<path d="M {x-11} {y} L {x-3} {y+8} L {x+14} {y-11}" fill="none" stroke="{accent}" stroke-width="4"/>')
    elif kind in {"model", "agent", "persona"}:
        p.append(f'<circle cx="{x}" cy="{y-11}" r="18" fill="{accent}" opacity=".22" stroke="{accent}" stroke-width="2"/>')
        p.append(f'<path d="M {x-29} {y+28} C {x-25} {y+4} {x+25} {y+4} {x+29} {y+28}" fill="{PANEL}" stroke="{accent}" stroke-width="2"/>')
        if kind == "model":
            for dx, dy in ((-8,-15),(8,-15),(0,-3)):
                p.append(f'<circle cx="{x+dx}" cy="{y+dy}" r="3" fill="{PALE}"/>')
    elif kind in {"chat", "qa"}:
        p.append(f'<rect x="{x-39}" y="{y-24}" width="57" height="30" rx="11" fill="{PANEL}" stroke="{PALE}" stroke-width="1.8"/>')
        p.append(f'<rect x="{x-13}" y="{y+3}" width="54" height="28" rx="11" fill="{accent}" opacity=".72"/>')
        p.append(f'<line x1="{x-27}" y1="{y-10}" x2="{x+4}" y2="{y-10}" stroke="{PALE}" stroke-width="3"/>')
        p.append(f'<line x1="{x}" y1="{y+16}" x2="{x+27}" y2="{y+16}" stroke="{INK}" stroke-width="3" opacity=".8"/>')
    elif kind in {"chart", "diagnostic", "coherence", "path", "formula"}:
        p.append(f'<line x1="{x-33}" y1="{y+24}" x2="{x-33}" y2="{y-24}" stroke="{LINE}" stroke-width="2"/><line x1="{x-33}" y1="{y+24}" x2="{x+35}" y2="{y+24}" stroke="{LINE}" stroke-width="2"/>')
        pts = [(x-28, y+14), (x-12, y+4), (x+2, y+10), (x+18, y-12), (x+33, y-20)]
        p.append('<path d="M ' + ' L '.join(f'{a} {b}' for a,b in pts) + f'" fill="none" stroke="{accent}" stroke-width="3"/>')
        for a,b in pts:
            p.append(f'<circle cx="{a}" cy="{b}" r="3" fill="{accent}"/>')
    elif kind in {"database", "containers", "server", "layers"}:
        if kind == "database":
            p.append(f'<path d="M {x-31} {y-18} C {x-31} {y-30} {x+31} {y-30} {x+31} {y-18} V {y+20} C {x+31} {y+32} {x-31} {y+32} {x-31} {y+20} Z" fill="{PANEL}" stroke="{accent}" stroke-width="2"/>')
            p.append(f'<ellipse cx="{x}" cy="{y-18}" rx="31" ry="10" fill="{PANEL}" stroke="{accent}" stroke-width="2"/>')
        else:
            for j in range(3):
                yy = y - 24 + j * 21
                p.append(f'<rect x="{x-34+j*4}" y="{yy}" width="{68-j*8}" height="15" rx="5" fill="{PANEL}" stroke="{accent if j == variant%3 else LINE}" stroke-width="1.8"/>')
    elif kind in {"api", "network", "orchestrate", "tools"}:
        p.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{accent}"/>')
        for a,b in ((-30,-20),(30,-20),(-30,22),(30,22)):
            p.append(f'<line x1="{x}" y1="{y}" x2="{x+a}" y2="{y+b}" stroke="{LINE}" stroke-width="2"/>')
            p.append(f'<circle cx="{x+a}" cy="{y+b}" r="7" fill="{PANEL}" stroke="{PALE}"/>')
    elif kind in {"map", "calendar", "ticket", "hotel", "clock"}:
        if kind == "map":
            p.append(f'<path d="M {x-35} {y+19} C {x-20} {y-22} {x+1} {y+28} {x+34} {y-17}" fill="none" stroke="{accent}" stroke-width="3" stroke-dasharray="5 5"/>')
            p.append(f'<circle cx="{x-35}" cy="{y+19}" r="6" fill="{accent}"/><path d="M {x+34} {y-28} C {x+18} {y-28} {x+20} {y-7} {x+34} {y+4} C {x+48} {y-7} {x+50} {y-28} {x+34} {y-28} Z" fill="{accent}"/>')
        elif kind == "calendar":
            p.append(box(x,y,70,58,accent,PANEL,7)); p.append(f'<line x1="{x-35}" y1="{y-10}" x2="{x+35}" y2="{y-10}" stroke="{accent}" stroke-width="3"/>')
            for ix in range(3):
                for iy in range(2): p.append(f'<circle cx="{x-20+ix*20}" cy="{y+2+iy*13}" r="3" fill="{PALE}"/>')
        elif kind == "clock":
            p.append(f'<circle cx="{x}" cy="{y}" r="29" fill="{PANEL}" stroke="{accent}" stroke-width="2"/><path d="M {x} {y} V {y-17} M {x} {y} L {x+14} {y+8}" stroke="{PALE}" stroke-width="3" stroke-linecap="round"/>')
        elif kind == "hotel":
            p.append(f'<path d="M {x-31} {y+24} V {y-18} H {x+31} V {y+24} M {x-38} {y+24} H {x+38}" fill="none" stroke="{accent}" stroke-width="3"/>')
            for dx in (-17,0,17): p.append(f'<rect x="{x+dx-5}" y="{y-8}" width="10" height="12" fill="{PALE}" opacity=".75"/>')
        else:
            p.append(f'<path d="M {x-36} {y-20} H {x+36} V {y-7} C {x+24} {y-7} {x+24} {y+7} {x+36} {y+7} V {y+20} H {x-36} V {y+7} C {x-24} {y+7} {x-24} {y-7} {x-36} {y-7} Z" fill="{PANEL}" stroke="{accent}" stroke-width="2"/>')
    elif kind in {"rules", "prior", "style", "language", "culture", "text", "book", "theorem", "algebra", "number"}:
        p.append(box(x, y, 74, 58, accent, PANEL, 9))
        symbols = {"rules":"⊕  △  ≡", "prior":"P(·)", "style":"Aa", "language":"EN 中", "culture":"文 化", "text":"Tt", "book":"≡", "theorem":"⊢ P", "algebra":"x²", "number":"ℕ"}
        p.append(txt(x, y+7, symbols.get(kind,"·"), 18, accent, weight=700))
    elif kind in {"geometry", "meaning", "sync", "rubric", "scale", "funnel", "attack", "break", "missing", "features", "environment", "stage", "cursor", "trace", "taxonomy", "issue", "benchmark", "samplewall", "game", "matrix", "formula", "compare", "loop", "token"}:
        # Compact bespoke glyphs for remaining semantic concepts.
        p.append(box(x, y, 74, 58, accent, PANEL, 12))
        glyph = {"geometry":"△ ○", "meaning":"◎", "sync":"↔", "rubric":"1—5", "scale":"A ⚖ B", "funnel":"▽", "attack":"! →", "break":"×", "missing":"{ … }", "features":"ƒ(x)", "environment":"↻", "stage":"V / C", "cursor":"↖", "trace":"1·2·3", "issue":"#42", "benchmark":"SET", "samplewall":"••••", "game":"▦", "matrix":"2×2", "compare":"A≠B", "loop":"↻", "token":"tok"}.get(kind, "•")
        p.append(txt(x, y+7, glyph, 18, accent, weight=700))
    else:
        p.append(box(x, y, 74, 58, accent, PANEL, 12))
        p.append(txt(x, y+6, short(kind, 8), 13, accent, weight=700))

    if label:
        p.append(txt(x, y + 48, short(label, 13), 10, MUTED, weight=600))
    return "\n".join(p)


def hero_objects(objects):
    """Keep the semantic endpoints while avoiding unreadable four/five-icon scenes."""
    if len(objects) <= 3:
        return objects
    return (objects[0], objects[len(objects) // 2], objects[-1])


def scene_icon(kind, x, y, accent="url(#accent)", scale=1.25, variant=0):
    """Scale one semantic glyph around its own center for thumbnail-first art."""
    raw = icon(kind, x, y, "", accent, variant)
    return (f'<g transform="translate({x:g} {y:g}) scale({scale:g}) '
            f'translate({-x:g} {-y:g})">{raw}</g>')


def custom_scene(slug, accent_a, accent_b):
    """Distinct hero silhouettes for the nineteen papers visible on the site."""
    A = "url(#accent)"
    S = "#cbd5e1"
    D = "#334155"
    green = "#10b981"
    red = "#ef4444"

    if slug == "autokaggle":
        parts = [scene_icon("table", 76, 180, A, 1.2)]
        parts.append(f'<path d="M 128 180 H 166 M 310 180 H 352" stroke="{D}" stroke-width="5" stroke-linecap="round" marker-end="url(#arrow)"/>')
        parts.append(f'<circle cx="238" cy="180" r="68" fill="{accent_a}" opacity=".07" stroke="{A}" stroke-width="5"/>')
        for i in range(6):
            angle = math.radians(i * 60 - 90)
            x, y = 238 + math.cos(angle) * 49, 180 + math.sin(angle) * 49
            parts.append(f'<line x1="238" y1="180" x2="{x:g}" y2="{y:g}" stroke="{S}" stroke-width="4"/>')
            parts.append(f'<circle cx="{x:g}" cy="{y:g}" r="10" fill="#fff" stroke="{A}" stroke-width="4"/>')
        parts.append(txt(238, 189, "ƒ", 34, A, weight=700))
        parts.append(scene_icon("submission", 399, 180, green, 1.2))
        return "\n".join(parts)

    if slug == "automv":
        bars = []
        for i, h in enumerate((20, 38, 64, 34, 78, 48, 26, 58, 32)):
            x = 52 + i * 16
            bars.append(f'<rect x="{x}" y="{180-h/2:g}" width="9" height="{h}" rx="4.5" fill="{A}"/>')
        film = [f'<path d="M 198 123 C 238 143 246 217 292 237 H 426 V 123 H 292 C 248 143 240 103 198 123 Z" fill="{accent_b}" opacity=".08" stroke="{A}" stroke-width="5"/>']
        for x in (270, 326, 382):
            film.append(f'<rect x="{x}" y="148" width="43" height="64" rx="7" fill="#fff" stroke="{D}" stroke-width="4"/>')
            film.append(f'<path d="M {x+9} 197 L {x+21} 180 L {x+32} 197 Z" fill="{A}" opacity=".75"/>')
        film.append(f'<path d="M 208 180 C 232 156 242 205 266 180" fill="none" stroke="{A}" stroke-width="6"/>')
        return "\n".join(bars + film)

    if slug == "code_simpleqa":
        return f'''
<path d="M 60 92 Q 150 72 232 116 V 274 Q 150 236 60 258 Z" fill="#fff" stroke="{A}" stroke-width="5"/>
<path d="M 420 92 Q 330 72 248 116 V 274 Q 330 236 420 258 Z" fill="#fff" stroke="{A}" stroke-width="5"/>
<path d="M 240 115 V 275" stroke="{D}" stroke-width="6"/>
<path d="M 86 137 H 184 M 86 162 H 202 M 86 187 H 164 M 86 212 H 195" stroke="{D}" stroke-width="6" stroke-linecap="round"/>
{txt(145, 238, "{ API }", 25, accent_a, weight=700)}
<rect x="282" y="128" width="103" height="61" rx="22" fill="{accent_b}" opacity=".11" stroke="{A}" stroke-width="4"/>
{txt(334, 167, "?", 31, accent_b, weight=700)}
{txt(300, 231, "EN", 24, D, weight=700)}
<path d="M 327 222 H 346" stroke="{S}" stroke-width="4"/>
{txt(372, 231, "中", 27, D, weight=700)}
<circle cx="384" cy="101" r="25" fill="{green}"/><path d="M 372 101 L 381 111 L 398 91" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"/>
'''

    if slug == "codeeditorbench":
        left_lines = "".join(f'<path d="M 76 {126+i*27} H {180-(i%2)*24}" stroke="{D}" stroke-width="7" stroke-linecap="round"/>' for i in range(5))
        right_lines = "".join(f'<path d="M 292 {126+i*27} H {404-(i%2)*32}" stroke="{green if i in (1,3) else D}" stroke-width="7" stroke-linecap="round"/>' for i in range(5))
        return f'''
<rect x="48" y="70" width="384" height="220" rx="22" fill="#fff" stroke="{D}" stroke-width="5"/>
<path d="M 48 108 H 432 M 240 108 V 290" stroke="{S}" stroke-width="4"/>
<circle cx="73" cy="89" r="6" fill="{red}"/><circle cx="93" cy="89" r="6" fill="#f59e0b"/><circle cx="113" cy="89" r="6" fill="{green}"/>
{left_lines}{right_lines}
<rect x="222" y="126" width="36" height="36" rx="10" fill="{red}"/>{txt(240, 153, "−", 26, "#fff", weight=700)}
<rect x="222" y="178" width="36" height="36" rx="10" fill="{green}"/>{txt(240, 205, "+", 26, "#fff", weight=700)}
<circle cx="397" cy="84" r="27" fill="{green}"/><path d="M 384 84 L 394 95 L 412 73" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round"/>
'''

    if slug == "criticlean":
        return f'''
<path d="M 240 100 V 265 M 160 265 H 320" stroke="{D}" stroke-width="8" stroke-linecap="round"/>
<path d="M 100 132 H 380" stroke="{A}" stroke-width="8" stroke-linecap="round"/>
<path d="M 132 132 L 102 194 H 162 Z M 348 132 L 318 194 H 378 Z" fill="{accent_a}" opacity=".09" stroke="{D}" stroke-width="4"/>
<rect x="62" y="197" width="100" height="55" rx="12" fill="#fff" stroke="{A}" stroke-width="4"/>
{txt(112, 231, "x² + y²", 20, D, weight=700)}
<rect x="318" y="197" width="100" height="55" rx="12" fill="#fff" stroke="{A}" stroke-width="4"/>
{txt(368, 231, "⊢ P", 24, D, weight=700)}
<circle cx="240" cy="130" r="30" fill="{accent_b}"/>{txt(240, 140, "=", 27, "#fff", weight=700)}
<circle cx="240" cy="264" r="24" fill="{green}"/><path d="M 229 264 L 238 273 L 253 254" fill="none" stroke="#fff" stroke-width="5"/>
'''

    if slug == "edgebench":
        return f'''
<path d="M 112 142 L 205 91 L 298 142 L 205 194 Z M 112 142 V 243 L 205 296 V 194 M 298 142 V 243 L 205 296" fill="{accent_a}" fill-opacity=".06" stroke="{D}" stroke-width="5" stroke-linejoin="round"/>
<path d="M 88 244 C 50 163 126 74 234 78 C 358 83 408 187 350 260 C 313 305 246 307 220 271" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round" marker-end="url(#arrow)"/>
<circle cx="92" cy="240" r="11" fill="{accent_a}"/><circle cx="130" cy="112" r="11" fill="{accent_b}"/><circle cx="260" cy="82" r="11" fill="{accent_a}"/><circle cx="386" cy="180" r="11" fill="{accent_b}"/>
<path d="M 158 226 L 194 203 L 225 218 L 261 165" fill="none" stroke="{green}" stroke-width="7" stroke-linecap="round"/>
<circle cx="261" cy="165" r="9" fill="{green}"/>
'''

    if slug == "formalmath":
        return f'''
<rect x="176" y="255" width="128" height="52" rx="15" fill="#fff" stroke="{D}" stroke-width="5"/>{txt(240, 289, "⊢ theorem", 21, D, weight=700)}
<path d="M 240 255 V 220 M 240 220 L 118 172 M 240 220 L 240 162 M 240 220 L 362 172" fill="none" stroke="{A}" stroke-width="7" stroke-linecap="round"/>
<circle cx="118" cy="172" r="22" fill="#fff" stroke="{A}" stroke-width="5"/>{txt(118, 180, "1", 20, accent_a, weight=700)}
<circle cx="240" cy="162" r="22" fill="#fff" stroke="{A}" stroke-width="5"/>{txt(240, 170, "2", 20, accent_b, weight=700)}
<circle cx="362" cy="172" r="22" fill="#fff" stroke="{A}" stroke-width="5"/>{txt(362, 180, "3", 20, accent_a, weight=700)}
<path d="M 118 150 L 172 104 M 240 140 V 86 M 362 150 L 308 104" stroke="{S}" stroke-width="5"/>
<circle cx="240" cy="72" r="42" fill="{green}"/><path d="M 218 72 L 235 89 L 265 53" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"/>
'''

    if slug == "mammoth2":
        return f'''
<rect x="48" y="63" width="118" height="72" rx="13" fill="#fff" stroke="{D}" stroke-width="4"/><path d="M 48 88 H 166 M 67 106 H 143" stroke="{S}" stroke-width="5"/>
<rect x="83" y="147" width="118" height="72" rx="13" fill="#fff" stroke="{D}" stroke-width="4"/><path d="M 83 172 H 201 M 102 190 H 178" stroke="{S}" stroke-width="5"/>
<path d="M 177 67 H 324 L 279 181 V 218 L 222 249 V 181 Z" fill="{accent_a}" fill-opacity=".09" stroke="{A}" stroke-width="6" stroke-linejoin="round"/>
<path d="M 240 98 V 195" stroke="{A}" stroke-width="7" marker-end="url(#arrow)"/>
<rect x="310" y="196" width="120" height="72" rx="14" fill="#fff" stroke="{A}" stroke-width="5"/><path d="M 329 220 H 408 M 329 244 H 392" stroke="{D}" stroke-width="6" stroke-linecap="round"/>
<rect x="292" y="222" width="120" height="72" rx="14" fill="#fff" stroke="{A}" stroke-width="5"/><path d="M 311 246 H 390 M 311 270 H 374" stroke="{D}" stroke-width="6" stroke-linecap="round"/>
{txt(354, 121, "10M", 42, accent_b, weight=700)}
'''

    if slug == "mm_browsecomp":
        return f'''
<rect x="46" y="66" width="326" height="226" rx="20" fill="#fff" stroke="{D}" stroke-width="5"/>
<path d="M 46 105 H 372" stroke="{S}" stroke-width="4"/><circle cx="72" cy="86" r="6" fill="{accent_a}"/><circle cx="92" cy="86" r="6" fill="{accent_b}"/>
<rect x="77" y="130" width="88" height="66" rx="9" fill="{accent_a}" opacity=".10" stroke="{D}" stroke-width="4"/><path d="M 88 182 L 112 151 L 133 173 L 151 150" fill="none" stroke="{A}" stroke-width="5"/>
<rect x="187" y="130" width="88" height="66" rx="9" fill="#fff" stroke="{D}" stroke-width="4"/><path d="M 218 146 L 250 163 L 218 181 Z" fill="{A}"/>
<path d="M 86 230 H 287 M 86 254 H 248" stroke="{S}" stroke-width="7" stroke-linecap="round"/>
<circle cx="258" cy="177" r="91" fill="#fff" fill-opacity=".78" stroke="{A}" stroke-width="10"/>
<path d="M 324 243 L 405 307" stroke="{A}" stroke-width="18" stroke-linecap="round"/>
<circle cx="401" cy="80" r="35" fill="{green}"/><path d="M 385 80 L 397 93 L 420 66" fill="none" stroke="#fff" stroke-width="7"/>
'''

    if slug == "nl2repo_bench":
        return f'''
<path d="M 48 72 H 164 L 194 102 V 278 H 48 Z" fill="#fff" stroke="{A}" stroke-width="5"/><path d="M 164 72 V 102 H 194" fill="none" stroke="{A}" stroke-width="5"/>
<path d="M 72 128 H 165 M 72 156 H 152 M 72 184 H 170 M 72 212 H 140" stroke="{D}" stroke-width="6" stroke-linecap="round"/>
<path d="M 194 174 H 250 V 112 M 250 174 V 174 M 250 174 V 238" fill="none" stroke="{A}" stroke-width="7"/>
<rect x="269" y="84" width="124" height="56" rx="13" fill="#fff" stroke="{D}" stroke-width="5"/>{txt(331, 120, "src/", 24, D, weight=700)}
<rect x="269" y="146" width="124" height="56" rx="13" fill="#fff" stroke="{D}" stroke-width="5"/>{txt(331, 182, "config/", 22, D, weight=700)}
<rect x="269" y="210" width="124" height="56" rx="13" fill="#fff" stroke="{D}" stroke-width="5"/>{txt(331, 246, "tests/", 22, D, weight=700)}
<rect x="376" y="226" width="50" height="44" rx="10" fill="{accent_b}"/><path d="M 390 226 V 214 C 390 196 414 196 414 214 V 226" fill="none" stroke="{accent_b}" stroke-width="7"/>
'''

    if slug == "omni_math":
        return f'''
<path d="M 56 284 L 238 62 L 424 284 Z" fill="{accent_a}" fill-opacity=".06" stroke="{A}" stroke-width="6" stroke-linejoin="round"/>
<path d="M 91 243 H 389 M 125 202 H 355 M 159 161 H 321 M 195 118 H 285" stroke="{S}" stroke-width="4"/>
<path d="M 112 284 C 156 236 164 207 208 178 C 245 154 268 124 309 83" fill="none" stroke="{A}" stroke-width="8" stroke-linecap="round"/>
{txt(130, 263, "x²", 28, accent_a, weight=700)}{txt(240, 222, "△", 34, accent_b, weight=700)}{txt(335, 263, "ℕ", 31, accent_a, weight=700)}
<path d="M 239 65 V 27 M 239 28 H 302 L 280 49 L 302 68 H 239" fill="{accent_b}" stroke="{accent_b}" stroke-width="3"/>
<circle cx="309" cy="83" r="11" fill="{green}"/>
'''

    if slug == "opencodeinterpreter":
        return f'''
<rect x="50" y="62" width="380" height="236" rx="22" fill="#fff" stroke="{D}" stroke-width="5"/>
<path d="M 50 104 H 430" stroke="{S}" stroke-width="4"/><circle cx="76" cy="83" r="6" fill="{red}"/><circle cx="97" cy="83" r="6" fill="#f59e0b"/><circle cx="118" cy="83" r="6" fill="{green}"/>
<path d="M 82 137 H 218 M 82 167 H 184" stroke="{D}" stroke-width="7" stroke-linecap="round"/>
<path d="M 82 221 H 194" stroke="{red}" stroke-width="7" stroke-linecap="round"/><path d="M 82 253 H 230" stroke="{green}" stroke-width="7" stroke-linecap="round"/>
<path d="M 290 145 C 384 144 397 249 320 276 C 248 302 216 230 253 198" fill="none" stroke="{A}" stroke-width="11" stroke-linecap="round" marker-end="url(#arrow)"/>
{txt(337, 202, "$", 46, accent_b, weight=700)}
<circle cx="391" cy="251" r="28" fill="{green}"/><path d="M 378 251 L 388 262 L 406 239" fill="none" stroke="#fff" stroke-width="6"/>
'''

    if slug == "opencoder":
        threads = []
        colors = (accent_a, accent_b, "#06b6d4", "#22c55e", "#f59e0b")
        for i, color in enumerate(colors):
            y = 102 + i * 38
            threads.append(f'<path d="M 45 {y} C 118 {y} 126 {180+(i-2)*12} 188 {180+(i-2)*12}" fill="none" stroke="{color}" stroke-width="9" stroke-linecap="round"/>')
        return "\n".join(threads) + f'''
<rect x="184" y="88" width="112" height="184" rx="24" fill="#fff" stroke="{D}" stroke-width="6"/>
<path d="M 210 121 H 270 M 210 151 H 258 M 210 181 H 270 M 210 211 H 250 M 210 241 H 270" stroke="{A}" stroke-width="7" stroke-linecap="round"/>
<path d="M 296 132 H 335 M 296 180 H 353 M 296 228 H 335" stroke="{A}" stroke-width="7"/>
<rect x="337" y="101" width="94" height="70" rx="16" fill="#fff" stroke="{A}" stroke-width="5"/>
<rect x="351" y="145" width="80" height="70" rx="16" fill="#fff" stroke="{A}" stroke-width="5"/>
<rect x="337" y="190" width="94" height="70" rx="16" fill="#fff" stroke="{A}" stroke-width="5"/>
{txt(384, 144, "7B", 23, D, weight=700)}{txt(391, 188, "8B", 23, D, weight=700)}{txt(384, 233, "✓", 28, green, weight=700)}
'''

    if slug == "oprover":
        return f'''
<path d="M 52 98 H 148 L 168 118 V 202 H 52 Z M 78 128 H 142 M 78 154 H 132" fill="#fff" stroke="{A}" stroke-width="5"/>
<path d="M 82 76 H 178 L 198 96 V 180 H 82 Z M 108 106 H 172 M 108 132 H 162" fill="#fff" stroke="{A}" stroke-width="5"/>
<rect x="196" y="112" width="118" height="136" rx="24" fill="#fff" stroke="{D}" stroke-width="6"/>{txt(255, 173, "LEAN", 25, D, weight=700)}{txt(255, 211, "⊢", 34, accent_a, weight=700)}
<path d="M 226 275 C 304 318 392 260 374 177 C 365 135 337 111 309 99" fill="none" stroke="{A}" stroke-width="10" marker-end="url(#arrow)"/>
<path d="M 315 181 H 370" stroke="{A}" stroke-width="8" marker-end="url(#arrow)"/>
<path d="M 372 129 H 430 V 238 H 344 V 157 Z" fill="#fff" stroke="{green}" stroke-width="6"/>
<path d="M 360 190 L 376 207 L 407 169" fill="none" stroke="{green}" stroke-width="8" stroke-linecap="round"/>
'''

    if slug == "ouro":
        parts = []
        for i in range(7):
            angle = math.radians(i * 48 - 122)
            x, y = 235 + math.cos(angle) * 105, 180 + math.sin(angle) * 105
            parts.append(f'<rect x="{x-27:g}" y="{y-15:g}" width="54" height="30" rx="10" fill="#fff" stroke="{A}" stroke-width="5"/>')
        parts.append(f'<path d="M 112 243 C 61 163 125 65 231 62 C 347 58 405 160 361 242" fill="none" stroke="{A}" stroke-width="10" stroke-linecap="round" marker-end="url(#arrow)"/>')
        parts.append(f'<circle cx="235" cy="180" r="44" fill="#eef2ff" stroke="{D}" stroke-width="5"/>')
        parts.append(txt(235, 191, "tok", 30, D, weight=700))
        parts.append(f'<path d="M 361 242 H 430" stroke="{green}" stroke-width="10" stroke-linecap="round" marker-end="url(#arrow)"/>')
        return "\n".join(parts)

    if slug == "supergpqa":
        parts = [f'<circle cx="240" cy="180" r="44" fill="#fff" stroke="{D}" stroke-width="6"/>', txt(240, 194, "?", 40, accent_a, weight=700)]
        for radius, count, size in ((88, 10, 10), (132, 18, 7)):
            parts.append(f'<circle cx="240" cy="180" r="{radius}" fill="none" stroke="{S}" stroke-width="4"/>')
            for i in range(count):
                angle = math.radians(i * 360 / count - 90)
                x, y = 240 + math.cos(angle) * radius, 180 + math.sin(angle) * radius
                color = A if i % 4 == 0 else S
                parts.append(f'<circle cx="{x:g}" cy="{y:g}" r="{size}" fill="#fff" stroke="{color}" stroke-width="4"/>')
        parts.append(f'<path d="M 372 180 C 328 151 302 164 276 180 H 240" fill="none" stroke="{A}" stroke-width="8" marker-end="url(#arrow)"/>')
        return "\n".join(parts)

    if slug == "workflow_gym":
        windows = [(78, 118), (165, 198), (268, 111), (357, 205)]
        parts = [f'<rect x="42" y="51" width="396" height="258" rx="23" fill="#fff" stroke="{D}" stroke-width="5"/>', f'<path d="M 42 91 H 438" stroke="{S}" stroke-width="4"/>']
        path = "M 84 145 C 128 145 129 225 174 225 S 224 138 277 138 S 320 232 366 232"
        parts.append(f'<path d="{path}" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round" marker-end="url(#arrow)"/>')
        for i, (x, y) in enumerate(windows):
            parts.append(f'<rect x="{x-33}" y="{y-26}" width="66" height="52" rx="12" fill="#fff" stroke="{A}" stroke-width="5"/>')
            if i < 3:
                parts.append(f'<path d="M {x-19} {y-7} H {x+19} M {x-19} {y+8} H {x+8}" stroke="{D}" stroke-width="5" stroke-linecap="round"/>')
            else:
                parts.append(f'<path d="M {x-14} {y} L {x-3} {y+12} L {x+18} {y-14}" fill="none" stroke="{green}" stroke-width="7"/>')
        for i in range(11):
            parts.append(f'<circle cx="{91+i*27}" cy="282" r="4" fill="{accent_a if i < 8 else green}"/>')
        return "\n".join(parts)

    if slug == "worldtravel":
        return f'''
<path d="M 46 86 L 156 58 L 254 92 L 356 58 L 432 91 V 280 L 354 250 L 252 284 L 154 250 L 46 282 Z" fill="{accent_a}" fill-opacity=".05" stroke="{S}" stroke-width="5" stroke-linejoin="round"/>
<path d="M 156 58 V 250 M 254 92 V 284 M 356 58 V 250" stroke="{S}" stroke-width="4"/>
<path d="M 77 238 C 117 141 173 224 219 153 S 314 102 393 198" fill="none" stroke="{A}" stroke-width="9" stroke-linecap="round" stroke-dasharray="1 18"/>
<circle cx="77" cy="238" r="15" fill="{accent_a}"/><circle cx="219" cy="153" r="15" fill="{accent_b}"/><circle cx="393" cy="198" r="15" fill="{green}"/>
<path d="M 131 176 V 132 H 176 V 176 M 145 132 V 117 M 162 132 V 117" fill="#fff" stroke="{D}" stroke-width="5"/>
<path d="M 285 118 H 343 V 168 H 285 Z M 285 134 H 343" fill="#fff" stroke="{D}" stroke-width="5"/>
<path d="M 393 198 V 113 H 430 L 414 131 L 430 149 H 393" fill="{green}" stroke="{green}" stroke-width="4"/>
'''

    if slug == "yue":
        bars_top = "".join(f'<rect x="{205+i*15}" y="{152-(18+(i*13)%44)/2:g}" width="8" height="{18+(i*13)%44}" rx="4" fill="{accent_a}"/>' for i in range(13))
        bars_bottom = "".join(f'<rect x="{205+i*15}" y="{222-(20+(i*17)%50)/2:g}" width="8" height="{20+(i*17)%50}" rx="4" fill="{accent_b}"/>' for i in range(13))
        return f'''
<path d="M 48 74 H 171 L 195 98 V 286 H 48 Z" fill="#fff" stroke="{D}" stroke-width="5"/><path d="M 171 74 V 98 H 195" fill="none" stroke="{D}" stroke-width="5"/>
<path d="M 72 126 H 164 M 72 156 H 148 M 72 186 H 166 M 72 216 H 139 M 72 246 H 157" stroke="{D}" stroke-width="6" stroke-linecap="round"/>
{bars_top}{bars_bottom}
<path d="M 198 187 H 406" stroke="{S}" stroke-width="4"/>
<path d="M 232 116 V 272 M 286 116 V 272 M 340 116 V 272" stroke="{S}" stroke-width="3" stroke-dasharray="6 7"/>
<circle cx="411" cy="187" r="47" fill="{accent_b}" opacity=".10" stroke="{A}" stroke-width="6"/>{txt(411, 201, "♪", 46, accent_b, weight=700)}
'''

    return None


def positions(layout, n):
    if layout == "flow":
        xs = [240] if n == 1 else [112 + i * (256 / (n - 1)) for i in range(n)]
        return [(x, 198) for x in xs]
    if layout == "timeline":
        xs = [112 + i * (256 / max(n - 1, 1)) for i in range(n)]
        return [(x, 210 if i % 2 == 0 else 172) for i, x in enumerate(xs)]
    if layout == "merge":
        if n == 2:
            return [(128, 198), (352, 198)]
        return [(124, 166), (124, 226), (350, 198)]
    if layout == "orbit":
        if n == 2:
            return [(128, 198), (352, 198)]
        return [(116, 178), (116, 230), (350, 202)]
    if layout == "cycle":
        coords = [(240, 151), (350, 222), (130, 222)]
        return coords[:n]
    if layout == "matrix":
        coords = [(135, 178), (345, 178), (240, 232)]
        return coords[:n]
    if layout == "compare":
        if n == 3:
            return [(112, 198), (240, 198), (368, 198)]
        return [(128 + i * 224 / max(n-1,1), 198) for i in range(n)]
    if layout == "split":
        return [(128 + i * 224 / max(n-1,1), 198) for i in range(n)]
    raise ValueError(f"unknown layout: {layout}")


def connectors(layout, coords, accent):
    out = []
    def line(a, b, dash=""):
        x1,y1=a; x2,y2=b
        extra = ' stroke-dasharray="6 6"' if dash else ""
        bend = min(y1, y2) - 18
        out.append(f'<path d="M {x1} {y1} Q {(x1+x2)/2:g} {bend:g} {x2} {y2}" fill="none" stroke="{accent}" stroke-width="2.6" opacity=".46" marker-end="url(#arrow)"{extra}/>')
    if layout in {"flow", "split", "timeline", "compare"}:
        for a,b in zip(coords, coords[1:]): line(a,b, layout == "timeline")
    elif layout == "merge":
        for a in coords[:-1]: line(a, coords[-1])
    elif layout == "orbit":
        for a in coords[:-1]: line(a, coords[-1], "dash")
    elif layout == "cycle":
        for a,b in zip(coords, coords[1:] + coords[:1]): line(a,b)
    elif layout == "matrix":
        edges = ((coords[0], coords[2]), (coords[1], coords[2])) if len(coords) == 3 else (
            (coords[0], coords[1]), (coords[0], coords[2]),
            (coords[1], coords[3]), (coords[2], coords[3]))
        for a,b in edges:
            line(a,b,"dash")
    return "\n".join(out)


def render(slug, spec, record):
    accent_a, accent_b = DOMAIN_PALETTES.get(record["domain"], ("#2563eb", "#7c3aed"))
    accent = "url(#accent)"
    scene = custom_scene(slug, accent_a, accent_b)
    if scene is None:
        scene_objects = hero_objects(spec["objects"])
        coords = positions(spec["layout"], len(scene_objects))
        objects = "\n".join(scene_icon(kind, x, y, accent, 1.32, i)
                              for i, ((kind, _), (x, y)) in enumerate(zip(scene_objects, coords)))
        scene = f'{connectors(spec["layout"], coords, accent)}\n{objects}'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<!-- tokenwave:generated:v4 slug={slug} layout={spec["layout"]} -->
<title id="title">{escape(spec["name"])} benchmark illustration</title>
<desc id="desc">{escape(spec["desc"])}</desc>
<defs>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{accent_a}"/><stop offset="1" stop-color="{accent_b}"/></linearGradient>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="9" stdDeviation="12" flood-color="#1e293b" flood-opacity=".10"/></filter>
  <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="{accent_b}"/></marker>
</defs>
<rect width="480" height="360" rx="28" fill="{BG}"/>
<rect x="22" y="22" width="436" height="316" rx="28" fill="#ffffff" stroke="{LINE}" stroke-width="1.5" filter="url(#shadow)"/>
{scene}
</svg>
'''


def load_records():
    records = {}
    for path in sorted(DATA.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        records[data["slug"]] = data
    return records


def main():
    records = load_records()
    missing = sorted(set(records) - set(VISUAL_SPECS))
    unknown = sorted(set(VISUAL_SPECS) - set(records))
    if missing or unknown:
        raise SystemExit(f"visual coverage error — missing={missing}, unknown={unknown}")

    rendered = {slug: render(slug, VISUAL_SPECS[slug], records[slug])
                for slug in sorted(records)}

    if CHECK:
        stale = []
        for slug, svg in rendered.items():
            out = OUT / f"{slug.replace('_', '-')}.svg"
            if not out.exists() or out.read_text(encoding="utf-8") != svg:
                stale.append(out.name)
        if stale:
            raise SystemExit("stale benchmark artwork: " + ", ".join(stale))
        print(f"OK — {len(rendered)} explicit visual scenes are complete and fresh.")
        return

    OUT.mkdir(parents=True, exist_ok=True)
    written = 0
    for slug, svg in rendered.items():
        out = OUT / f"{slug.replace('_', '-')}.svg"
        if out.exists() and not FORCE:
            continue
        out.write_text(svg, encoding="utf-8")
        written += 1
        print(f"  {out.name:<30} {VISUAL_SPECS[slug]['layout']}")
    print(f"generated {written} of {len(rendered)} content-specific SVGs")


if __name__ == "__main__":
    main()
