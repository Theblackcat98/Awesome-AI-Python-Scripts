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
    # For both CUDA and ROCm, PyTorch uses torch.cuda.is_available()
    if torch.cuda.is_available():
        # The device name for whisper is 'cuda' for both NVIDIA and AMD GPUs (with ROCm)
        version_module = getattr(torch, 'version', None)
        if version_module and hasattr(version_module, 'hip') and version_module.hip:
            logging.info("ROCm (AMD GPU) detected. Passing 'cuda' to whisper.")
        else:
            logging.info("NVIDIA GPU detected. Passing 'cuda' to whisper.")
        return "cuda"
    if torch.backends.mps.is_available():
        logging.info("Apple Silicon (MPS) detected. Using MPS.")
        return "mps"
    logging.info("No compatible GPU detected. Falling back to CPU.")
    return "cpu"

def download_youtube_audio(url, output_folder):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        'restrictfilenames': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # The prepare_filename method might return a filename with the original extension,
        # not the one from the post-processor.
        if info:
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            return base + '.' + ydl_opts['postprocessors'][0]['preferredcodec']
        return None

def transcribe_audio(audio_file):
    device = get_optimal_device()

    command = [
        "whisper",
        audio_file,
        "--device", device,
        "--model", "turbo",
        "--language", "en",
        "--task", "transcribe",
        "--output_format", "txt",
        "--word_timestamps", "True"
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

    if not audio_file or not os.path.exists(audio_file):
        print("Error: Could not find the audio file or file does not exist.")
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