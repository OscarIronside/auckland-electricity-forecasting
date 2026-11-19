"""Execute the forecasting notebook using this environment's own kernel."""

from pathlib import Path
import argparse
import json
import sys
import tempfile

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=root/'reports/forecasting-executed.ipynb')
    args = parser.parse_args()
    notebook = nbformat.read(root/'forecasting.ipynb', as_version=4)
    with tempfile.TemporaryDirectory(prefix='forecasting-kernel-') as directory:
        kernel_path = Path(directory)/'portfolio'
        kernel_path.mkdir()
        spec = {'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
                'display_name': 'Portfolio Python', 'language': 'python',
                'env': {'MPLBACKEND': 'Agg'}}
        (kernel_path/'kernel.json').write_text(json.dumps(spec))
        specs = KernelSpecManager(kernel_dirs=[directory])
        manager = KernelManager(kernel_name='portfolio', kernel_spec_manager=specs)
        client = NotebookClient(notebook, km=manager, timeout=300,
                                resources={'metadata': {'path': str(root)}})
        try:
            client.execute()
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, args.output)
    print(f'Executed {sum(c.cell_type == "code" for c in notebook.cells)} notebook code cells.')
    print(f'Notebook with refreshed outputs: {args.output}')


if __name__ == '__main__':
    main()
