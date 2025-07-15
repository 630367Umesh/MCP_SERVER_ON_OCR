# ui/app.py

import streamlit as st
import requests
import base64
from PIL import Image
import io
import fitz  # PyMuPDF
from fitz import Page  # type: ignore
import json
from datetime import datetime
import os

# --- Page Config ---
st.set_page_config(page_title="OCR Utility - Streamlit UI", layout="centered")

# === Background Styling ===
def set_bg():
    image_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1050&q=80"  # Modern, nature-themed Unsplash image
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url('{image_url}');
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .main-box {{
            background-color: rgba(255, 255, 255, 0.90);
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0px 0px 25px rgba(0,0,0,0.3);
        }}
        .result-box {{
            background-color: rgba(240, 248, 255, 0.95);
            padding: 1rem;
            border-radius: 0.5rem;
            border-left: 4px solid #4CAF50;
            margin: 0.5rem 0;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg()

# === Helper Functions ===
def create_download_data(results_dict, filename):
    """Create downloadable data from results"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "results": results_dict
    }
    return json.dumps(data, indent=2)

def run_all_tools(img_base64, file_bytes, file_type, uploaded_file_name, engine, expected_text=""):
    """Run all OCR tools sequentially"""
    results = {}
    
    # Progress bar for all tools
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Tool 1: Extract
        status_text.text("🔍 Running Text Extraction...")
        response = requests.post("http://localhost:8001/tools/extract", data={
            "image_base64": img_base64,
            "engine": engine
        })
        results["extract"] = response.json().get("result", "Failed")
        progress_bar.progress(25)
        
        # Tool 2: Summarise
        status_text.text("📝 Running Summarization...")
        files = {"uploaded_file": (uploaded_file_name, file_bytes, file_type)}
        response = requests.post(
            "http://localhost:8001/tools/summarise",
            files=files,
            data={"engine": engine}
        )
        results["summarise"] = response.json().get("result", "Failed")
        progress_bar.progress(50)
        
        # Tool 3: Test (if expected text provided)
        if expected_text.strip():
            status_text.text("✅ Running Accuracy Test...")
            response = requests.post(
                "http://localhost:8001/tools/test",
                files=files,
                data={"expected": expected_text, "engine": engine}
            )
            results["test"] = response.json().get("result", "Failed")
            progress_bar.progress(75)
            
            # Tool 4: Train
            status_text.text("🎓 Saving Training Data...")
            response = requests.post(
                "http://localhost:8001/tools/train",
                files=files,
                data={"expected": expected_text, "engine": engine}
            )
            results["train"] = response.json().get("result", "Failed")
        else:
            results["test"] = "Skipped - No expected text provided"
            results["train"] = "Skipped - No expected text provided"
        
        progress_bar.progress(100)
        status_text.text("🎉 All tools completed successfully!")
        
    except Exception as e:
        st.error(f"❌ Error running tools: {e}")
        results["error"] = str(e)
    
    return results

# === Main Layout ===
st.markdown("<div class='main-box'>", unsafe_allow_html=True)
st.title("📄 OCR Utility - Streamlit UI")
st.markdown("### 🔄 **Auto-Run All Tools** - Complete OCR Pipeline")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    engine = st.selectbox("OCR Engine", ["tesseract", "nougat", "mistral"])
    auto_run = st.checkbox("🔄 Auto-run all tools", value=True, help="Automatically run all tools when file is uploaded")
    st.markdown("---")
    st.markdown("**Available Tools:**")
    st.markdown("• 🔍 **Extract**: Text extraction")
    st.markdown("• 📝 **Summarise**: AI-powered summarization")
    st.markdown("• 🌐 **Translate**: Translate extracted text to another language")

# Language options for translation
LANGUAGES = [
    ("French", "fr"), ("English", "en"), ("Spanish", "es"), ("German", "de"), ("Italian", "it"),
    ("Portuguese", "pt"), ("Russian", "ru"), ("Chinese (Simplified)", "zh"), ("Japanese", "ja"),
    ("Korean", "ko"), ("Arabic", "ar"), ("Hindi", "hi"), ("Bengali", "bn"), ("Urdu", "ur"),
    ("Turkish", "tr"), ("Vietnamese", "vi"), ("Polish", "pl"), ("Dutch", "nl"), ("Greek", "el"),
    ("Czech", "cs"), ("Swedish", "sv"), ("Finnish", "fi"), ("Danish", "da"), ("Norwegian", "no"),
    ("Hungarian", "hu"), ("Romanian", "ro"), ("Thai", "th"), ("Indonesian", "id"), ("Malay", "ms"),
    ("Hebrew", "he"), ("Ukrainian", "uk"), ("Persian", "fa"), ("Swahili", "sw"), ("Filipino", "tl"),
    ("Serbian", "sr"), ("Croatian", "hr"), ("Slovak", "sk"), ("Bulgarian", "bg"), ("Lithuanian", "lt"),
    ("Latvian", "lv"), ("Estonian", "et"), ("Slovenian", "sl"), ("Macedonian", "mk"), ("Albanian", "sq"),
    ("Georgian", "ka"), ("Armenian", "hy"), ("Azerbaijani", "az"), ("Kazakh", "kk"), ("Uzbek", "uz"),
    ("Mongolian", "mn"), ("Nepali", "ne"), ("Sinhala", "si"), ("Burmese", "my"), ("Khmer", "km"),
    ("Lao", "lo"), ("Malayalam", "ml"), ("Tamil", "ta"), ("Telugu", "te"), ("Kannada", "kn"),
    ("Marathi", "mr"), ("Gujarati", "gu"), ("Punjabi", "pa"), ("Odia", "or"), ("Maithili", "mai"),
    ("Santali", "sat"), ("Kurdish", "ku"), ("Pashto", "ps"), ("Somali", "so"), ("Afrikaans", "af"),
    ("Zulu", "zu"), ("Xhosa", "xh"), ("Yoruba", "yo"), ("Igbo", "ig"), ("Hausa", "ha"), ("Amharic", "am")
]
LANGUAGE_NAMES = [f"{name} ({code})" for name, code in LANGUAGES]
LANGUAGE_CODE_MAP = {f"{name} ({code})": code for name, code in LANGUAGES}

# Main content
uploaded_file = st.file_uploader("📁 Upload Image or PDF", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file:
    st.session_state.uploaded_filename = uploaded_file.name
    file_bytes = uploaded_file.read()
    file_type = uploaded_file.type

    # Convert PDF to image if needed
    if file_type == "application/pdf":
        st.info("📄 PDF uploaded. Converting first page to image...")
        try:
            pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
            page = pdf_doc.load_page(0)
            # Use type: ignore to suppress linter error for get_pixmap/getPixmap
            try:
                pix = page.get_pixmap(dpi=300)  # type: ignore
            except AttributeError:
                pix = page.getPixmap(dpi=300)  # type: ignore
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        except Exception as e:
            st.error(f"❌ PDF conversion failed: {e}")
            st.stop()
    else:
        try:
            image = Image.open(io.BytesIO(file_bytes))
        except Exception as e:
            st.error(f"❌ Image load failed: {e}")
            st.stop()

    # Display uploaded image
    col1, col2 = st.columns([2, 1])
    with col1:
        st.image(image, caption="Uploaded Document", use_container_width=True)
    with col2:
        st.markdown(f"**File:** {uploaded_file.name}")
        st.markdown(f"**Size:** {len(file_bytes):,} bytes")
        st.markdown(f"**Engine:** {engine}")

    # Encode image to base64
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Expected text input (for test and train)
    expected_text = st.text_area("✍️ Expected Text (for accuracy testing & training)", 
                                placeholder="Enter the expected text from this document...",
                                help="Leave empty to skip test and train tools")

    # Auto-run or manual run
    if auto_run:
        st.markdown("---")
        st.markdown("### 🚀 **Auto-Running All Tools**")
        
        # Run extract and summarise always
        results = {}
        results.update(run_all_tools(img_base64, file_bytes, file_type, uploaded_file.name, engine, expected_text=""))

        # Language selection for auto-run
        st.markdown("---")
        selected_lang_display = st.selectbox("🌐 Select Translation Language", LANGUAGE_NAMES, index=0, key="auto_lang")
        selected_lang_code = LANGUAGE_CODE_MAP[selected_lang_display]
        # Run translate tool
        files = {"uploaded_file": (uploaded_file.name, file_bytes, file_type)}
        response = requests.post(
            "http://localhost:8001/tools/translate",
            files=files,
            data={"target_language": selected_lang_display, "engine": engine}
        )
        results["translate"] = response.json().get("result", "Failed")
        
        # Display results
        st.markdown("---")
        st.markdown("### 📊 **Results**")
        
        # Extract results
        with st.expander("🔍 **Text Extraction Results**", expanded=True):
            st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            st.text_area("Extracted Text", results.get("extract", "No result"), height=200)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Summarize results
        with st.expander("📝 **Summarization Results**", expanded=True):
            st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            st.text_area("Summary", results.get("summarise", "No result"), height=150)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Translate results
        with st.expander("🌐 **Translation Results**", expanded=True):
            st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            st.text_area("Translated Summary", results.get("translate", "No result"), height=150)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # If expected text is provided, run and show test/train
        if expected_text.strip():
            test_train_results = run_all_tools(img_base64, file_bytes, file_type, uploaded_file.name, engine, expected_text)
            # Test results
            with st.expander("✅ **Accuracy Test Results**", expanded=True):
                st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                st.text_area("Test Result", test_train_results.get("test", "No result"), height=100)
                st.markdown("</div>", unsafe_allow_html=True)
            # Train results
            with st.expander("🎓 **Training Data Results**", expanded=True):
                st.markdown("<div class='result-box'>", unsafe_allow_html=True)
                st.text_area("Training Result", test_train_results.get("train", "No result"), height=100)
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Download button
        st.markdown("---")
        st.markdown("### 💾 **Download Results**")
        
        # Create downloadable data
        download_data = create_download_data(results, uploaded_file.name)
        
        # Download button
        st.download_button(
            label="📥 Download All Results (JSON)",
            data=download_data,
            file_name=f"ocr_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            help="Download all results as a JSON file"
        )
        
        # Individual downloads
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.download_button(
                label="📄 Extract",
                data=results.get("extract", ""),
                file_name=f"extract_{uploaded_file.name}.txt",
                mime="text/plain"
            )
        with col2:
            st.download_button(
                label="📝 Summary",
                data=results.get("summarise", ""),
                file_name=f"summary_{uploaded_file.name}.txt",
                mime="text/plain"
            )
        if expected_text.strip():
            with col3:
                st.download_button(
                    label="✅ Test",
                    data=test_train_results.get("test", ""),
                    file_name=f"test_{uploaded_file.name}.txt",
                    mime="text/plain"
                )
            with col4:
                st.download_button(
                    label="🎓 Train",
                    data=test_train_results.get("train", ""),
                    file_name=f"train_{uploaded_file.name}.txt",
                    mime="text/plain"
                )
    
    else:
        # Manual run option (original functionality)
        st.markdown("---")
        option = st.selectbox("Choose OCR Tool", ["extract", "summarise", "translate"])
        
        if option == "translate":
            selected_lang_display = st.selectbox("🌐 Select Translation Language", LANGUAGE_NAMES, index=0, key="manual_lang")
            target_language = selected_lang_display
        
        if st.button(f"🔍 Run {option.title()} Tool"):
            with st.spinner("⏳ Contacting OCR MCP server..."):
                try:
                    if option == "extract":
                        response = requests.post("http://localhost:8001/tools/extract", data={
                            "image_base64": img_base64,
                            "engine": engine
                        })

                    elif option == "summarise":
                        files = {"uploaded_file": (uploaded_file.name, file_bytes, file_type)}
                        response = requests.post(
                            "http://localhost:8001/tools/summarise",
                            files=files,
                            data={"engine": engine}
                        )

                    elif option == "translate":
                        files = {"uploaded_file": (uploaded_file.name, file_bytes, file_type)}
                        response = requests.post(
                            "http://localhost:8001/tools/translate",
                            files=files,
                            data={"target_language": target_language, "engine": engine}
                        )

                    result = response.json()
                    if "result" in result:
                        st.success("✅ Response Received")
                        st.code(result["result"])
                        st.download_button(
                            label=f"📥 Download {option.title()} Result",
                            data=result["result"],
                            file_name=f"{option}_{uploaded_file.name}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.warning("⚠️ No output returned.")
                except Exception as e:
                    st.error(f"❌ Error communicating with server: {e}")

# === Download Training Data Section ===
with st.expander("📥 Download Training Data", expanded=False):
    dataset_dir = os.path.join(os.getcwd(), "training_dataset")
    if os.path.exists(dataset_dir):
        files = [f for f in os.listdir(dataset_dir) if os.path.isfile(os.path.join(dataset_dir, f))]
        if files:
            for file in files:
                file_path = os.path.join(dataset_dir, file)
                with open(file_path, "rb") as f:
                    st.download_button(
                        label=f"⬇️ {file}",
                        data=f.read(),
                        file_name=file,
                        mime="application/pdf" if file.lower().endswith(".pdf") else ("text/plain" if file.lower().endswith(".txt") else "application/octet-stream")
                    )
        else:
            st.info("No training data files found.")
    else:
        st.info("training_dataset/ folder does not exist.")

st.markdown("</div>", unsafe_allow_html=True)
