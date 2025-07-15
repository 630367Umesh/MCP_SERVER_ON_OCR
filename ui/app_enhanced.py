# ui/app_enhanced.py

import streamlit as st
import requests
import base64
from PIL import Image
import io
import fitz  # PyMuPDF
import os
import json
import zipfile
from datetime import datetime
import pandas as pd

# === Background Styling ===
st.markdown(
    """
    <style>
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=1050&q=80');
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# === Helper Functions (moved up) ===
def create_dataset_zip():
    """Create a zip file of all files in training_dataset and return as BytesIO."""
    dataset_dir = "training_dataset"
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for filename in os.listdir(dataset_dir):
            file_path = os.path.join(dataset_dir, filename)
            if os.path.isfile(file_path):
                zipf.write(file_path, arcname=filename)
    zip_buffer.seek(0)
    return zip_buffer

def create_dataset_csv(dataset_info):
    """Create a CSV file with dataset information"""
    try:
        df = pd.DataFrame(dataset_info)
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📊 Download Dataset Info (CSV)",
            data=csv_data,
            file_name=f"dataset_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"❌ Error creating CSV file: {e}")

def execute_tool(tool, uploaded_file, file_bytes, file_type, img_base64, expected, engine, server_url):
    """Execute the selected OCR tool"""
    try:
        if tool == "extract":
            response = requests.post(f"{server_url}/tools/extract", data={
                "image_base64": img_base64,
                "engine": engine
            })
        elif tool == "summarise":
            files = {"uploaded_file": (uploaded_file.name, file_bytes, file_type)}
            response = requests.post(f"{server_url}/tools/summarise", files=files, data={"engine": engine})
        elif tool == "test":
            files = {"uploaded_file": (uploaded_file.name, file_bytes, file_type)}
            response = requests.post(f"{server_url}/tools/test", files=files, data={"expected": expected, "engine": engine})
        elif tool == "train":
            files = {"uploaded_file": (uploaded_file.name, file_bytes, file_type)}
            response = requests.post(f"{server_url}/tools/train", files=files, data={"expected": expected, "engine": engine})
        
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def create_download_button(content, filename, button_text):
    """Create a download button for text content"""
    st.download_button(
        label=button_text,
        data=content,
        file_name=filename,
        mime="text/plain"
    )

def display_training_dataset():
    """Display training dataset information and management options"""
    if not os.path.exists("training_dataset"):
        st.info("No training dataset found")
        return
    
    files = os.listdir("training_dataset")
    image_files = [f for f in files if f.endswith(('.png', '.jpg', '.jpeg', '.pdf'))]
    label_files = [f for f in files if f.endswith('.txt')]
    
    # Dataset statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📄 Total Images", len(image_files))
    with col2:
        st.metric("📝 Total Labels", len(label_files))
    with col3:
        st.metric("🔧 Tesseract Samples", len([f for f in image_files if f.startswith('tesseract')]))
    with col4:
        st.metric("🤖 Nougat Samples", len([f for f in image_files if f.startswith('nougat')]))
    
    # Dataset table
    if image_files:
        st.subheader("📋 Dataset Contents")
        
        # Create dataset info
        dataset_info = []
        for img_file in image_files:
            base_name = img_file.rsplit('.', 1)[0]
            label_file = f"{base_name}.txt"
            label_path = os.path.join("training_dataset", label_file)
            
            if os.path.exists(label_path):
                with open(label_path, 'r', encoding='utf-8') as f:
                    label_text = f.read().strip()
            else:
                label_text = "No label found"
            
            engine = "tesseract" if img_file.startswith("tesseract") else "nougat"
            file_size = os.path.getsize(os.path.join("training_dataset", img_file)) / 1024
            
            dataset_info.append({
                "Image": img_file,
                "Engine": engine,
                "Size (KB)": f"{file_size:.1f}",
                "Label Preview": label_text[:50] + "..." if len(label_text) > 50 else label_text
            })
        
        df = pd.DataFrame(dataset_info)
        st.dataframe(df, use_container_width=True)
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download Dataset (ZIP)"):
                create_dataset_zip()
        with col2:
            if st.button("📊 Export Dataset Info (CSV)"):
                create_dataset_csv(dataset_info)

# --- Page Config ---
st.set_page_config(
    page_title="OCR AI Tool - Enhanced", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Sidebar Configuration ===
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # OCR Engine Selection
    engine = st.selectbox(
        "🔧 OCR Engine", 
        ["tesseract", "nougat"],
        help="Choose the OCR engine for text extraction"
    )
    
    # Server Configuration
    st.subheader("🌐 Server Settings")
    server_url = st.text_input(
        "Server URL", 
        value="http://localhost:8000",
        help="URL of the OCR MCP server"
    )
    
    # Advanced Settings
    with st.expander("🔧 Advanced Settings"):
        st.checkbox("Show debug info", value=False, key="debug_mode")
        st.checkbox("Auto-download results", value=True, key="auto_download")
        
    # Training Dataset Info
    st.subheader("📊 Training Dataset")
    if os.path.exists("training_dataset"):
        files = os.listdir("training_dataset")
        image_files = [f for f in files if f.endswith((".png", ".jpg", ".jpeg", ".pdf"))]
        label_files = [f for f in files if f.endswith('.txt')]
        
        st.metric("📄 Images", len(image_files))
        st.metric("📝 Labels", len(label_files))
        
        if len(files) > 0:
            zip_buffer = create_dataset_zip()
            st.download_button(
                label="⬇️ Download All as ZIP",
                data=zip_buffer,
                file_name="training_dataset.zip",
                mime="application/zip"
            )
    else:
        st.info("No training dataset found")

# === Main Content ===
st.markdown("<div class='main-box'>", unsafe_allow_html=True)

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🤖 OCR AI Tool - Enhanced")
    st.markdown("**Advanced OCR with AI-powered features**")

# Tool Selection
option = st.selectbox(
    "🎯 Choose OCR Tool", 
    ["extract", "summarise", "test", "train", "dataset"],
    help="Select the OCR operation you want to perform"
)

# === File Upload Section ===
if option != "dataset":
    uploaded_file = st.file_uploader(
        "📁 Upload Image or PDF", 
        type=["png", "jpg", "jpeg", "pdf"],
        help="Upload an image or PDF file for OCR processing"
    )

    if uploaded_file:
        st.session_state.uploaded_filename = uploaded_file.name
        file_bytes = uploaded_file.read()
        file_type = uploaded_file.type

        # Display uploaded file info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 File Type", file_type)
        with col2:
            st.metric("📏 File Size", f"{len(file_bytes) / 1024:.1f} KB")
        with col3:
            st.metric("🔧 Engine", engine)

        # Convert PDF to image if needed
        if file_type == "application/pdf":
            st.info("📄 PDF uploaded. Converting first page to image...")
            try:
                pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
                try:
                    page = pdf_doc.load_page(0)
                    pix = page.get_pixmap(dpi=300)  # type: ignore
                except AttributeError:
                    page = pdf_doc[0]
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

        # Display image
        st.image(image, caption=f"Uploaded: {uploaded_file.name}", use_container_width=True)

        # Encode image to base64
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # === Tool-specific Inputs ===
        if option in ["test", "train"]:
            expected = st.text_area(
                "✍️ Expected Text (Ground Truth)", 
                placeholder="Enter the expected text for comparison or training...",
                help="For test: text to compare against OCR output\nFor train: correct text for training data"
            )

        # === Execute Tool ===
        if st.button(f"🚀 Run {option.title()} Tool", type="primary"):
            with st.spinner(f"⏳ Processing with {engine}..."):
                try:
                    result = execute_tool(option, uploaded_file, file_bytes, file_type, img_base64, expected if option in ["test", "train"] else None, engine, server_url)
                    
                    if result and "result" in result:
                        st.success("✅ Processing Complete!")
                        
                        # Display result
                        with st.expander("📋 View Result", expanded=True):
                            st.code(result["result"])
                        
                        # Download buttons based on tool
                        if option == "extract":
                            create_download_button(result["result"], "extracted_text.txt", "📥 Download Extracted Text")
                        elif option == "summarise":
                            create_download_button(result["result"], "summary.txt", "📥 Download Summary")
                        elif option == "test":
                            create_download_button(result["result"], "test_result.txt", "📥 Download Test Result")
                        elif option == "train":
                            st.success("🎓 Training sample saved to dataset!")
                            if st.button("📊 View Dataset"):
                                display_training_dataset()
                    else:
                        st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"❌ Error communicating with server: {e}")

# === Dataset Management ===
elif option == "dataset":
    st.subheader("📊 Training Dataset Management")
    
    if os.path.exists("training_dataset"):
        display_training_dataset()
    else:
        st.info("No training dataset found. Use the train tool to create samples.")

st.markdown("</div>", unsafe_allow_html=True)

# === Footer ===
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🤖 OCR AI Tool - Enhanced | Powered by FastAPI & Streamlit</p>
        <p>Support for Tesseract & Nougat OCR engines</p>
    </div>
    """,
    unsafe_allow_html=True
) 