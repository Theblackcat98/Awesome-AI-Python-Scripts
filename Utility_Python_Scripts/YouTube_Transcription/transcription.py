import os
import subprocess
import yt_dlp
import re
import glob
import json
import torch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_optimal_device():
    """Determines the optimal device for PyTorch based on availability."""
    if torch.backends.mps.is_available():
        logging.info("Apple Silicon (MPS) detected. Using MPS.")
        return "mps"
    # ROCm check assumes that if CUDA is available, it might be a ROCm environment on AMD
    if torch.cuda.is_available():
        # Crude check for ROCm: torch.version.hip exists in ROCm builds
        # This check is wrapped to avoid static analysis errors with Pylance
        version_module = getattr(torch, 'version', None)
        if version_module and hasattr(version_module, 'hip') and version_module.hip:
            logging.info("ROCm (AMD GPU) detected. Using ROCm.")
            return "rocm"
        else:
            logging.info("CUDA (Nvidia GPU) detected. Using CUDA.")
            return "cuda"
    logging.info("No compatible GPU detected. Falling back to CPU.")
    return "cpu"

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_youtube_audio(url, output_folder):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info:
            title = sanitize_filename(info.get('title', 'default_title'))
            return find_audio_file(output_folder, title)
        return None

def find_audio_file(folder, title):
    pattern = os.path.join(folder, f"{title}.*")
    files = glob.glob(pattern)
    return files[0] if files else None

def transcribe_audio(audio_file):
    device = get_optimal_device()

    command = [
        "insanely-fast-whisper",
        "--file-name", audio_file,
        "--device-id", device,
        "--model-name", "openai/whisper-large-v3",
        "--batch-size", "4",
        "--timestamp", "word"
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        logging.error("Error during transcription:")
        logging.error(result.stderr)
        return None

    try:
        # Try parsing the output as JSON
        transcription_data = json.loads(result.stdout)
        transcription_text = transcription_data.get("text", "")
    except json.JSONDecodeError:
        # Fallback to manual parsing if JSON fails
        logging.warning("Failed to parse transcription output as JSON. Falling back to line-based parsing.")
        output_lines = result.stdout.strip().split('\n')
        # A simple heuristic to find the start of the actual transcription
        transcription_text = ' '.join(line for line in output_lines if not line.startswith('[') and not line.endswith(']'))

    return {
        'text': transcription_text,
        'raw_output': result.stdout
    }


def main():
    choice = input("Enter '1' for YouTube URL or '2' for local audio file path: ")
    
    if choice == '1':
        youtube_url = input("Enter the YouTube URL: ")
        audio_folder = "youtube_audio"
        os.makedirs(audio_folder, exist_ok=True)
        print("Downloading and converting YouTube video...")
        audio_file = download_youtube_audio(youtube_url, audio_folder)
    elif choice == '2':
        audio_file = input("Enter the path to the local audio file: ")
    else:
        print("Invalid choice. Exiting.")
        return

    if audio_file is None:
        print("Error: Could not find the audio file.")
        return

    transcript_folder = "youtube_transcript"
    os.makedirs(transcript_folder, exist_ok=True)
    
    print(f"Audio file to be transcribed: {os.path.abspath(audio_file)}")
    
    if not os.path.exists(audio_file):
        print(f"Error: The audio file '{audio_file}' does not exist.")
        return
    
    print("Transcribing audio...")
    transcription = transcribe_audio(audio_file)

    if transcription is None:
        print("Transcription failed.")
        return

    print("Transcription complete. Results:")
    if isinstance(transcription, dict) and 'text' in transcription:
        print(transcription['text'])
        
        video_name = os.path.splitext(os.path.basename(audio_file))[0]
        transcript_file = os.path.join(transcript_folder, f"{video_name}.txt")
        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(transcription['text'])
        print(f"Transcription saved to {transcript_file}")
        
        # Save the raw output
        raw_output_file = os.path.join(transcript_folder, f"{video_name}_raw_output.txt")
        with open(raw_output_file, "w", encoding="utf-8") as f:
            f.write(transcription['raw_output'])
        print(f"Raw transcription output saved to {raw_output_file}")
    else:
        print("Unexpected transcription format:")
        print(transcription)

if __name__ == "__main__":
    main()