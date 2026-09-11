import os, shutil, subprocess, tempfile, uuid
from pathlib import Path
from flask import Flask, request, send_file, jsonify, after_this_request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def clamp(v,a,b): return max(a,min(b,v))

@app.get("/")
def home():
    return jsonify(status="ok", app="MKALFLAWLESS Shorts Creator Backend")

@app.get("/health")
def health():
    return jsonify(ok=True, ffmpeg=bool(shutil.which("ffmpeg")))

@app.post("/export")
def export():
    if "video" not in request.files:
        return jsonify(error="No video uploaded"), 400

    f = request.files["video"]
    start = max(0, float(request.form.get("start", 0)))
    length = clamp(float(request.form.get("length", 15)), 1, 600)
    camera_pos = request.form.get("camera_pos", "top").lower()

    # Same normalized camera crop concept as the trusted desktop editor.
    cx = clamp(float(request.form.get("cam_x", .01)), 0, .99)
    cy = clamp(float(request.form.get("cam_y", .09)), 0, .99)
    cw = clamp(float(request.form.get("cam_w", .24)), .02, 1)
    ch = clamp(float(request.form.get("cam_h", .44)), .02, 1)
    gx = clamp(float(request.form.get("game_x", 0)), -100, 100)
    frac = (gx + 100) / 200

    work = Path(tempfile.mkdtemp(prefix="mkalflawless_"))
    src = work / ("source" + (Path(f.filename).suffix or ".mp4"))
    out = work / "MKALFLAWLESS_SHORT.mp4"
    f.save(src)

    filters = [
        "[0:v]split=2[game_src][cam_src]",
        f"[game_src]scale=-2:1280:flags=lanczos,crop=1080:1280:(iw-1080)*{frac}:0[game]",
        f"[cam_src]crop=iw*{cw}:ih*{ch}:iw*{cx}:ih*{cy},"
        "scale=1080:640:force_original_aspect_ratio=increase:flags=lanczos,"
        "crop=1080:640,unsharp=3:3:0.18:3:3:0.00[cam]"
    ]
    filters.append("[cam][game]vstack=inputs=2[outv]" if camera_pos == "top"
                   else "[game][cam]vstack=inputs=2[outv]")

    cmd = [
        "ffmpeg","-y","-ss",str(start),"-i",str(src),"-t",str(length),
        "-filter_complex",";".join(filters),
        "-map","[outv]","-map","0:a?",
        "-c:v","libx264","-preset","medium","-crf","16",
        "-c:a","aac","-b:a","192k","-movflags","+faststart",str(out)
    ]
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            shutil.rmtree(work, ignore_errors=True)
            return jsonify(error="FFmpeg export failed", details=p.stderr[-2500:]), 500
    except Exception as e:
        shutil.rmtree(work, ignore_errors=True)
        return jsonify(error=str(e)), 500

    @after_this_request
    def cleanup(response):
        try: shutil.rmtree(work, ignore_errors=True)
        except: pass
        return response

    return send_file(out, as_attachment=True,
                     download_name="MKALFLAWLESS_SHORT.mp4",
                     mimetype="video/mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
