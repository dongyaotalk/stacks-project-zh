"""Prepare an AJbook candidate manuscript from already rendered model lanes."""
import argparse
from collections import Counter
from pathlib import Path
import re

from .chapter_templates import manifest_chapters
from .extraction import Policy
from .provenance import _parse_registry_section
from .records import RecordError, load_upstream_commit
from .validation_io import current_inputs, read_text, tracked_inputs
from .workflow import (
    _chapter_scaffold,
    _install_render_outputs,
    _load_chapter_title_translations,
    _load_tags,
    _project_container_tex,
)


CHAPTER_INPUT = re.compile(r"^\\input\{\\TranslationModelDirectory/chapters/([^{}]+)\}$", re.MULTILINE)
SOURCE_REVISION = re.compile(r"英文源提交\s+([0-9a-f]{12,40})")
CORRECTION_MODELS = re.compile(r"修订模型=([A-Za-z0-9._+, -]+)")
SAFE_ID = re.compile(r"[A-Za-z0-9._+-]+")
COLORS = ("blue!55!black", "teal!60!black", "violet!63!black", "orange!70!black")


def _tex_id(value):
    if not SAFE_ID.fullmatch(value):
        raise RecordError(f"unsafe TeX identity: {value!r}")
    return value.replace("_", r"\_")


def _source_page(chapters, registry, corrections):
    counts = Counter(lane for _, lane in chapters if lane)
    marks = {
        lane: rf"\textcolor{{{COLORS[index % len(COLORS)]}}}{{{_tex_id(registry[lane]['model_id'])}}}"
        for index, lane in enumerate(counts)
    }
    legend = [
        rf"\noindent {marks[lane]}（{counts[lane]} 章，Harness: {_tex_id(registry[lane]['harness_id'])}）\par"
        for lane in counts
    ]
    corrections_text = [
        r"\noindent " + marks[lane] + " 书稿含修订模型 "
        + ", ".join(_tex_id(model.strip()) for model in corrections[lane].split(","))
        + r"。完整运行记录见 \texttt{translation-data}。\par"
        for lane in counts if corrections[lane]
    ]
    cells = []
    for number, (slug, lane) in enumerate(chapters, 1):
        label = marks[lane] if lane else ("索引" if slug == "index" else r"\textcolor{black!58}{待译}")
        cells.append((rf"\hyperref[{slug}-section-phantom]{{{number}}}", label))
    height = (len(cells) + 3) // 4
    cells.extend([("", "")] * (4 * height - len(cells)))
    rows = [
        " & ".join(value for start in range(0, len(cells), height) for value in cells[start + line]) + r" \\"
        for line in range(height)
    ]
    return "\n".join([
        r"\chapter*{各章译文来源}",
        r"\phantomsection",
        r"\label{chapter-source-index}",
        r"\addcontentsline{toc}{chapter}{各章译文来源}",
        r"\noindent 点击章号可跳转到对应章节。\par\smallskip",
        r"\begingroup\small",
        *legend,
        *corrections_text,
        r"\noindent 待译章节保留标题。索引由排版程序生成。\par\medskip",
        r"\fontsize{9}{10.4}\selectfont",
        r"\setlength{\tabcolsep}{4pt}",
        r"\renewcommand{\arraystretch}{1.05}",
        r"\noindent\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}rlrlrlrl@{}}",
        r"\hline",
        " & ".join([r"\textbf{章号} & \textbf{通道}"] * 4) + r" \\",
        r"\hline",
        *rows,
        r"\hline",
        r"\end{tabular*}\par",
        r"\endgroup",
        "",
    ])


@tracked_inputs
def prepare_candidate_book(root: Path, harvest: Path, lanes: list[str]):
    if not lanes or len(lanes) != len(set(lanes)):
        raise RecordError("provide a nonempty ordered list of distinct candidate lanes")

    revision = load_upstream_commit(root / "upstream.lock")
    registry = _parse_registry_section(read_text(root / "config/models.yml"), "lanes")
    manifest = manifest_chapters(read_text(harvest / "chapters.tex"))
    chapter_names = [slug for slug, _ in manifest]
    titles = _load_chapter_title_translations(root / "config/chapter-titles.json", chapter_names)
    tags = _load_tags(harvest / "tags" / "tags")
    policy = Policy(read_text(root / "config/macro-policy.yml"))

    translations = root / "ajbook-template/translations"
    corrections = {}
    for lane in lanes:
        if not SAFE_ID.fullmatch(lane) or ".." in lane or registry.get(lane, {}).get("kind") != "model_candidate":
            raise RecordError(f"not a registered candidate lane: {lane}")
        directory = translations / lane
        metadata = read_text(directory / "metadata.tex")
        source = SOURCE_REVISION.search(metadata)
        if source is None or not revision.startswith(source[1]):
            raise RecordError(f"{lane}: rendered manuscript does not identify the locked English source")
        if CHAPTER_INPUT.findall(read_text(directory / "contents.tex")) != chapter_names:
            raise RecordError(f"{lane}: expected a full manuscript in locked chapter order")
        correction = CORRECTION_MODELS.search(metadata)
        corrections[lane] = correction[1].strip() if correction else ""

    selected = {}
    chapters = []
    labels = set()
    for slug, title in manifest:
        scaffold = _chapter_scaffold(slug, titles[slug], title)
        selected[slug] = scaffold
        source_lane = ""
        if slug != "index":
            for lane in lanes:
                chapter = read_text(translations / lane / "chapters" / f"{slug}.tex")
                if chapter.strip() != scaffold.strip():
                    selected[slug] = chapter
                    source_lane = lane
                    break
        _, chapter_labels = _project_container_tex(selected[slug], slug, policy, tags)
        labels.update(chapter_labels)
        chapters.append((slug, source_lane))

    output = translations / "candidate"
    payloads = {
        output / "chapters" / f"{slug}.tex": _project_container_tex(tex, slug, policy, tags, labels)[0].encode()
        for slug, tex in selected.items()
    }
    payloads[output / "contents.tex"] = "".join(
        rf"\input{{\TranslationModelDirectory/chapters/{slug}}}" + "\n" for slug in chapter_names
    ).encode()
    payloads[output / "frontmatter.tex"] = _source_page(chapters, registry, corrections).encode()
    payloads[output / "metadata.tex"] = (
        r"\renewcommand{\TranslationModelName}{多通道全书候选译文}" + "\n"
        r"\renewcommand{\TranslationMaintainer}{OpenSSL}" + "\n"
        r"\renewcommand{\TranslationStatus}{未经人工审校的模型候选译文}" + "\n"
        rf"\renewcommand{{\TranslationNotice}}{{英文源提交 {revision[:12]}。"
        r"各章实际采用的书稿与模型信息见\hyperref[chapter-source-index]{各章译文来源}。"
        "完整运行记录见 translation-data。}\n"
    ).encode()
    _install_render_outputs(output, payloads, current_inputs().assert_unchanged)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--harvest", type=Path, required=True)
    parser.add_argument("--lane", dest="lanes", action="append", required=True)
    args = parser.parse_args()
    try:
        output = prepare_candidate_book(args.root.resolve(), args.harvest.resolve(), args.lanes)
    except (OSError, RecordError) as error:
        parser.exit(1, f"ERROR: {error}\n")
    print(f"Prepared the candidate book: {output}")


if __name__ == "__main__":
    main()
