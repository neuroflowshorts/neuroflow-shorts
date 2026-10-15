"""NeuroFlow Shorts bot.
Picks a topic -> Gemini writes a script -> edge-tts voice -> Pexels clips -> ffmpeg builds
a 1080x1920 video with captions. Output: output/short.mp4 and output/meta.json
"""
import asyncio
import csv
import datetime
import json
import os
import pathlib
import random
import re
import subprocess
import time

import requests

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "output"
WORK = OUT / "work"
WORK.mkdir(parents=True, exist_ok=True)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "")
VOICE = os.environ.get("TTS_VOICE", "en-US-AriaNeural")  # try en-IN-NeerjaNeural for an Indian accent

SYSTEM = """You write scripts for YouTube Shorts for the channel NeuroFlow: gentle, science-informed productivity for neurodivergent people (ADHD, autism, anxiety) and anyone who struggles with executive dysfunction.

Voice: warm, calm, validating, like a kind friend who truly gets it. Never shaming. No hustle culture, no 'just try harder', no 5 AM routines.

Safety rules: never diagnose, never claim to treat or cure anything, never state medical claims as certain. Use hedged language such as 'many people with ADHD find', 'can feel like' or 'research suggests'. Never describe how the brain or nervous system works as certain fact. Do not invent studies, statistics, or expert names. Stick to widely accepted ideas (body doubling, task initiation, time blindness, energy management, sensory breaks, self-compassion).

Structure (75 to 105 words total, about 35 to 45 seconds spoken):
1. Hook: first sentence, 12 words or fewer, names a relatable struggle.
2. One sentence of validation explaining why it is hard (it is the brain, not laziness).
3. ONE concrete tiny tip, plus a low-energy version of it.
4. A soft closing line inviting the viewer to follow for more gentle tools. No pressure.

Style: plain spoken sentences. No emojis, no hashtags, no headings, no stage directions, no lists.

Return ONLY JSON with these keys:
title: string, 70 characters or fewer, relatable, honest, not clickbait
script: string, the narration exactly as spoken
visual_keywords: array of 8 stock-video search phrases, each 2 or 3 simple words, for calm visuals (for example 'writing notebook', 'window sunlight', 'coffee desk', 'laptop typing', 'person walking', 'plant leaves'); avoid anything with readable text
hook: string, 3 to 6 words, bold opening text shown on screen that names the struggle (for example 'Inbox dread? Try this.')
description: string, two short sentences
tags: array of 8 to 10 strings"""

GENERIC = ["calm nature", "soft light", "coffee cup", "plant leaves", "person walking", "clouds sky"]

DISCLAIMER = "Narration is AI-generated and visuals are licensed stock footage. This video is for general education and support, not medical advice. Please talk to a qualified professional about diagnosis or treatment."


def pick_topic():
    with open(ROOT / "topics.csv", encoding="utf-8") as f:
        topics = [r[0].strip() for r in csv.reader(f) if r and r[0].strip()]
    return topics[datetime.date.today().toordinal() % len(topics)]


def ask_gemini(topic):
    models = []
    for m in (MODEL, "gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-flash"):
        if m not in models:
            models.append(m)
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"parts": [{"text": f"Topic: {topic}\nWrite a fresh, specific take. Avoid generic advice."}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9},
    }
    last = None
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        for attempt in range(3):
            try:
                r = requests.post(url, headers={"x-goog-api-key": GEMINI_KEY}, json=body, timeout=60)
                if r.status_code != 200:
                    print(f"GEMINI ERROR [{model}] HTTP {r.status_code}: {r.text[:400]}")
                    last = f"HTTP {r.status_code}"
                    if r.status_code in (400, 401, 403, 404):
                        break  # try next model
                    time.sleep(15 * (attempt + 1))  # busy server: wait longer each time
                    continue
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                data = json.loads(text)
                n = len(data["script"].split())
                if not 55 <= n <= 125:
                    raise ValueError(f"script has {n} words, retrying")
                print("Gemini OK with model:", model)
                return data
            except Exception as e:
                last = e
                print(f"Gemini problem [{model}]:", e)
                time.sleep(3)
    raise RuntimeError(f"Gemini failed on all models. Last error: {last}")


def clean(text):
    text = re.sub(r"[*_#`]", "", text)
    return re.sub(r"\s+", " ", text).strip()


async def tts(text, mp3):
    import edge_tts
    try:
        comm = edge_tts.Communicate(text, VOICE, rate="-5%", boundary="WordBoundary")
    except TypeError:  # older edge-tts versions only emit word boundaries anyway
        comm = edge_tts.Communicate(text, VOICE, rate="-5%")
    words = []
    with open(mp3, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                start = ch["offset"] / 1e7
                words.append((ch["text"], start, start + ch["duration"] / 1e7))
    return words


def probe(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)]
    )
    return float(out.strip())


def fake_words(text, dur):
    ws = text.split()
    step = dur / max(len(ws), 1)
    return [(w, i * step, (i + 1) * step) for i, w in enumerate(ws)]


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def make_ass(words, path, per=3, hook=None):
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,"
        "MarginL,MarginR,MarginV,Encoding\n"
        "Style: Main,DejaVu Sans,76,&H00FFFFFF,&H000000FF,&H00302010,&H80000000,-1,0,0,0,100,100,0,0,1,7,2,5,90,90,0,1\n"
        "Style: Hook,DejaVu Sans,96,&H0000E5FF,&H000000FF,&H00201008,&H80000000,-1,0,0,0,100,100,0,0,1,9,3,8,70,70,330,1\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )
    lines = []
    if hook:
        hw = re.sub(r"[{}\\]", "", hook).upper().split()
        if len(hw) > 3:
            mid = (len(hw) + 1) // 2
            htxt = " ".join(hw[:mid]) + "\\N" + " ".join(hw[mid:])
        else:
            htxt = " ".join(hw)
        lines.append(f"Dialogue: 1,{ts(0.05)},{ts(2.6)},Hook,,0,0,0,,{htxt}")
    chunks = [words[i:i + per] for i in range(0, len(words), per)]
    for i, ch in enumerate(chunks):
        start = ch[0][1]
        end = chunks[i + 1][0][1] if i + 1 < len(chunks) else ch[-1][2] + 0.3
        text = " ".join(w[0] for w in ch).replace("{", "").replace("}", "")
        lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Main,,0,0,0,,{text}")
    pathlib.Path(path).write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def fetch_pexels(keywords, want=5):
    paths, seen = [], set()
    if not PEXELS_KEY:
        print("No PEXELS_API_KEY, using plain background.")
        return paths
    for kw in keywords:
        if len(paths) >= want:
            break
        try:
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": PEXELS_KEY},
                params={"query": kw, "orientation": "portrait", "size": "medium", "per_page": 8},
                timeout=30,
            )
            vids = r.json().get("videos", [])
            random.shuffle(vids)
            for v in vids:
                if v["id"] in seen:
                    continue
                files = [f for f in v["video_files"]
                         if f.get("file_type") == "video/mp4" and f.get("height", 0) >= 1080
                         and f["height"] >= f.get("width", 0)]
                if not files:
                    continue
                best = min(files, key=lambda x: x["height"])
                p = WORK / f"raw{len(paths)}.mp4"
                p.write_bytes(requests.get(best["link"], timeout=180).content)
                seen.add(v["id"])
                paths.append(p)
                break
        except Exception as e:
            print("Pexels failed for", kw, e)
    return paths


def fetch_pixabay(keywords, want=5):
    paths, seen = [], set()
    for kw in keywords:
        if len(paths) >= want:
            break
        try:
            r = requests.get(
                "https://pixabay.com/api/videos/",
                params={"key": PIXABAY_KEY, "q": kw, "per_page": 10, "safesearch": "true"},
                timeout=30,
            )
            hits = r.json().get("hits", [])
            random.shuffle(hits)
            for h in hits:
                if h["id"] in seen:
                    continue
                vids = h.get("videos", {})
                pick = next((vids[k] for k in ("large", "medium") if vids.get(k, {}).get("url")), None)
                if not pick:
                    continue
                p = WORK / f"raw{len(paths)}.mp4"
                p.write_bytes(requests.get(pick["url"], timeout=180).content)
                seen.add(h["id"])
                paths.append(p)
                break
        except Exception as e:
            print("Pixabay failed for", kw, e)
    return paths


def fetch_clips(keywords, want=5):
    if PIXABAY_KEY:
        clips = fetch_pixabay(keywords, want)
        if clips:
            return clips
    if PEXELS_KEY:
        return fetch_pexels(keywords, want)
    print("No stock-video key set, using plain background.")
    return []


def run(cmd):
    subprocess.run(cmd, check=True, cwd=WORK)


def build(clips, total):
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p"
    enc = ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23"]
    if clips:
        seg = total / len(clips)
        names = []
        for i, c in enumerate(clips):
            run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", c.name,
                 "-t", f"{seg:.3f}", "-vf", vf] + enc + [f"seg{i}.mp4"])
            names.append(f"seg{i}.mp4")
        (WORK / "list.txt").write_text("".join(f"file '{n}'\n" for n in names))
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt",
             "-c", "copy", "bg.mp4"])
    else:
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
             f"color=c=0x1f2a44:s=1080x1920:r=30:d={total:.2f}", "-pix_fmt", "yuv420p"] + enc + ["bg.mp4"])

    music = sorted((ROOT / "music").glob("*.mp3"))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", "bg.mp4", "-i", "voice.mp3"]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(random.choice(music).resolve())]
        af = "[1:a]anull[a1];[2:a]volume=0.08[a2];[a1][a2]amix=inputs=2:duration=first:normalize=0[mix];[mix]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
    else:
        af = "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
    cmd += ["-filter_complex", "[0:v]ass=captions.ass[v];" + af, "-map", "[v]", "-map", "[a]",
            "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
            str((OUT / "short.mp4").resolve())]
    run(cmd)


def main():
    topic = os.environ.get("TOPIC") or pick_topic()
    print("Topic:", topic)
    data = ask_gemini(topic)
    script = clean(data["script"])
    words = asyncio.run(tts(script, WORK / "voice.mp3"))
    dur = probe(WORK / "voice.mp3")
    if not words:
        words = fake_words(script, dur)
    make_ass(words, WORK / "captions.ass", hook=data.get("hook"))
    clips = fetch_clips(list(data.get("visual_keywords", [])) + GENERIC, want=9)
    total = min(dur + 0.6, 59.0)
    build(clips, total)

    tags = [str(t)[:30] for t in data.get("tags", [])][:10]
    hashtags = "#Shorts #ADHD #Neurodivergent #GentleProductivity"
    title = clean(data["title"])[:92]
    meta = {
        "title": title,
        "description": f"{clean(data.get('description', ''))}\n\nNew gentle tools every day. Follow NeuroFlow.\n\n{hashtags}\n\n{DISCLAIMER}",
        "tags": tags + ["Shorts", "ADHD", "neurodivergent", "executive dysfunction"],
        "topic": topic,
        "script": script,
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Done:", title, f"({total:.1f}s)")


if __name__ == "__main__":
    main()
