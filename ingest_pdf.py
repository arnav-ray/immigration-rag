from docling.document_converter import DocumentConverter
from pathlib import Path

# 1. Setup the directory paths
input_dir = Path("data_input")
output_dir = Path("data_output")

# 2. Initialize the Universal Docling brain
converter = DocumentConverter()

print(f"Scanning '{input_dir}' for documents...")

# 3. Loop through EVERY file in the input folder
for input_file in input_dir.iterdir():
    # Ignore hidden system files or folders
    if input_file.is_file() and not input_file.name.startswith('.'):
        print(f"\nProcessing: {input_file.name} (Format detected: {input_file.suffix})")
        
        try:
            # Docling automatically adapts to XML, HTML, DOCX, PDF, etc.
            result = converter.convert(input_file)
            
            # Save it with the same name, but as a .md file
            output_filename = output_dir / f"{input_file.stem}_Clean.md"
            with output_filename.open("w", encoding="utf-8") as f:
                f.write(result.document.export_to_markdown())
                
            print(f" -> Success! Saved to: {output_filename}")
            
        except Exception as e:
            print(f" -> Failed to process {input_file.name}. Error: {e}")

print("\nBatch Ingestion Complete!")