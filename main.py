import os
import getpass
import docx
from docx import Document
from docx.shared import Pt
import requests
from tempfile import NamedTemporaryFile
from docx2pdf import convert

def prompt_file_path(prompt_text):
    path = input(prompt_text)
    while not os.path.isfile(path):
        print(f"File not found: {path}")
        path = input(prompt_text)
    return path

def read_docx_text(docx_path):
    doc = Document(docx_path)
    text = "\n".join([p.text for p in doc.paragraphs])
    return text, doc

def read_txt_file(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_gemini_api_key():
    print("You need a Gemini API key. Get one at https://aistudio.google.com/app/apikey")
    return getpass.getpass("Enter your Gemini API key (input hidden): ")

def call_gemini(api_key, resume_text, job_desc):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + api_key
    prompt = f"""
You are an expert resume writer. Given the following resume and job description, rewrite the resume to best match the job description, keeping the original formatting and structure as much as possible. Only update the content where relevant. Return the improved resume content only.

Resume:
{resume_text}

Job Description:
{job_desc}
"""
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(url, json=data)
    response.raise_for_status()
    result = response.json()
    try:
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception:
        print("Error with Gemini response:", result)
        raise

def update_docx_with_text(doc, new_text):
    # Simple approach: replace all paragraphs with new text split by lines
    lines = new_text.split('\n')
    for i, para in enumerate(doc.paragraphs):
        if i < len(lines):
            para.text = lines[i]
        else:
            para.text = ''
    # If more lines, add new paragraphs
    for line in lines[len(doc.paragraphs):]:
        doc.add_paragraph(line)
    return doc

def main():
    print("--- Resume Auto-Updater with Gemini ---")
    resume_path = prompt_file_path("Enter path to your resume (.docx): ")
    job_desc_path = prompt_file_path("Enter path to the job description (.txt or .docx): ")
    api_key = get_gemini_api_key()

    resume_text, doc = read_docx_text(resume_path)
    if job_desc_path.lower().endswith('.docx'):
        job_desc, _ = read_docx_text(job_desc_path)
    else:
        job_desc = read_txt_file(job_desc_path)

    print("Contacting Gemini API to update your resume...")
    new_resume_text = call_gemini(api_key, resume_text, job_desc)

    print("Updating resume document...")
    updated_doc = update_docx_with_text(doc, new_resume_text)
    updated_docx_path = os.path.splitext(resume_path)[0] + "_updated.docx"
    updated_doc.save(updated_docx_path)
    print(f"Updated .docx saved to: {updated_docx_path}")

    print("Converting to PDF...")
    updated_pdf_path = os.path.splitext(resume_path)[0] + "_updated.pdf"
    convert(updated_docx_path, updated_pdf_path)
    print(f"PDF saved to: {updated_pdf_path}")

if __name__ == "__main__":
    main()
