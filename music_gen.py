import os, json, shutil, random, subprocess, time, threading
from music21 import stream, chord, note, instrument, tempo, metadata, midi

def gm_instrument(program):
    inst = instrument.Instrument()
    inst.midiProgram = program
    return inst


# --- Paths ---
CONFIG_PATH = "config.json"
OUTPUT_PATH = "output"
# FFMPEG_PATH = os.path.join("ffmpeg", "bin", "ffmpeg.exe")
# FLUIDSYNTH_PATH = os.path.join("fluidsynth", "bin", "fluidsynth.exe")
FFMPEG_PATH = "ffmpeg"
FLUIDSYNTH_PATH = "fluidsynth"
SOUNDFONT_PATH = os.path.join("FluidR3_GM", "FluidR3_GM.sf2")
#BGM_PATH = os.path.join("assets", "bgm.mp3")

# --- Section Lengths ---
SECTION_LENGTHS = {
    "intro": 4, "groove": 8, "verse": 8, "chorus": 8, "bridge": 8,
    "drop": 8, "build": 8, "solo": 8, "outro": 4, "loop": 16,
    "variation": 8, "layered_loop": 8, "fadeout": 4, "layer1": 8,
    "layer2": 8, "ambient_loop": 16, "dream_flow": 8, "infinite_loop": 16,
    "loop_a": 8, "focus_block": 8, "pause_fill": 4, "soothing_loop": 16,
    "deep_layer": 8, "dream_pad": 8
}

# --- Instrument Mapping ---
INSTRUMENT_MAP = {
    "Charango": gm_instrument(24),         # Nylon Guitar (closest)
    "Reeds": gm_instrument(68),            # Oboe / Reed
    "Harp": gm_instrument(46),             # Harp
    "Piano": gm_instrument(0),             # Acoustic Grand Piano
    "Electric Piano": gm_instrument(4),    # Electric Piano 1
    "Synth Lead": gm_instrument(80),       # Lead 1 (Square)
    "Bass Guitar": gm_instrument(33),      # Electric Bass Finger
    "Drum Kit": gm_instrument(118),        # Woodblock (percussion)
    "Arpeggiator": gm_instrument(6),       # Harpsichord
    "Acoustic Guitar": gm_instrument(24),  # Nylon Guitar
    "Soft Strings": gm_instrument(48),     # String Ensemble 1
    "Felt Piano": gm_instrument(0),        # Acoustic Grand Piano
    "Air Pad": gm_instrument(89),          # Warm Pad
    "Sub Bass": gm_instrument(32),         # Acoustic Bass
    "Flute": gm_instrument(73),            # Flute
    "Chill Guitar": gm_instrument(24),     # Nylon Guitar
    "Electric Guitar": gm_instrument(27)   # Electric Guitar (clean)
}

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def get_instrument(name):
    return INSTRUMENT_MAP.get(name, instrument.Instrument(name))

def convert_midi_to_mp3(midi_path):
    wav = midi_path.replace(".mid", ".wav")
    mp3 = midi_path.replace(".mid", ".mp3")
    mixed = midi_path.replace(".mid", "_mixed.mp3")

    try:
        subprocess.run([FLUIDSYNTH_PATH, "-ni", "-F", wav, "-r", "44100", SOUNDFONT_PATH, midi_path], check=True)
        subprocess.run([FFMPEG_PATH, "-y", "-i", wav, mp3], check=True)

        result = subprocess.run(
            [FFMPEG_PATH, "-i", mp3, "-f", "null", "-"],
            stderr=subprocess.PIPE,
            text=True
        )

        duration = None
        for line in result.stderr.splitlines():
            if "Duration" in line:
                time_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = map(float, time_str.replace(":", " ").split())
                duration = h * 3600 + m * 60 + s
                break

        if not duration:
            raise Exception("Could not extract MP3 duration.")

        subprocess.run([FFMPEG_PATH, "-y", "-i", wav, mp3], check=True)
        shutil.move(mp3, mixed)

        '''subprocess.run([
            FFMPEG_PATH, "-y",
            "-t", str(duration),
            "-i", mp3,
            "-t", str(duration),
            "-i", BGM_PATH,
            "-filter_complex", "[0:a]volume=0.3[a0];[1:a]volume=0.5[a1];[a0][a1]amix=inputs=2:duration=shortest",
            "-c:a", "libmp3lame",
            mixed
        ], check=True)'''

    finally:
        for f in [wav, mp3]:
            if os.path.exists(f):
                os.remove(f)

    return mixed

def create_melody_part(mode, structure):
    melody = stream.Part()
    melody.insert(0, gm_instrument(0))  # Acoustic Grand Piano
    scale_map = {
        "focus": ["C5", "D5", "E5", "G5", "A5"],
        "relax": ["C4", "D4", "E4", "G4", "A4"],
        "sleep": ["A3", "C4", "D4", "E4"]
    }
    scale = scale_map.get(mode, ["C4", "D4", "E4", "G4"])

    for section in structure:
        total_beats = SECTION_LENGTHS.get(section, 8) * 4
        beats = 0

        while beats < total_beats:
            n = note.Note(random.choice(scale))
            n.quarterLength = random.choice([2, 4])  # long breath notes
            n.volume.velocity = random.randint(25, 45)
            melody.append(n)
            melody.append(note.Rest(quarterLength=1))  # silence = meditation
            beats += n.quarterLength + 1

    return melody

def create_drone_part(mode, structure):
    drone = stream.Part()
    drone.insert(0, gm_instrument(48))  # Soft Strings / String Ensemble 1

    base_note = {
        "focus": "C3",
        "relax": "A2",
        "sleep": "D2"
    }.get(mode, "C2")

    for section in structure:
        length = SECTION_LENGTHS.get(section, 8) * 4
        n = note.Note(base_note, quarterLength=length)
        n.volume.velocity = 20
        drone.append(n)

    return drone

def generate_music(mode):
    config = load_config()
    data = config.get(mode)
    if not data:
        raise ValueError(f"Invalid mode: {mode}")

    bpm = data.get("tempo", 80)
    instruments = data.get("instruments", [])
    structure = data.get("structure", ["intro", "loop", "outro"])

    shutil.rmtree(OUTPUT_PATH, ignore_errors=True)
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    score = stream.Score()
    score.append(tempo.MetronomeMark(number=bpm + random.choice([-2, 0, 1])))
    score.insert(0, metadata.Metadata(title=f"Xenotune - {mode.title()}"))

    progression_map = {
        "focus": [["C4", "E4", "G4"], ["D4", "F4", "A4"], ["G3", "B3", "D4"]],
        "relax": [["C4", "G4", "A4"], ["E4", "G4", "B4"], ["D4", "F4", "A4"]],
        "sleep": [["C3", "E3", "G3"], ["A3", "C4", "E4"], ["F3", "A3", "C4"]]
    }
    progression = progression_map.get(mode, [["C4", "E4", "G4"]])

    for inst in instruments:
        if "samples" in inst:
            continue
        part = stream.Part()
        part.insert(0, get_instrument(inst.get("name", "Piano")))
        style = inst.get("style", "")
        notes = inst.get("notes", random.choice(progression))
        vel_range = (18, 40) if "ambient" in style else (30, 70)

        for section in structure:
            beats = 0
            total_beats = SECTION_LENGTHS.get(section, 8) * 4
            while beats < total_beats:
                vel = random.randint(*vel_range)
                if "arp" in style:
                    for n in notes:
                        nt = note.Note(n, quarterLength=0.5)
                        nt.volume.velocity = vel
                        part.append(nt)
                        beats += 0.5
                        if beats >= total_beats:
                            break
                    continue
                length = random.choice([4, 6, 8])  # deep sustain
                c = chord.Chord(random.choice(progression), quarterLength=length)
                c.volume.velocity = vel
                part.append(c)
                beats += length
        score.append(part)

    score.append(create_drone_part(mode, structure))
    score.append(create_melody_part(mode, structure))

    midi_path = os.path.join(OUTPUT_PATH, f"{mode}.mid")
    mf = midi.translate.streamToMidiFile(score)
    mf.open(midi_path, 'wb')
    mf.write()
    mf.close()

    return convert_midi_to_mp3(midi_path)
