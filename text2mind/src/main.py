"""
Main module for text2mind tool.
"""

import os
import click
from tqdm import tqdm
import tempfile
import sys

# Allow relative imports when running as script
if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use relative imports for package
try:
    from .parser import parse_text
    from .xmind_generator import create_xmind_from_structure
except ImportError:
    # When run directly
    from parser import parse_text
    from xmind_generator import create_xmind_from_structure

@click.group()
def cli():
    """Convert text files to XMind mind maps."""
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
def convert(input_file, output_file):
    """Convert a text file to a mind map XMind file."""
    # Ensure output file has .xmind extension
    if not output_file.endswith('.xmind'):
        output_file = output_file + '.xmind'
        
    click.echo(f"Converting {input_file} to {output_file}")
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Parse the text
    click.echo("Parsing text...")
    structure = parse_text(text)
    
    # Create XMind file
    click.echo("Creating XMind file...")
    create_xmind_from_structure(structure, output_file)
    
    click.echo(f"Mind map saved to {output_file}")

@cli.command()
@click.argument('input_files', nargs=-1, type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
def batch_convert(input_files, output_dir):
    """Convert multiple text files to mind map XMind files."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    for input_file in tqdm(input_files, desc="Converting files"):
        # Generate output file name
        base_name = os.path.basename(input_file)
        name_without_ext = os.path.splitext(base_name)[0]
        output_file = os.path.join(output_dir, name_without_ext + ".xmind")
        
        # Convert the file
        convert.callback(input_file, output_file)

if __name__ == "__main__":
    cli() 