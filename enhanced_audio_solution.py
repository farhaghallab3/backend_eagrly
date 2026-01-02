#!/usr/bin/env python3
"""
Enhanced Chatbot Audio Solution with FFmpeg Conversion
This script provides the complete implementation for converting audio to WAV before Whisper processing.
"""

def get_enhanced_audio_processing_code():
    """
    Returns the enhanced audio processing code with FFmpeg conversion
    """
    return '''
            if audio_file:
                print("DEBUG: Processing audio file")
                try:
                    # Save temporary file for Whisper
                    import tempfile
                    from django.core.files.storage import default_storage
                    from django.core.files.base import ContentFile
                    import subprocess
                    
                    # Create a temp file path
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
                        for chunk in audio_file.chunks():
                            temp_audio.write(chunk)
                        temp_audio_path = temp_audio.name

                    # Convert to WAV format for better Whisper compatibility
                    # Create temp WAV file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
                        wav_audio_path = temp_wav.name

                    # Use ffmpeg to convert WebM to WAV
                    conversion_cmd = [
                        'ffmpeg', '-i', temp_audio_path, '-ar', '16000', 
                        '-ac', '1', '-f', 'wav', wav_audio_path, '-y'  # -y to overwrite
                    ]
                    
                    try:
                        result = subprocess.run(conversion_cmd, capture_output=True, text=True, check=True)
                        print("DEBUG: Successfully converted audio to WAV format")
                        audio_to_process = wav_audio_path
                    except subprocess.CalledProcessError as e:
                        print(f"ERROR: ffmpeg conversion failed: {e}")
                        print(f"stdout: {e.stdout}")
                        print(f"stderr: {e.stderr}")
                        # Fallback: use original file if conversion fails
                        print("DEBUG: Falling back to original audio format")
                        audio_to_process = temp_audio_path
                    except FileNotFoundError:
                        print("WARNING: ffmpeg not found. Please install ffmpeg for better audio processing.")
                        print("Using original audio format as fallback.")
                        # Fallback: use original file if ffmpeg not available
                        audio_to_process = temp_audio_path

                    # Transcribe using Whisper with converted audio
                    with open(audio_to_process, "rb") as audio:
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1", 
                            file=audio
                        )
                    
                    user_message = transcription.text
                    print(f"DEBUG: Transcribed audio to: '{user_message}'")
                    
                    # Clean up temp files
                    os.remove(temp_audio_path)
                    if audio_to_process != temp_audio_path:
                        try:
                            os.remove(audio_to_process)
                        except:
                            pass  # File might already be cleaned up
                    
                except Exception as e:
                    print(f"Error processing audio: {e}")
                    return Response({"error": "Failed to process audio recording"}, status=status.HTTP_400_BAD_REQUEST)
'''

def create_installation_guide():
    """
    Creates installation guide for ffmpeg
    """
    return """
# FFmpeg Installation Guide

## Windows
1. Download FFmpeg from: https://ffmpeg.org/download.html#build-windows
2. Extract the downloaded zip file
3. Add FFmpeg to your system PATH:
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Under "System Variables", find "Path" and click "Edit"
   - Add the FFmpeg bin directory (e.g., C:\\ffmpeg\\bin)
   - Click OK to save changes

## Verification
After installation, open command prompt and run:
```
ffmpeg -version
```

You should see FFmpeg version information if installed correctly.

## Docker (if using containerized deployment)
Add to your Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y ffmpeg
```
"""

if __name__ == "__main__":
    print("=== Enhanced Chatbot Audio Solution ===")
    print("\n1. FFmpeg Installation Required")
    print(create_installation_guide())
    
    print("\n2. Enhanced Audio Processing Code:")
    print(get_enhanced_audio_processing_code())
