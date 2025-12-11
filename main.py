import subprocess
import os
import sys
import gradio as gr
import requests
import json

OLLAMA_SERVER_URL = "http://localhost:11434"

def get_available_models() -> list[str]:
    try:
        response = requests.get(f"{OLLAMA_SERVER_URL}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["model"] for model in models]
        return ["Error: Check Ollama Server"]
    except:
        return ["Error: Ollama not running"]

def summarize_with_model(llm_model_name, context, text):
    prompt = f"Context: {context}\n\nTranscript:\n{text}\n\nSummarize this meeting, highlighting key decisions and action items by speaker."
    data = {"model": llm_model_name, "prompt": prompt, "stream": False}
    try:
        resp = requests.post(f"{OLLAMA_SERVER_URL}/api/generate", json=data)
        if resp.status_code == 200:
            return resp.json().get("response", "No response generated.")
        else:
            return f"Ollama Error: {resp.text}"
    except Exception as e:
        return f"Summarization Error: {str(e)}"

def translate_and_summarize(audio_file_path, context, whisper_model, llm_model):
    if not audio_file_path: 
        return "Please upload a file", None
    
    diarize_script = os.path.join("whisper-diarization", "diarize.py")
    if not os.path.exists(diarize_script):
        return "CRITICAL ERROR: 'whisper-diarization' folder not found!", None

    print(f"🚀 Starting Diarization on {audio_file_path}...")
    
    # COMMAND: Using --no-stem to prevent crashes
    cmd = [
        sys.executable, 
        diarize_script, 
        "-a", audio_file_path, 
        "--batch-size", "0", 
        "--device", "cpu",
        "--no-stem"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        return f"Diarization Failed. Error Code: {e.returncode}\nCheck terminal for details.", None

    base_name = os.path.splitext(audio_file_path)[0]
    output_file = f"{base_name}.txt"
    
    if not os.path.exists(output_file):
        output_file = f"{base_name}.srt"
    
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            transcript = f.read()
        
        print("✅ Diarization Complete. Summarizing...")
        summary = summarize_with_model(llm_model, context, transcript)
        return summary, output_file
    else:
        return "Error: Transcript file was not created.", None

def gradio_app(audio, context, whisper_model, llm_model):
    return translate_and_summarize(audio, context, whisper_model, llm_model)

if __name__ == "__main__":
    iface = gr.Interface(
        fn=gradio_app,
        inputs=[
            gr.Audio(type="filepath", label="Upload Meeting Audio"),
            gr.Textbox(label="Context"),
            gr.Dropdown(choices=["medium.en"], label="Whisper Model", value="medium.en"),
            gr.Dropdown(choices=get_available_models(), label="Ollama Model", value="llama3.2:latest")
        ],
        outputs=[
            gr.Textbox(label="Summary"),
            gr.File(label="Speaker Transcript")
        ],
        title="AI Meeting Summarizer (Speaker Aware)",
        description="Upload audio. PLEASE WAIT 1-2 MINUTES for processing."
    )
    iface.launch(server_name="0.0.0.0", share=False)
