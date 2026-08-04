#!/usr/bin/env python3
"""Generate content-specific benchmark artwork.

Each benchmark has an explicit visual scene.  Shared primitives keep the set
coherent, while the object mix and topology describe the actual task instead
of routing broad subcategories into generic charts.

Run:
    python3 tools/gen_images.py --force   # redraw every asset
    python3 tools/gen_images.py --check   # validate coverage and freshness
"""

import hashlib
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "benchmarks"
OUT = ROOT / "static" / "images" / "benchmarks"
FORCE = "--force" in sys.argv
CHECK = "--check" in sys.argv

W, H = 480, 360
BG = "#07111f"
INK = "#e8eef9"
MUTED = "#91a1b8"
LINE = "#31435d"
PANEL = "#101d30"
PALE = "#c7d3e5"
PALETTES = ["#54a6ff", "#8d7cff", "#25c2a0", "#ff8a66", "#e8bd57", "#e16fae"]


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

    p.append(txt(x, y + 48, short(label), 10.5, PALE, weight=600))
    return "\n".join(p)


def positions(layout, n):
    if layout == "flow":
        xs = [240] if n == 1 else [72 + i * (336 / (n - 1)) for i in range(n)]
        return [(x, 184) for x in xs]
    if layout == "timeline":
        xs = [70 + i * (340 / max(n - 1, 1)) for i in range(n)]
        return [(x, 174 + (-1 if i % 2 else 1) * 30) for i, x in enumerate(xs)]
    if layout == "merge":
        if n == 2:
            return [(118, 180), (362, 180)]
        inputs = n - 1
        ys = [112 + i * (146 / max(inputs - 1, 1)) for i in range(inputs)]
        return [(112, y) for y in ys] + [(362, 184)]
    if layout == "orbit":
        satellites = n - 1
        coords = [(92, 128), (92, 238), (240, 270), (388, 238), (388, 128)]
        return coords[:satellites] + [(272, 178)]
    if layout == "cycle":
        coords = [(240, 103), (366, 180), (240, 257), (114, 180), (240, 180)]
        return coords[:n]
    if layout == "matrix":
        coords = [(150, 135), (330, 135), (150, 235), (330, 235)]
        return coords[:n]
    if layout == "compare":
        if n == 3:
            return [(105, 180), (240, 180), (375, 180)]
        return [(105 + i * 270 / max(n-1,1), 180) for i in range(n)]
    if layout == "split":
        return [(92 + i * 296 / max(n-1,1), 180) for i in range(n)]
    raise ValueError(f"unknown layout: {layout}")


def connectors(layout, coords, accent):
    out = []
    def line(a, b, dash=""):
        x1,y1=a; x2,y2=b
        extra = ' stroke-dasharray="6 6"' if dash else ""
        out.append(f'<path d="M {x1} {y1} L {x2} {y2}" fill="none" stroke="{accent}" stroke-width="2" opacity=".55" marker-end="url(#arrow)"{extra}/>')
    if layout in {"flow", "split", "timeline", "compare"}:
        for a,b in zip(coords, coords[1:]): line(a,b, layout == "timeline")
    elif layout == "merge":
        for a in coords[:-1]: line(a, coords[-1])
    elif layout == "orbit":
        for a in coords[:-1]: line(a, coords[-1], "dash")
    elif layout == "cycle":
        for a,b in zip(coords, coords[1:] + coords[:1]): line(a,b)
    elif layout == "matrix":
        for a,b in ((coords[0],coords[1]),(coords[0],coords[2]),(coords[1],coords[3]),(coords[2],coords[3])):
            line(a,b,"dash")
    return "\n".join(out)


def render(slug, spec, domain):
    digest = hashlib.sha256(slug.encode()).digest()
    accent = PALETTES[digest[0] % len(PALETTES)]
    halo_x = 70 + digest[1] % 340
    halo_y = 80 + digest[2] % 200
    coords = positions(spec["layout"], len(spec["objects"]))
    objects = "\n".join(icon(kind, x, y, label, accent, i)
                            for i, ((kind, label), (x,y)) in enumerate(zip(spec["objects"], coords)))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<!-- tokenwave:generated:v2 slug={slug} layout={spec["layout"]} -->
<title id="title">{escape(spec["name"])} benchmark illustration</title>
<desc id="desc">{escape(spec["desc"])}</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0b1930"/><stop offset="1" stop-color="{BG}"/></linearGradient>
  <radialGradient id="halo"><stop stop-color="{accent}" stop-opacity=".22"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
  <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M 24 0 L 0 0 0 24" fill="none" stroke="#2b3b53" stroke-width=".7" opacity=".32"/></pattern>
  <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="{accent}"/></marker>
</defs>
<rect width="480" height="360" rx="18" fill="url(#bg)"/>
<rect width="480" height="360" rx="18" fill="url(#grid)"/>
<circle cx="{halo_x}" cy="{halo_y}" r="145" fill="url(#halo)"/>
<path d="M 28 77 H 452" stroke="{LINE}" stroke-width="1" opacity=".7"/>
{txt(28, 41, spec["name"], 15, INK, "start", 700)}
{txt(452, 41, domain.upper(), 9.5, accent, "end", 700)}
{connectors(spec["layout"], coords, accent)}
{objects}
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

    rendered = {slug: render(slug, VISUAL_SPECS[slug], records[slug]["domain"])
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
