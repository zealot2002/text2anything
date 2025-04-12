# Text2Mind

A tool to convert text files to XMind mind maps.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
python src/main.py convert input.txt output.xmind
```

### Web Interface

```bash
python run_web_app.py
```

Then open http://localhost:8088 in your browser.

### Input Format

The input text file should follow a hierarchical format using indentation:

```
Root Topic
    Subtopic 1
        Sub-subtopic A
        Sub-subtopic B
    Subtopic 2
        Sub-subtopic C
```

## Examples

Check the examples directory for sample input files.

## Features

- Parses indented text to create hierarchical mind map structures
- Generates XMind files that can be opened with XMind software
- Provides both command-line and web interfaces
- Supports batch conversion of multiple files 