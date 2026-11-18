"""Build native editable widescreen PowerPoint deck B_Stage4_Slides_EN.pptx (sharing Part C's OOXML master)."""
import argparse
import csv
import os
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "05_Project3_月面机器人装配"
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".cache/matplotlib"))

from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "图表"
TEMPLATE_PPTX = ROOT / "AC回传/C/C_第二阶段汇报.pptx"
STAGE3_DIR = PROJECT / "运行验证/B_第三阶段_2026-11-10"

EMU = 914400  # 1 inch in EMUs (16:9 widescreen = 13.3333 x 7.5000 in)


def emu(inches: float) -> int:
    return int(round(inches * EMU))


def make_run(text: str, size_pt: float = 12.0, bold: bool = False, color: str = "1E293B", font: str = "Calibri") -> str:
    b_attr = ' b="1"' if bold else ""
    sz = int(round(size_pt * 100))
    return (
        f'<a:r><a:rPr lang="en-US" sz="{sz}"{b_attr} dirty="0">'
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'<a:latin typeface="{font}"/><a:ea typeface="Microsoft YaHei"/>'
        f'</a:rPr><a:t>{escape(text)}</a:t></a:r>'
    )


def make_para(runs_xml: str, space_after_pt: float = 4.0, align: str = "l") -> str:
    spc = int(round(space_after_pt * 100))
    return (
        f'<a:p><a:pPr algn="{align}">'
        f'<a:lnSpc><a:spcPct val="115000"/></a:lnSpc>'
        f'<a:spcAft><a:spcPts val="{spc}"/></a:spcAft>'
        f'</a:pPr>{runs_xml}</a:p>'
    )


def make_shape(sp_id: int, name: str, x_in: float, y_in: float, w_in: float, h_in: float,
               paras_xml: str, fill_hex: str | None = "FFFFFF", border_hex: str | None = "CBD5E1",
               border_pt: float = 1.0, pad_in: float = 0.12, anchor: str = "t") -> str:
    fill_xml = f'<a:solidFill><a:srgbClr val="{fill_hex}"/></a:solidFill>' if fill_hex else "<a:noFill/>"
    if border_hex:
        ln_w = int(round(border_pt * 12700))
        ln_xml = f'<a:ln w="{ln_w}"><a:solidFill><a:srgbClr val="{border_hex}"/></a:solidFill></a:ln>'
    else:
        ln_xml = '<a:ln w="0"><a:noFill/></a:ln>'
    pad = emu(pad_in)
    return (
        f'<p:sp>'
        f'<p:nvSpPr><p:cNvPr id="{sp_id}" name="{escape(name)}"/>'
        f'<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>'
        f'<p:spPr><a:xfrm><a:off x="{emu(x_in)}" y="{emu(y_in)}"/><a:ext cx="{emu(w_in)}" cy="{emu(h_in)}"/></a:xfrm>'
        f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 3500"/></a:avLst></a:prstGeom>'
        f'{fill_xml}{ln_xml}</p:spPr>'
        f'<p:txBody><a:bodyPr wrap="square" lIns="{pad}" tIns="{pad}" rIns="{pad}" bIns="{pad}" anchor="{anchor}"/>'
        f'<a:lstStyle/>{paras_xml}</p:txBody>'
        f'</p:sp>'
    )


def make_picture(sp_id: int, rel_id: str, img_path: Path, box_x: float, box_y: float, box_w: float, box_h: float) -> str:
    with Image.open(img_path) as im:
        iw, ih = im.size
    aspect = iw / ih
    box_aspect = box_w / box_h
    if aspect >= box_aspect:
        w = box_w
        h = box_w / aspect
        x = box_x
        y = box_y + (box_h - h) / 2.0
    else:
        h = box_h
        w = box_h * aspect
        y = box_y
        x = box_x + (box_w - w) / 2.0
    return (
        f'<p:pic>'
        f'<p:nvPicPr><p:cNvPr id="{sp_id}" name="{escape(img_path.name)}"/>'
        f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
        f'<p:blipFill><a:blip r:embed="{rel_id}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
        f'<p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
        f'</p:pic>'
    )


SLIDES_SPEC = [
    {
        "tag": "Part B · Kinematics",
        "title": "All 96 target poses were reachable",
        "kpis": [
            ("96 / 96", "IK targets reached", "EFF6FF", "1D4ED8"),
            ("3.75°", "Smallest joint margin (J5)", "ECFDF5", "047857"),
            ("Rank 6", "Across the full trajectory", "FFF7ED", "C2410C"),
        ],
        "cards": [
            ("PiPER model", [
                "Six revolute joints from the URDF.",
                "TCP is 135.8 mm from the gripper base.",
            ]),
            ("Scaled Jacobian and IK", [
                "Scale translation with L = 0.3 m.",
                "Projected DLS uses a 2° limit buffer.",
            ]),
        ],
        "img": STAGE3_DIR / "compensation_on/limits_singularity.png",
        "img_caption": "Minimum joint margin and scaled singular value",
        "footer": "Minimum scaled singular value: 0.273 at targets, 0.0294 across the full run.",
    },
    {
        "tag": "Part B · Control",
        "title": "Correcting the held block’s XY offset",
        "kpis": [
            ("0.0476 mm", "Max TCP segment-end error", "EFF6FF", "1D4ED8"),
            ("0.0574 mm", "Servo tracking RMS", "ECFDF5", "047857"),
            ("0.826 mm", "Largest XY correction", "FFF7ED", "C2410C"),
        ],
        "cards": [
            ("Trajectory and feedback", [
                "Quintic transfers and 2 mm vertical IK checks.",
                "60 Hz DLS feedback and a 240 Hz joint servo.",
            ]),
            ("Post-lift correction", [
                "Measure block offset in the TCP frame.",
                "Shift transfer and lowering in XY, up to 2 mm.",
            ]),
        ],
        "img": STAGE3_DIR / "compensation_on/command_tracking.png",
        "img_caption": "Servo position and orientation tracking",
        "footer": "The model uses the simulated block pose after lifting to 82 mm.",
    },
    {
        "tag": "Part B · Placement accuracy",
        "title": "XY compensation improves horizontal placement",
        "kpis": [
            ("−75.5%", "Maximum horizontal error", "EFF6FF", "1D4ED8"),
            ("−72.0%", "Maximum 3D error", "ECFDF5", "047857"),
            ("+0.031°", "Maximum orientation error", "FFF7ED", "C2410C"),
        ],
        "cards": [
            ("Maximum XY error", ["0.927 → 0.227 mm"]),
            ("Orientation trade-off", ["0.156° → 0.187°"]),
        ],
        "img_caption": "Final horizontal error by block",
        "footer": "Same host and payload. Both runs completed all 16 blocks from step zero.",
    },
    {
        "tag": "Part B · Joint effort",
        "title": "Joint 1 peaked during transfer of block 11",
        "kpis": [
            ("15.196 N·m", "J1 peak · block 11 transfer", "EFF6FF", "1D4ED8"),
            ("13.133 N·m", "J2 peak · block 16 lift", "ECFDF5", "047857"),
            ("+2.27%", "J6 RMS increase", "FFF7ED", "C2410C"),
        ],
        "cards": [
            ("Motor feedback calibration", [
                "6 of 6 calibration cases passed.",
                "Torque equals 4 × raw motor feedback.",
            ]),
            ("Loaded model", [
                "Robot with gripper: 4.67 kg, including a 1.02 kg fixed base.",
                "Candidate block: 72.61 g.",
            ]),
        ],
        "img": STAGE3_DIR / "compensation_on/joint_motion_torque.png",
        "img_caption": "Joint positions, speeds and equivalent torques",
        "footer": "Sampled at 240 Hz. Each value represents the last internal substep.",
    },
    {
        "tag": "Part B · Q&A backup",
        "title": "Reproduction and model limits",
        "kpis": [
            ("11,300", "Single-block trace rows", "EFF6FF", "1D4ED8"),
            ("236", "Rendered physics frames", "ECFDF5", "047857"),
            ("6 / 6", "Fresh calibration passes", "FFF7ED", "C2410C"),
        ],
        "cards": [
            ("First placement reproduced", [
                "3D error: 0.039958 mm.",
                "XY command shift: 0.020105 mm.",
            ]),
            ("Simulation assumptions", [
                "Contact-gated grasp constraint and ideal pose sensing.",
                "Loaded link inertias and candidate block properties.",
            ]),
        ],
        "img": STAGE3_DIR / "comparison_common_torque.png",
        "img_caption": "Equivalent peak and RMS torque by joint",
        "footer": "The single-block result matched the first placement event of the adopted run.",
    },
]


def plot_horizontal_error(output: Path):
    with (OUT_DIR / "XY与竖向误差分解.csv").open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    items = [int(row["item"]) for row in rows]
    if items != list(range(1, 17)):
        raise ValueError("Expected paired horizontal results for blocks 1 to 16.")

    fig, ax = plt.subplots(figsize=(8.08, 3.98), dpi=240)
    for key, offset, color, label in (
        ("off", -0.20, "#94a3b8", "Compensation off"),
        ("on", 0.20, "#1d4ed8", "Compensation on"),
    ):
        ax.bar(
            [item + offset for item in items],
            [float(row[f"{key}_xy_norm_mm"]) for row in rows],
            width=0.37, color=color, label=label, zorder=3,
        )
    ax.set(xlim=(0.45, 16.55), ylim=(0, 1.02), xticks=items,
           yticks=[0, 0.25, 0.50, 0.75, 1.0])
    ax.set_xlabel("Block", fontsize=15, color="#334155")
    ax.set_ylabel("Horizontal error (mm)", fontsize=15, color="#334155")
    ax.tick_params(labelsize=13, length=0, pad=6, colors="#334155")
    ax.axvline(8.5, color="#cbd5e1", linestyle="--", linewidth=1)
    ax.grid(axis="y", color="#e2e8f0")
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.15), ncol=2,
              frameon=False, borderaxespad=0, fontsize=13)
    fig.subplots_adjust(left=0.13, right=0.985, top=0.86, bottom=0.20)
    fig.savefig(output, facecolor="white")
    plt.close(fig)


def speaker_notes() -> list[str]:
    script = (OUT_DIR / "B_Stage4_Slides_and_QA_EN.md").read_text(encoding="utf-8")
    notes = []
    for i in range(1, 5):
        section = script.split(f"### Slide B{i}", 1)[1].split("\n---", 1)[0]
        lines = (line.strip() for line in section.splitlines())
        notes.append(" ".join(line[2:].strip().strip('"') for line in lines if line.startswith("> ")))
    if len(notes) != 4 or not all(notes):
        raise ValueError("The four main slides require speaker notes from the English script.")
    return notes + [
        "Q&A backup. The independent review matched the first placement event. The full-run "
        "final pose of that block is sampled after all sixteen placements. The reported "
        "torque is the calibrated last-substep sample, and the loaded mass includes the fixed base."
    ]


def build_slide_xml(spec: dict, img_rel_id: str) -> str:
    shapes = []
    sp_id = 10

    # Header tag & title
    header_paras = (
        make_para(make_run(spec["tag"], size_pt=14, bold=True, color="2563EB"), space_after_pt=2.0)
        + make_para(make_run(spec["title"], size_pt=30, bold=True, color="0F172A"), space_after_pt=0.0)
    )
    shapes.append(make_shape(sp_id, "Header", 0.45, 0.16, 12.43, 0.91, header_paras, fill_hex=None, border_hex=None, pad_in=0.04))
    sp_id += 1

    # 3 KPI Pills across top
    kpi_w = 3.98
    kpi_gap = 0.245
    for idx, (val, lbl, bg_hex, fg_hex) in enumerate(spec["kpis"]):
        kx = 0.45 + idx * (kpi_w + kpi_gap)
        kp_paras = (
            make_para(make_run(val, size_pt=25, bold=True, color=fg_hex), space_after_pt=1.0, align="c")
            + make_para(make_run(lbl, size_pt=15, bold=True, color="334155"), space_after_pt=0.0, align="c")
        )
        shapes.append(make_shape(sp_id, f"KPI_{idx+1}", kx, 1.12, kpi_w, 0.97, kp_paras, fill_hex=bg_hex, border_hex=fg_hex, border_pt=0.8, pad_in=0.06, anchor="ctr"))
        sp_id += 1

    horizontal_slide = spec["tag"] == "Part B · Placement accuracy"
    figure_x = 4.64 if horizontal_slide else 6.45
    figure_width = 12.88 - figure_x
    card_width = figure_x - 0.60

    for i, (heading, lines) in enumerate(spec["cards"]):
        content = make_para(make_run(heading, size_pt=21, bold=True), space_after_pt=10)
        for line in lines:
            content += make_para(make_run(line, size_pt=24 if horizontal_slide else 18), space_after_pt=8)
        shapes.append(make_shape(sp_id, f"Card_{i + 1}", 0.45, 2.24 + 2.28 * i,
                                 card_width, 2.14, content, pad_in=0.24, anchor="ctr"))
        sp_id += 1

    shapes.append(make_shape(sp_id, "FigureCard", figure_x, 2.24, figure_width, 4.42,
                             make_para(make_run("")), pad_in=0.05))
    sp_id += 1
    shapes.append(make_picture(sp_id, img_rel_id, spec["img"],
                               figure_x + 0.12, 2.34, figure_width - 0.24, 3.70))
    sp_id += 1
    cap_para = make_para(make_run(spec["img_caption"], size_pt=15, color="475569"),
                         space_after_pt=0, align="c")
    shapes.append(make_shape(sp_id, "FigureCaption", figure_x + 0.08, 6.11,
                             figure_width - 0.16, 0.42, cap_para, fill_hex=None,
                             border_hex=None, pad_in=0.03, anchor="ctr"))
    sp_id += 1

    foot_para = make_para(make_run(spec["footer"], size_pt=15, bold=True, color="F8FAFC"),
                          space_after_pt=0)
    shapes.append(make_shape(sp_id, "Footer", 0.45, 6.87, 12.43, 0.48, foot_para,
                             fill_hex="1E293B", border_hex=None, pad_in=0.09, anchor="ctr"))

    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<p:cSld>'
        '<p:bg><p:bgPr><a:solidFill><a:srgbClr val="F8FAFC"/></a:solidFill></p:bgPr></p:bg>'
        '<p:spTree>'
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        '<p:grpSpPr><a:xfrm/></p:grpSpPr>'
        + "".join(shapes)
        + '</p:spTree></p:cSld>'
        '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>'
        '</p:sld>'
    )


def build_notes_xml(notes_text: str, slide_num: int) -> str:
    paras = "".join(
        f'<a:p><a:r><a:rPr lang="en-US" sz="1100"/><a:t>{escape(line)}</a:t></a:r></a:p>'
        for line in notes_text.splitlines()
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<p:notes xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<p:cSld><p:spTree>'
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        '<p:grpSpPr><a:xfrm/></p:grpSpPr>'
        '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Slide Image Placeholder 1"/>'
        '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="sldImg" idx="0"/></p:nvPr></p:nvSpPr><p:spPr/></p:sp>'
        '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Notes Placeholder 2"/>'
        '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/>'
        f'<p:txBody><a:bodyPr/><a:lstStyle/>{paras}</p:txBody></p:sp>'
        '<p:sp><p:nvSpPr><p:cNvPr id="4" name="Slide Number Placeholder 3"/>'
        '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="sldNum" idx="5"/></p:nvPr></p:nvSpPr><p:spPr/>'
        f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:t>{slide_num}</a:t></a:r></a:p></p:txBody></p:sp>'
        '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>'
    )


def render_preview_sheet(deck: Path, output: Path, render_dir: Path):
    profile = (render_dir / "lo-profile").as_uri()
    subprocess.run(
        ["soffice", f"-env:UserInstallation={profile}", "--headless",
         "--convert-to", "pdf", "--outdir", str(render_dir), str(deck)],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["pdftoppm", "-r", "96", "-png", str(render_dir / (deck.stem + ".pdf")),
         str(render_dir / "page")],
        check=True, capture_output=True,
    )
    pages = sorted(render_dir.glob("page-*.png"))
    if len(pages) != len(SLIDES_SPEC):
        raise ValueError(f"LibreOffice rendered {len(pages)} pages, expected {len(SLIDES_SPEC)}.")
    with Image.open(pages[0]) as page:
        width, height = page.size
    gap = 18
    sheet = Image.new("RGB", (2 * width + 3 * gap, 3 * height + 4 * gap), "#e2e8f0")
    for i, path in enumerate(pages):
        with Image.open(path) as page:
            sheet.paste(page, (gap + (i % 2) * (width + gap), gap + (i // 2) * (height + gap)))
    sheet.save(output)


def build_deck(out_pptx: Path, slides: list[dict]):
    keep_prefixes = (
        "docProps/",
        "_rels/.rels",
        "ppt/theme/",
        "ppt/slideMasters/",
        "ppt/slideLayouts/",
        "ppt/notesMasters/",
        "ppt/presProps.xml",
        "ppt/tableStyles.xml",
    )

    with zipfile.ZipFile(TEMPLATE_PPTX, "r") as tpl, zipfile.ZipFile(out_pptx, "w", zipfile.ZIP_DEFLATED) as out:
        for item in tpl.infolist():
            if item.filename.startswith(keep_prefixes):
                data = tpl.read(item.filename)
                if item.filename == "docProps/core.xml":
                    txt = data.decode("utf8")
                    txt = txt.replace("C 第二阶段汇报", "HKU CIVL 7023 Project 3 - Part B Final Slides")
                    data = txt.encode("utf8")
                out.writestr(item.filename, data)

        # Presentation & Rels
        sld_ids_xml = ""
        pres_rels_extra = ""
        ct_overrides = [
            '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
            '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
            '<Override PartName="/ppt/slideMasters/theme/theme2.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
            '<Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"/>',
            '<Override PartName="/ppt/notesMasters/theme/theme3.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
            '<Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>',
            '<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>',
        ]
        for k in range(1, 7):
            ct_overrides.append(
                f'<Override PartName="/ppt/slideLayouts/slideLayout{k}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
            )

        for idx, spec in enumerate(slides, start=1):
            sld_rId = f"rIdSlide{idx}"
            img_rId = f"rIdImg{idx}"
            notes_rId = f"rIdNotes{idx}"
            media_name = f"b_slide_{idx}.png"
            out.write(spec["img"], f"ppt/media/{media_name}")

            slide_xml = build_slide_xml(spec, img_rId)
            ET.fromstring(slide_xml)  # strict XML well-formedness check
            out.writestr(f"ppt/slides/slide{idx}.xml", slide_xml.encode("utf8"))

            slide_rels = (
                '<?xml version="1.0" encoding="utf-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="/ppt/slideLayouts/slideLayout6.xml" Id="rIdLayout"/>'
                f'<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="/ppt/media/{media_name}" Id="{img_rId}"/>'
                f'<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="/ppt/notesSlides/notesSlide{idx}.xml" Id="{notes_rId}"/>'
                '</Relationships>'
            )
            ET.fromstring(slide_rels)
            out.writestr(f"ppt/slides/_rels/slide{idx}.xml.rels", slide_rels.encode("utf8"))

            notes_xml = build_notes_xml(spec["notes"], idx)
            ET.fromstring(notes_xml)
            out.writestr(f"ppt/notesSlides/notesSlide{idx}.xml", notes_xml.encode("utf8"))

            notes_rels = (
                '<?xml version="1.0" encoding="utf-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="/ppt/notesMasters/notesMaster1.xml" Id="rIdNotesMaster"/>'
                f'<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="/ppt/slides/slide{idx}.xml" Id="rIdParentSlide"/>'
                '</Relationships>'
            )
            ET.fromstring(notes_rels)
            out.writestr(f"ppt/notesSlides/_rels/notesSlide{idx}.xml.rels", notes_rels.encode("utf8"))

            sld_ids_xml += f'<p:sldId id="{255 + idx}" r:id="{sld_rId}"/>'
            pres_rels_extra += (
                f'<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="/ppt/slides/slide{idx}.xml" Id="{sld_rId}"/>'
            )
            ct_overrides.append(
                f'<Override PartName="/ppt/slides/slide{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            )
            ct_overrides.append(
                f'<Override PartName="/ppt/notesSlides/notesSlide{idx}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>'
            )

        pres_xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="R9fa24dbb0a2c4430"/></p:sldMasterIdLst>'
            '<p:notesMasterIdLst><p:notesMasterId r:id="R1a8d7c9194604e09"/></p:notesMasterIdLst>'
            f'<p:sldIdLst>{sld_ids_xml}</p:sldIdLst>'
            '<p:sldSz cx="12192000" cy="6858000"/>'
            '<p:notesSz cx="6858000" cy="9144000"/>'
            '</p:presentation>'
        )
        ET.fromstring(pres_xml)
        out.writestr("ppt/presentation.xml", pres_xml.encode("utf8"))

        pres_rels = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="/ppt/theme/theme1.xml" Id="R8ca6b5537d1c44a8"/>'
            '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="/ppt/slideMasters/slideMaster1.xml" Id="R9fa24dbb0a2c4430"/>'
            '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="/ppt/notesMasters/notesMaster1.xml" Id="R1a8d7c9194604e09"/>'
            '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="/ppt/presProps.xml" Id="R4bc2100960a64764"/>'
            '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles" Target="/ppt/tableStyles.xml" Id="R16729e59c05f47f3"/>'
            + pres_rels_extra
            + '</Relationships>'
        )
        ET.fromstring(pres_rels)
        out.writestr("ppt/_rels/presentation.xml.rels", pres_rels.encode("utf8"))

        content_types = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="png" ContentType="image/png"/>'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            + "".join(ct_overrides)
            + '</Types>'
        )
        ET.fromstring(content_types)
        out.writestr("[Content_Types].xml", content_types.encode("utf8"))

    # Round-trip audit of every XML file inside generated PPTX
    with zipfile.ZipFile(out_pptx, "r") as z:
        xml_files = [n for n in z.namelist() if n.endswith((".xml", ".rels"))]
        for xf in xml_files:
            ET.fromstring(z.read(xf))

    print(f"Built {out_pptx.name} with {len(xml_files)} validated XML parts")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true",
                        help="Render the actual PPTX with soffice and pdftoppm and update the PNG preview")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="civl7023-b-slides-") as temp:
        render_dir = Path(temp)
        plot = render_dir / "horizontal_error.png"
        plot_horizontal_error(plot)
        slides = [dict(spec, img=spec.get("img", plot), notes=notes)
                  for spec, notes in zip(SLIDES_SPEC, speaker_notes(), strict=True)]
        deck = render_dir / "B_Stage4_Slides_EN.pptx"
        build_deck(deck, slides)
        if args.preview:
            preview = render_dir / "B_Stage4_Slides_Preview.png"
            render_preview_sheet(deck, preview, render_dir)
            (FIG_DIR / preview.name).write_bytes(preview.read_bytes())
        (OUT_DIR / deck.name).write_bytes(deck.read_bytes())


if __name__ == "__main__":
    main()
