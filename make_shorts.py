import os, asyncio, subprocess
from PIL import Image, ImageEnhance
import edge_tts

TITLE = os.environ.get("SHORTS_TITLE", "10초 일본어 #Shorts")
HOOK = os.environ.get("SHORTS_HOOK", "일본 여행 가서 식당 주문할 때")
WORD = os.environ.get("SHORTS_WORD", "お願いします")
PRON = os.environ.get("SHORTS_PRON", "おねがいします  [ 오네가이시마스 ]")
MEANING = os.environ.get("SHORTS_MEANING", "부탁합니다, 주세요")
EXAMPLE = os.environ.get("SHORTS_EXAMPLE", "お水をお願いします。")
EXAMPLE_PRON = os.environ.get("SHORTS_EXAMPLE_PRON", "오미즈오 오네가이시마스")
EXAMPLE_KO = os.environ.get("SHORTS_EXAMPLE_KO", "물 좀 부탁드립니다.")

VOICE_JP = "ja-JP-NanamiNeural"
VOICE_KO = "ko-KR-SunHiNeural"

async def generate_tts(text, voice, raw_file, final_file, rate="+5%", end_pad=0.15):
    await edge_tts.Communicate(text, voice, rate=rate, volume="+12%").save(raw_file)
    af = f"silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_silence=0.05:start_threshold=-45dB,areverse,apad=pad_dur={end_pad}"
    subprocess.run(["ffmpeg", "-y", "-i", raw_file, "-af", af, "-c:a", "libmp3lame", "-q:a", "2", final_file], check=True)

def get_duration(filename):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filename]
    return float(subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout)

def wrap_text(text, max_chars=15):
    lines = []
    while len(text) > max_chars:
        lines.append(text[:max_chars])
        text = text[max_chars:]
    if text: lines.append(text)
    return "\n".join(lines)

def prepare_bg(out_path="final_bg.jpg"):
    for fname in ["bg.jpg", "bg.png", "bg.jpeg"]:
        if os.path.exists(fname):
            img = Image.open(fname).convert("RGB").resize((1080, 1920), Image.LANCZOS)
            ImageEnhance.Brightness(img).enhance(0.75).save(out_path, quality=92)
            return
    Image.new("RGB", (1080, 1920), color=(15, 23, 42)).save(out_path)

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
    t_word, t_meaning, t_example = d_h, d_h + d_w, d_h + d_w + d_m + d_t
    total_dur = t_example + d_ex + d_exk

    with open("concat.txt", "w") as f:
        f.write("file 'h.mp3'\nfile 'w.mp3'\nfile 'm.mp3'\nfile 't.mp3'\nfile 'ex.mp3'\nfile 'exk.mp3'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "concat.txt", "-c", "copy", "raw_audio.mp3"], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", "raw_audio.mp3", "-filter:a", "loudnorm=I=-15:TP=-1.5:LRA=11", "full_audio.mp3"], check=True)

    font_path = next((p for p in ["/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/truetype/nanum/NanumGothicExtraBold.ttf"] if os.path.exists(p)), "")
    with open("hook.txt", "w", encoding="utf-8") as f: f.write(wrap_text(HOOK, 14))
    with open("word.txt", "w", encoding="utf-8") as f: f.write(wrap_text(WORD, 10))
    with open("pron.txt", "w", encoding="utf-8") as f: f.write(PRON.strip())
    with open("meaning.txt", "w", encoding="utf-8") as f: f.write(wrap_text(MEANING, 13))
    with open("ex_en.txt", "w", encoding="utf-8") as f: f.write(wrap_text(EXAMPLE, 16))
    with open("ex_pron.txt", "w", encoding="utf-8") as f: f.write(wrap_text(EXAMPLE_PRON, 17))
    with open("ex_ko.txt", "w", encoding="utf-8") as f: f.write(wrap_text(EXAMPLE_KO, 15))

    vf = (
        f"drawbox=x=70:y=200:w=940:h=190:color=#FFD600@0.95:t=fill,"
        f"drawtext=fontfile={font_path}:textfile=hook.txt:fontcolor=#111111:fontsize=54:x=(w-text_w)/2:y=235:line_spacing=16,"
        f"drawbox=x=60:y=430:w=960:h=520:color=#0D1117@0.72:t=fill:enable='gte(t,{t_word})',"
        f"drawbox=x=60:y=430:w=960:h=520:color=#00E5FF@0.8:t=4:enable='gte(t,{t_word})',"
        f"drawtext=fontfile={font_path}:textfile=word.txt:fontcolor=#00E5FF:fontsize=95:borderw=5:bordercolor=black:x=(w-text_w)/2:y=480:enable='gte(t,{t_word})',"
        f"drawtext=fontfile={font_path}:textfile=pron.txt:fontcolor=#E0E0E0:fontsize=46:borderw=3:bordercolor=black:x=(w-text_w)/2:y=630:enable='gte(t,{t_word})',"
        f"drawtext=fontfile={font_path}:textfile=meaning.txt:fontcolor=#00E676:fontsize=70:borderw=4:bordercolor=black:x=(w-text_w)/2:y=735:line_spacing=18:enable='gte(t,{t_meaning})',"
        f"drawbox=x=60:y=990:w=960:h=630:color=#0D1117@0.78:t=fill:enable='gte(t,{t_example})',"
        f"drawbox=x=60:y=990:w=960:h=630:color=#FFD600@0.8:t=4:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_path}:text='📌 문장 예시':fontcolor=#FFD600:fontsize=46:x=(w-text_w)/2:y=1025:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_path}:textfile=ex_en.txt:fontcolor=white:fontsize=56:borderw=4:bordercolor=black:x=(w-text_w)/2:y=1110:line_spacing=16:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_path}:textfile=ex_pron.txt:fontcolor=#80D8FF:fontsize=46:borderw=3:bordercolor=black:x=(w-text_w)/2:y=1310:line_spacing=14:enable='gte(t,{t_example})',"
        f"drawtext=fontfile={font_path}:textfile=ex_ko.txt:fontcolor=#00E676:fontsize=52:borderw=3:bordercolor=black:x=(w-text_w)/2:y=1460:line_spacing=16:enable='gte(t,{t_example})'"
    )
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", "final_bg.jpg", "-i", "full_audio.mp3", "-vf", vf, "-t", f"{total_dur}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "output.mp4"], check=True)
    print("일본어 쇼츠 렌더링 완료: output.mp4", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
