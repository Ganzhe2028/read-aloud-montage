"""Build a reading video from files in one folder, on macOS or Windows."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from selection import Excerpt, choose_excerpt


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "待处理音频"
DEFAULT_OUTPUT = ROOT / "成片"
BACKGROUND = ROOT / "素材" / "海边日落.png"
SUPPORTED = {".m4a", ".mp3", ".wav", ".aac", ".mp4"}


def ffmpeg_path() -> str:
    override = os.environ.get("READING_FFMPEG")
    if override and Path(override).is_file():
        return override
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError, OSError):
        fallback = shutil.which("ffmpeg")
        if fallback:
            return fallback
    raise RuntimeError("找不到视频处理组件；请先运行本机的‘首次安装’入口")


def run_ffmpeg(executable: str, arguments: list[str]) -> None:
    result = subprocess.run(
        [executable, "-nostdin", "-hide_banner", "-v", "error", *arguments],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[-700:] or "音视频处理失败")


def digest(path: Path) -> str:
    checksum = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def find_font() -> str | None:
    options = (
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "msyh.ttc",
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "simsun.ttc",
    )
    return str(next((path for path in options if path.is_file()), "")) or None


def make_background(destination: Path, stamp: str) -> bool:
    if not BACKGROUND.is_file():
        raise RuntimeError("背景图不在‘素材’文件夹，请把工具文件夹恢复完整")
    with Image.open(BACKGROUND) as source:
        image = ImageOps.fit(source.convert("RGB"), (1280, 720), method=Image.Resampling.LANCZOS)
    font_path = find_font()
    if font_path:
        draw = ImageDraw.Draw(image)
        title_font = ImageFont.truetype(font_path, 74)
        sub_font = ImageFont.truetype(font_path, 32)
        draw.text((700, 505), "朗读集锦", font=title_font, fill="#fff2db", stroke_width=3, stroke_fill="#241c1c")
        draw.text((705, 605), f"一起读书  ·  {stamp}", font=sub_font, fill="#ffe8c1", stroke_width=2, stroke_fill="#241c1c")
    image.save(destination)
    return font_path is not None


def extract_audio(executable: str, source: Path, excerpt: Excerpt, destination: Path) -> None:
    length = excerpt.end - excerpt.start
    run_ffmpeg(executable, [
        "-y", "-ss", f"{excerpt.start:.3f}", "-i", str(source),
        "-t", f"{length:.3f}", "-vn",
        "-af", f"loudnorm=I=-18:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.12,afade=t=out:st={max(0, length - 0.22):.3f}:d=0.22",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(destination),
    ])


def render_video(executable: str, background: Path, excerpts: list[Path], destination: Path, temp: Path) -> None:
    concat_file = temp / "audio-list.txt"
    concat_file.write_text(
        "ffconcat version 1.0\n" + "".join(f"file '{path.name}'\n" for path in excerpts),
        encoding="utf-8",
    )
    run_ffmpeg(executable, [
        "-y", "-loop", "1", "-framerate", "30", "-i", str(background),
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-map", "0:v:0", "-map", "1:a:0", "-shortest",
        "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(destination),
    ])
    run_ffmpeg(executable, ["-xerror", "-i", str(destination), "-f", "null", "-"])


def report_html(title: str, video: Path, included: list[dict], skipped: list[str], font_found: bool) -> str:
    escape = lambda value: html.escape(str(value), quote=True)
    rows = []
    for index, item in enumerate(included, start=1):
        cells = (
            index, item["file"], f"{item['start']:.1f}–{item['end']:.1f} 秒",
            f"{item['speech_seconds']:.1f} 秒", item["warning"] or "请试听首尾",
        )
        rows.append("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in cells) + "</tr>")
    skipped_list = "".join(f"<li>{escape(item)}</li>" for item in skipped) or "<li>无</li>"
    font_warning = "" if font_found else "<p>本机没有找到可用的中文字体，视频背景未叠加标题。</p>"
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · 核对清单</title><style>body{{font:18px/1.6 -apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif;background:#f7f6f2;color:#24362b;margin:0}}main{{max-width:980px;margin:40px auto;padding:0 24px}}section{{background:#fff;border-radius:18px;padding:24px 30px;margin:20px 0}}h1{{font-size:32px}}h2{{font-size:23px}}table{{width:100%;border-collapse:collapse;font-size:15px}}th,td{{text-align:left;vertical-align:top;border-bottom:1px solid #e5e9e3;padding:11px 9px}}th{{background:#edf3eb}}a{{color:#236d4d}}li{{margin:8px 0}}@media(max-width:650px){{table{{display:block;overflow-x:auto}}}}</style></head><body><main>
<h1>{escape(title)}</h1><section><p>本次入片 {len(included)} 条 · <a href="{escape(video.name)}">播放视频</a></p><p>程序只处理“待处理音频”文件夹里的文件；请核对是否有尚未放进来的投稿。</p></section>
<section><h2>入片顺序</h2><table><thead><tr><th>顺序</th><th>文件名</th><th>原音频选段</th><th>检测到的人声</th><th>提醒</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
<section><h2>未入片</h2><ul>{skipped_list}</ul>{font_warning}</section>
<section><h2>分享前</h2><p>请试听每段开头、结尾和交接处，核对朗读者身份及内容。人声检测无法判断朗读质量、错字或句子是否完整。确认后，再自行决定是否分享。</p></section>
</main></body></html>"""


def build(input_dir: Path, output_dir: Path) -> tuple[Path, Path, int, int]:
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(
        (path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED),
        key=lambda path: path.name.casefold(),
    )
    if not paths:
        raise RuntimeError(f"‘{input_dir.name}’里没有音频；请先把本期文件放进去")
    executable = ffmpeg_path()
    skipped = []
    unique = []
    seen = set()
    for path in paths:
        try:
            file_hash = digest(path)
        except OSError as error:
            skipped.append(f"{path.name}：无法读取文件（{error}）")
            continue
        if file_hash in seen:
            skipped.append(f"{path.name}：与另一份文件内容相同，未重复入片")
            continue
        seen.add(file_hash)
        unique.append(path)
    if not unique:
        raise RuntimeError("本期没有可读取的音频；原有成片未改动")

    vad_python = os.environ.get("READING_VAD_PYTHON", sys.executable)
    detected = subprocess.run(
        [vad_python, str(ROOT / "voice_detect.py")],
        input=json.dumps([str(path) for path in unique], ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if detected.returncode:
        raise RuntimeError("本地人声检测无法启动；请先运行‘首次安装’。" + detected.stderr.strip()[-300:])
    results = json.loads(detected.stdout)
    if len(results) != len(unique):
        raise RuntimeError("人声检测返回的文件数不符；原有成片未改动")
    day = datetime.now().strftime("%Y-%m-%d")
    video = output_dir / f"朗读合辑-{day}-待审核.mp4"
    report = output_dir / f"朗读合辑-{day}-核对清单.html"
    included = []
    with tempfile.TemporaryDirectory(prefix="reading-", dir=ROOT / ".work") as temp_name:
        temp = Path(temp_name)
        background = temp / "background.png"
        font_found = make_background(background, day)
        excerpt_paths = []
        for item in results:
            source = Path(item["path"])
            if "error" in item:
                skipped.append(f"{source.name}：无法读取音频（{item['error']}）")
                continue
            excerpt = choose_excerpt(item["speech"], float(item["duration"]))
            if excerpt is None:
                skipped.append(f"{source.name}：没有检测到足够的人声，请人工检查")
                continue
            excerpt_path = temp / f"clip-{len(excerpt_paths):04d}.wav"
            try:
                extract_audio(executable, source, excerpt, excerpt_path)
            except RuntimeError as error:
                skipped.append(f"{source.name}：截取失败（{error}）")
                continue
            excerpt_paths.append(excerpt_path)
            included.append({
                "file": source.name,
                "start": excerpt.start,
                "end": excerpt.end,
                "speech_seconds": excerpt.speech_seconds,
                "warning": excerpt.warning,
            })
        if not excerpt_paths:
            raise RuntimeError("没有找到可用的朗读片段；原有成片未改动")
        assembled = temp / "assembled.mp4"
        render_video(executable, background, excerpt_paths, assembled, temp)
        title = f"朗读合辑 {day}"
        report_text = report_html(title, video, included, skipped, font_found)
        report_temp = temp / "report.html"
        report_temp.write_text(report_text, encoding="utf-8")
        os.replace(assembled, video)
        os.replace(report_temp, report)
    return video, report, len(included), len(skipped)


def main() -> int:
    parser = argparse.ArgumentParser(description="从本期音频文件夹制作朗读视频")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    (ROOT / ".work").mkdir(exist_ok=True)
    try:
        video, report, included, skipped = build(args.input_dir, args.output_dir)
    except Exception as error:
        print(f"制作未完成：{error}", file=sys.stderr)
        return 1
    print(f"制作完成：入片 {included} 条，需检查 {skipped} 条")
    print(f"视频：{video}")
    print(f"核对清单：{report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
