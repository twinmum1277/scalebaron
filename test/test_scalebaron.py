import os
from scalebaron import run_scalebaron

def test_basic_run():
    input_dir = "examples/test_input"
    output_dir = "examples/test_output"
    os.makedirs(output_dir, exist_ok=True)
    run_scalebaron(input_dir=input_dir, output_dir=output_dir)
    output_files = os.listdir(output_dir)
    assert any(f.endswith(".png") for f in output_files), "No image output produced"
    assert any("summary" in f for f in output_files), "No summary table produced"