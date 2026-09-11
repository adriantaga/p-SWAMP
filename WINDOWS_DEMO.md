# Windows Nordic 44 Demo

This workshop guide describes two ways to run the Nordic 44 demo on Windows.
Use the ready-made executable for the quickest start, or install the source code
and dependencies if you want a full development setup.

## Option 1: Run the ready-made executable

1. Open this p-SWAMP [releases page](https://github.com/adriantaga/p-SWAMP/releases)
   and download `nordic44_rtsim-run_case-windows.exe` from the latest release's
   **Assets** section.

2. Double-click the downloaded executable. Windows may show a **Windows protected
   your PC** dialog because the executable is not digitally signed. Select **More
   info**, then select **Run anyway** to start the demo.

3. A terminal window should open first. The application can take 30 seconds or
   more to start, during which nothing else may appear to happen. Be patient and
   wait for the application windows to open.

4. On some computers, **More info** or **Run anyway** is not available. Try
   right-clicking the downloaded `.exe` file and selecting **Properties**. On the
   **General** tab, select the **Unblock** checkbox in the **Security** section,
   then select **Apply** and **OK**. Run the executable again. If the executable
   was downloaded in a ZIP archive, extract it before completing these steps.

## Option 2: Install from source

These instructions cover a complete Windows setup: downloading the source code,
installing Python and all dependencies, and running the Nordic 44 demo.
If you already have experience with Python and Git, you can adapt or skip steps
that do not apply to your existing setup.

1. Install [uv](https://docs.astral.sh/uv/) (a Python package manager) from PowerShell or Command Prompt:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   exit
   ```

2. Download the p-SWAMP source code ZIP:

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
