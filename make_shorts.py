import os, asyncio, subprocess
from PIL import Image, ImageEnhance
import edge_tts

TITLE = os.environ.get("SHORTS_TITLE", "10초 일본어 #Shorts").replace("\r", "").replace("\n", " ").strip()
HOOK = os.environ.get("SHORTS_HOOK", "일본 친구랑 헤어질 때 자연스럽게 인사할 때").replace("\r", "").replace("\n", " ").strip()
WORD = os.environ.get("SHORTS_WORD", "お願いします").replace("\r", "").replace("\n", " ").strip()
PRON = os.environ.get("SHORTS_PRON", "おねがいします  [ 오네가이시마스 ]").replace("\r", "").replace("\n", " ").strip()
MEANING = os.environ.get("SHORTS_MEANING", "부탁합니다, 주세요").replace("\r", "").replace("\n", " ").strip()
EXAMPLE = os.environ.get("SHORTS_EXAMPLE", "お水をお願いします。").replace("\r", "").replace("\n", " ").strip()
EXAMPLE_PRON = os.environ.get("SHORTS_EXAMPLE_PRON", "오미즈오 오네가이시마스").replace("\r", "").replace("\n", " ").strip()
EXAMPLE_KO = os.environ.get("SHORTS_EXAMPLE_KO", "물 좀 부탁드립니다.").replace("\r", "").replace("\n", " ").strip()

VOICE_JP = "ja-JP-NanamiNeural"
VOICE_KO = "ko-KR-SunHiNeural"

async def generate_tts(text, voice, raw_file, final_file, rate="+5%", end_pad=0.15):
    await edge_tts.Communicate(text, voice, rate=rate, volume="+12%").save(raw_file)
    af = f"silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse,apad=pad_dur={end_pad}"
    subprocess.run(["ffmpeg", "-y", "-i", raw_file, "-af", af, "-c:a", "libmp3lame", "-q:a", "2", final_file], check=True)

def get_duration(filename):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename]
    return float(subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)

def split_ko_2lines(text, max_chars=14):
    clean = " ".join(text.split())
    words, lines, current = clean.split(" "), [], ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current = (current + " " + w).strip()
        else:
            if current:
                lines.append(current)
            current = w
            if len(lines) >= 2:
                break
    if current and len(lines) < 2:
        lines.append(current)
    line1 = lines[0] if len(lines) > 0 else ""
    line2 = lines[1] if len(lines) > 1 else ""
    return line1.strip(), line2.strip()

def split_jp_2lines(text, max_chars=18):
    clean = text.strip()
    if len(clean) <= max_chars:
        return clean, ""
    return clean[:max_chars].strip(), clean[max_chars:max_chars*2].strip()

def prepare_bg(out_path="final_bg.jpg"):
    for fname in ["bg.jpg", "bg.png", "bg.jpeg"]:
        if os.path.exists(fname):
            img = Image.open(fname).convert("RGB").resize((1080, 1920), Image.LANCZOS)
            ImageEnhance.Brightness(img).enhance(0.55).save(out_path, quality=92)
            return
    Image.new("RGB", (1080, 1920), color=(15, 23, 42)).save(out_path)

def write_line(filename, text):
    clean = text.replace("\r", "").replace("\n", "").strip()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(clean)

async def main():
    prepare_bg("final_bg.jpg")
    await generate_tts(HOOK, VOICE_KO, "h_raw.mp3", "h.mp3", rate="+12%", end_pad=0.20)
    await generate_tts(WORD, VOICE_JP, "w_raw.mp3", "w.mp3", rate="+0%", end_pad=0.20)
    await generate_tts(MEANING, VOICE_KO, "m_raw.mp3", "m.mp3", rate="+12%", end_pad=0.25)
    await generate_tts("문장 예시입니다.", VOICE_KO, "t_raw.mp3", "t.mp3", rate="+12%", end_pad=0.18)
    await generate_tts(EXAMPLE, VOICE_JP, "ex_raw.mp3", "ex.mp3", rate="+0%", end_pad=0.18)
    await generate_tts(EXAMPLE_KO, VOICE_KO, "exk_raw.mp3", "exk.mp3", rate="+12%", end_pad=0.30)

    d_h, d_w, d_m = get_duration("h.mp3"), get_duration("w.mp3"), get_duration("m.mp3")
    d_t, d_ex, d_exk = get_duration("t.mp3"), get_duration("ex.mp3"), get_duration("exk.mp3")

    t_word = d_h
    t_meaning = d_h + d_w
    t_example = d_h + d_w + d_m + d_t
    total_dur = t_example + d_ex + d_exk

    with open("concat.txt", "w") as f:
        f.write("file 'h.mp3'\nfile 'w.mp3'\nfile 'm.mp3'\nfile 't.mp3'\nfile 'ex.mp3'\nfile 'exk.mp3'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", "raw_audio.mp3"], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", "raw_audio.mp3", "-filter:a", "loudnorm=I=-15:TP=-1.5:LRA=11", "full_audio.mp3"], check=True)

    font_cjk = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    if not os.path.exists(font_cjk):
        font_cjk = "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"
    font_ko = "/usr/share/fonts/truetype/nanum/NanumSquareRoundEB.ttf"
    if not os.path.exists(font_ko):
        font_ko = font_cjk

    hira_part, kor_pron_part = PRON, ""
    if "[" in PRON:
        parts = PRON.split("[", 1)
        hira_part = parts[0].strip()
        kor_pron_part = "[" + parts[1].strip()
    if hira_part == WORD:
        hira_part = ""

    hook_1, hook_2 = split_ko_2lines(HOOK, 14)
    mean_1, mean_2 = split_ko_2lines(MEANING, 13)
    ex_jp_1, ex_jp_2 = split_jp_2lines(EXAMPLE, 18)
    ex_pr_1, ex_pr_2 = split_ko_2lines(EXAMPLE_PRON, 20)
    ex_ko_1, ex_ko_2 = split_ko_2lines(EXAMPLE_KO, 16)

    write_line("hook_1.txt", hook_1)
    write_line("hook_2.txt", hook_2)
    write_line("word.txt", WORD[:12])
    write_line("hira.txt", hira_part)
    write_line("kor_pron.txt", kor_pron_part)
    write_line("mean_1.txt", mean_1)
    write_line("mean_2.txt", mean_2)
    write_line("ex_jp_1.txt", ex_jp_1)
    write_line("ex_jp_2.txt", ex_jp_2)
    write_line("ex_pr_1.txt", ex_pr_1)
    write_line("ex_pr_2.txt", ex_pr_2)
    write_line("ex_ko_1.txt", ex_ko_1)
    write_line("ex_ko_2.txt", ex_ko_2)

    vf = (
        f"drawtext=fontfile={font_ko}:textfile=hook_1.txt:fontcolor=white:fontsize=60:borderw=6:bordercolor=black:x=(w-text_w)/2:y=190,"
        f"drawtext=fontfile={font_ko}:textfile=hook_2.txt:fontcolor=white:fontsize=60:borderw=6:bordercolor=black:x=(w-text_w)/2:y=268,"
        f"drawtext=fontfile={font_cjk}:textfile=word.txt:fontcolor=#00E5FF:fontsize=105:borderw=8:bordercolor=black:x=(w-text_w)/2:y=470:enable='gte(t,{t_word})',"
        f"drawtext=fontfile={font_cjk}:textfile=hira.txt:fontcolor=#E0E0E0:fontsize=46:borderw=4:bordercolor=black:x=(w-text_w)/2:y=620:enable='gte(t,{t_word})',"
        f"drawtext=fontfile={font_ko}:textfile=kor_pron.txt:fontcolor=#B2EBF2:fontsize=48:borderw=4:bordercolor=black:x=(w-text_w)/2:y=680:enable='gte(t,{t_word})',"
        f"drawtext=fontfile={font_ko}:textfile=mean_1.txt:fontcolor=#FFD600:fontsize=72:borderw=7:bordercolor=black:x=(w-text_w)/2:y=770:enable='gte(t,{t_meaning})',"
        f"drawtext=fontfile={font_ko}:textfile=mean_2.txt:fontcolor=#FFD600:fontsize=72:borderw=7:bordercolor=black:x=(w-text_w)/2:y=855:enable='gte(t,{t_meaning})',"
        f"drawtext=fontfile={font_cjk}:textfile=ex_jp_1.txt:fontcolor=white:fontsize=56:borderw=6:bordercolor=black:x=(w-text_w)/2:y=1010:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_cjk}:textfile=ex_jp_2.txt:fontcolor=white:fontsize=56:borderw=6:bordercolor=black:x=(w-text_w)/2:y=1080:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_ko}:textfile=ex_pr_1.txt:fontcolor=#80D8FF:fontsize=44:borderw=4:bordercolor=black:x=(w-text_w)/2:y=1200:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_ko}:textfile=ex_pr_2.txt:fontcolor=#80D8FF:fontsize=44:borderw=4:bordercolor=black:x=(w-text_w)/2:y=1258:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_ko}:textfile=ex_ko_1.txt:fontcolor=#00E676:fontsize=52:borderw=5:bordercolor=black:x=(w-text_w)/2:y=1380:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_ko}:textfile=ex_ko_2.txt:fontcolor=#00E676:fontsize=52:borderw=5:bordercolor=black:x=(w-text_w)/2:y=1448:enable='gte(t,{t_example})'"
    )
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", "final_bg.jpg", "-i", "full_audio.mp3", "-vf", vf, "-t", f"{total_dur}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "output.mp4"], check=True)
    print("네모 박스 완전 제거된 일본어 쇼츠 완료: output.mp4", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
