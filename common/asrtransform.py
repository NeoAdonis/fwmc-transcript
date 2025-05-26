"""This module contains functions related to automatic speech recognition."""

import os

import webvtt

from common import asr, media, time

def fix_repeats(
    vtt_root, file, audio_root, model, align_model, align_metadata, limit=4
):
    """EXPERIMENTAL. Fix repeated lines in a transcript."""
    changed = False
    i = 1
    last_unique_caption = None
    last_captions = []
    last_unique_id = 0
    new_vtt = webvtt.WebVTT()
    base_name = os.path.basename(vtt_root)
    audio_path = os.path.join(audio_root, f"{base_name}/audio.opus")
    if not os.path.exists(audio_path):
        audio_path = os.path.join(audio_root, f"{base_name}/audio.webm")
    if not os.path.exists(audio_path):
        audio_path = os.path.join(audio_root, f"{base_name}/audio.mp4")
    if not os.path.exists(audio_path):
        return False
    for caption in webvtt.read(os.path.join(vtt_root, file)):
        if last_unique_caption is None:
            last_unique_caption = caption
        if caption.text != last_unique_caption.text:
            if (i - last_unique_id) > limit:
                new_start = time.str_to_timedelta(f"{last_unique_caption.start}000")
                new_end = time.str_to_timedelta(f"{caption.start}000")
                media.convert_to_wav(
                    audio_path,
                    "fragment",
                    time.timedelta_to_str(new_start),
                    time.timedelta_to_str(new_end),
                )
                fragment_audio_path = os.path.join(
                    audio_root, f"{base_name}/fragment.wav"
                )
                asr.transcribe_audio(
                    fragment_audio_path, model, align_model, align_metadata, vtt_root
                )
                fragment_vtt = os.path.join(vtt_root, "fragment.vtt")
                for fragment_caption in webvtt.read(fragment_vtt):
                    fragment_start = new_start + time.str_to_timedelta(
                        f"{fragment_caption.start}000"
                    )
                    fragment_end = new_start + time.str_to_timedelta(
                        f"{fragment_caption.end}000"
                    )
                    fragment_caption.start = time.timedelta_to_str(fragment_start)
                    fragment_caption.end = time.timedelta_to_str(fragment_end)
                    new_vtt.captions.append(fragment_caption)
                os.remove(fragment_audio_path)
                os.remove(fragment_vtt)
                changed = True
            else:
                for last_caption in last_captions:
                    new_vtt.captions.append(last_caption)
            last_captions = []
            last_unique_id = i
            last_unique_caption = caption
        last_captions.append(caption)
        i += 1
    if changed:
        for last_caption in last_captions:
            new_vtt.captions.append(last_caption)
        new_vtt.save(os.path.join(vtt_root, file))
        with open(os.path.join(vtt_root, file), "r", encoding="utf-8") as f:
            content = f.read()
        content += "\n\n"
        with open(os.path.join(vtt_root, file), "w", encoding="utf-8") as f:
            f.write(content)
    return changed
