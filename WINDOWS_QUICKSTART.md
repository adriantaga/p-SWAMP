# Windows Quick Start

These instructions cover a complete Windows setup: downloading the source code,
installing Python and all dependencies, and running the Nordic 44 demo.
If you already have Python experience, you can adapt or skip steps that do not
apply to your existing setup.

1. Install [uv](https://docs.astral.sh/uv/) (a Python package manager) from PowerShell or Command Prompt:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   exit
   ```

2. Download the p-SWAMP source code:

   1. Open the [p-SWAMP GitHub repository](https://github.com/p-swamp/p-SWAMP).
   2. Select **Code** and then **Download ZIP**.
   3. Extract the ZIP archive.

3. Open a terminal in the extracted `p-SWAMP` folder. In Windows 11, right-click the folder and select **Open in Terminal**.

4. Create and activate a Python 3.12 virtual environment, then install the full dependency set. uv downloads Python 3.12 automatically if it is not already installed:

   ```powershell
   uv venv --python 3.12 --system-certs
   .venv\Scripts\activate
   uv sync --extra full
   ```

5. Run the Nordic 44 real-time simulation demo:

   ```powershell
   python examples/nordic44_rtsim/run_case.py
   ```
