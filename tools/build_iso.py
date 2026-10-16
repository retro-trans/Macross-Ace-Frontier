"""Build a translated test ISO of Macross Ace Frontier from the original disc.

Usage:
  python tools/build_iso.py <version> [--iso "<original>.iso"] [--tr <insert.json>] [--no-hd] [--no-images] [--work <dir>]
                            [--voice-subs <subs.json> ...] [--voice-placeholder]
  e.g. python tools/build_iso.py 0.1.0

Needs (once): the USRDIR files and the decrypted EBOOT extracted as in docs/formats.md,
work/source/dat (tools/muf_archive.py extract), work/source/text (dump_text.py, dump_eboot.py),
and work/translation/en/insert.json (tools/corpus_slice.py merge + export).

Steps (each one is a tool that can also be run on its own):
  1. tools/eboot_insert.py  relocate the English EBOOT text, reserve 3 KB  -> <work>/EBOOT.ins.bin
     (1 KB for the VWF width table, 2 KB for the voice-subtitle hooks)
  2. tools/vwf_build.py     VWF font + patches on that EBOOT              -> <work>/vwf/
  2b. tools/voice_subs_patch.py voice-subtitle hooks (only with --voice-subs or
     --voice-placeholder; docs/voice_subtitles.md)                        -> <work>/EBOOT.BIN
  3. tools/insert_text.py   FES string pools and mission unit lists       -> <work>/overlay/
     (the VWF font is copied into the same overlay)
  3b. tools/redraw_images.py English redrawn textures (GIM)              -> <work>/overlay/
     (skip with --no-images; layout in work/ui/redraw_layout.json, docs/image_redraw.md)
  3c. tools/voice_subs_at3.py English line appended to each voice clip    -> <work>/overlay/
     (with --voice-subs; --voice-placeholder writes each clip's id instead, to test the hooks)
  4. tools/muf_archive.py   repack with the overlay                       -> <work>/USRDIR/
  5. tools/iso_patch.py     new EBOOT and archives                        -> work/output/Macross Ace Frontier (EN v<version>).iso

The EBOOT on the disc is the decrypted PRX (plain ELF). PPSSPP and custom firmware load it as it is.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def run(*args):
    print(">", " ".join(args), flush=True)
    subprocess.run([PY, "-I"] + list(args), cwd=ROOT, check=True)


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("--"):
        sys.exit(__doc__)
    version = args.pop(0)
    iso = "Macross Ace Frontier (Japan).iso"
    tr = os.path.join("work", "translation", "en", "insert.json")
    vwf_args, work, images = [], None, True
    voice_subs, voice_placeholder = [], False
    while args:
        a = args.pop(0)
        if a == "--iso":
            iso = args.pop(0)
        elif a == "--tr":
            tr = args.pop(0)
        elif a == "--no-hd":
            vwf_args.append("--no-hd")
        elif a == "--no-images":
            images = False
        elif a == "--voice-subs":
            voice_subs.append(args.pop(0))
        elif a == "--voice-placeholder":
            voice_placeholder = True
        elif a == "--work":
            work = args.pop(0)
        else:
            sys.exit("unknown argument " + a)
    b = work or os.path.join("work", "output", "build")
    ins = os.path.join(b, "EBOOT.ins.bin")
    vwf = os.path.join(b, "vwf")
    overlay = os.path.join(b, "overlay")
    usrdir = os.path.join(b, "USRDIR")
    out_iso = os.path.join("work", "output", "Macross Ace Frontier (EN v%s).iso" % version)
    if os.path.isdir(os.path.join(ROOT, overlay)):
        shutil.rmtree(os.path.join(ROOT, overlay))

    voice = bool(voice_subs or voice_placeholder)
    eboot = os.path.join(vwf, "EBOOT.BIN")
    run("tools/eboot_insert.py", "--reserve", "3072", "--out", ins, tr)
    run("tools/vwf_build.py", "--eboot", ins, "--out", vwf, *vwf_args)
    if voice:
        eboot = os.path.join(b, "EBOOT.BIN")
        run("tools/voice_subs_patch.py", os.path.join(vwf, "EBOOT.BIN"), eboot, "--area", ins + ".json")
    run("tools/insert_text.py", "--out", overlay, tr)
    font = os.path.join("data", "extra", "gpsp3_font14.fnt")
    os.makedirs(os.path.join(ROOT, overlay, "data", "extra"), exist_ok=True)
    shutil.copyfile(os.path.join(ROOT, vwf, font), os.path.join(ROOT, overlay, font))
    if images:
        run("tools/redraw_images.py", "--out", overlay, "--preview", os.path.join(b, "redraw"), "--no-sheets")
    if voice:
        run("tools/voice_subs_at3.py", "--out", overlay, "--widths", os.path.join(vwf, "vwf_widths.json"),
            *(["--placeholder"] if voice_placeholder else voice_subs))
    run("tools/muf_archive.py", "repack", os.path.join("work", "source", "dat"), usrdir,
        "--base", os.path.join("work", "source", "iso", "USRDIR"), "--overlay", overlay)
    run("tools/iso_patch.py", iso, out_iso,
        "PSP_GAME/SYSDIR/EBOOT.BIN=" + eboot,
        *["PSP_GAME/USRDIR/%s=%s" % (f, os.path.join(usrdir, f)) for f in ("fileset.dat", "macross.dat", "macross.idx")])
    print("built", out_iso)


if __name__ == "__main__":
    main()
