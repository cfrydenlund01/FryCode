# Mistral E*Trade GUI Stock Assistant

This application is a Python-based GUI tool for Windows that integrates a locally deployed Mistral 7B Instruct AI model with the E*Trade API. It's designed to monitor and analyze the U.S. stock market, providing structured investment recommendations based on a user-defined strategy, with a strong emphasis on risk management and explicit user confirmation for all trades.

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Setup and Installation](#setup-and-installation)
    - [E*Trade API Key Setup](#etrade-api-key-setup)
    - [Mistral 7B Model Download](#mistral-7b-model-download)
    - [Python Environment Setup](#python-environment-setup)
- [Usage](#usage)
    - [Test Mode (Simulation)](#test-mode-simulation)
    - [Live Mode](#live-mode)
    - [Risk Profile Settings](#risk-profile-settings)
    - [Manual Retraining](#manual-retraining)
- [Folder Structure](#folder-structure)
- [Safety and Transparency](#safety-and-transparency)
- [License](#license)

## Features

- **Real-Time Market Data Integration**: Connects securely to the E*Trade API for live prices, volume, chart data, technical indicators, and sentiment.
- **AI Pattern Recognition (Mistral 7B)**: Employs a locally embedded Mistral 7B Instruct model to analyze market data for trading signals (breakouts, reversals, momentum).
- **User Risk Management**: Allows users to define risk profiles (Low, Medium, High) to filter recommendations.
- **Structured Investment Recommendations**: Provides clear BUY, SELL, HOLD signals with detailed information including confidence, risk level, time horizon, and reasoning.
- **Execution Control**: Toggles between a "Test Mode" for simulated trading and a "Live Mode" requiring explicit user confirmation for real trades.
- **Explicit User Confirmation Only**: No automatic or unapproved trading. All live trades require user confirmation via the GUI.
- **Automated Time Horizon Determination**: Mistral infers ideal holding periods (Short-term, Swing, Long-term).
- **Manual Retraining & Adjustment**: Provides a mechanism for manual model retraining.
- **No Data Fabrication**: All numerical output is strictly derived from E*Trade API responses or direct calculations.

## System Requirements

- Windows Operating System
- Python 3.9+
- Recommended: NVIDIA GPU with CUDA support for faster Mistral 7B inference.

## Setup and Installation

### E*Trade API Key Setup

1.  **Create an E*Trade Developer Account**: Go to the E*Trade Developer website and sign up for a developer account.
2.  **Create a New Application**: Register a new application to obtain your Consumer Key and Consumer Secret.
3.  **Configure Callback URL**: For OAuth 1.0a, you'll need a callback URL. For a desktop application, you might use `oob` (out-of-band) or set up a local redirect URL (e.g., `http://localhost:8080`).
4.  **Environment Variables**: Create a `.env` file in the root directory (`mistral_etrade_gui/`) and add your E*Trade API credentials:

    ```
    ETRADE_CONSUMER_KEY=your_consumer_key
    ETRADE_CONSUMER_SECRET=your_consumer_secret
    ETRADE_ACCOUNT_ID=your_account_id # Optional, for specific account access
    ```

### Mistral 7B Model Download

You have two primary options for deploying Mistral 7B locally: Hugging Face Transformers (PyTorch/TensorFlow) or `llama.cpp` (quantized versions for CPU/GPU).

**Option 1: Hugging Face Transformers (Recommended for GPU)**

The model will be downloaded automatically by the `transformers` library the first time it's loaded. Ensure you have sufficient disk space (typically 14GB+ for the full model).

**Option 2: `llama.cpp` (Recommended for CPU or limited VRAM)**

1.  **Download a Quantized GGUF Model**: Visit the Hugging Face page for Mistral 7B GGUF models (e.g., `TheBloke/Mistral-7B-Instruct-v0.2-GGUF`).
2.  **Place the Model**: Download your chosen `.gguf` file (e.g., `mistral-7b-instruct-v0.2.Q4_K_M.gguf`) and place it in a new `mistral_etrade_gui/ai/models/` directory:

    ```
    mistral_etrade_gui/
    ├── ai/
    │   ├── models/
    │   │   └── mistral-7b-instruct-v0.2.Q4_K_M.gguf
    │   └── mistral_agent.py
    ```

    You will need to configure `mistral_agent.py` to point to this file.

### Python Environment Setup

1.  **Clone the Repository**:
    ```bash
    git clone [https://github.com/your-username/mistral_etrade_gui.git](https://github.com/your-username/mistral_etrade_gui.git)
    cd mistral_etrade_gui
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment**:
    -   **Windows**:
        ```bash
        .\venv\Scripts\activate
        ```
    -   **macOS/Linux**:
        ```bash
        source venv/bin/activate
        ```

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

    **Note for `llama-cpp-python`**: Depending on your system and whether you want GPU acceleration, you might need to follow specific installation instructions from the `llama-cpp-python` GitHub repository for your OS and CUDA/ROCm setup.

## Usage

To start the application, run `main.py` from the root directory after activating your virtual environment:

```bash
python main.py