# Unofficial HackerOne API

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/studiogangster/hackerone_org_api/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/studiogangster/hackerone_org_api.svg)](https://github.com/studiogangster/hackerone_org_api/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/studiogangster/hackerone_org_api.svg)](https://github.com/studiogangster/hackerone_org_api/network)
[![GitHub issues](https://img.shields.io/github/issues/studiogangster/hackerone_org_api.svg)](https://github.com/studiogangster/hackerone_org_api/issues)

## Usage

1. **Install Poetry:**

   Ensure you have Poetry installed. If not, follow the instructions [here](https://python-poetry.org/docs/#installation) to install Poetry.

2. **Set up your virtual environment:**

   Use Poetry to create a virtual environment for your project. Open a terminal and navigate to your project directory. Run:

   ```bash
   poetry shell
    ```
2. **nvironment Variables:**
    1. Ensure sample_env is moved to .env in your project root.
    2. Customize the variables in the .env file according to your specific needs.

    ```
    mv sample_env .env
    ```
    # Update the variables in the .env file with the required values.

## Now, your application is up and running, ready to integrate with HackerOne seamlessly!




3. **Run the application:**

    Start the main script using Python. You can either run it directly:

    ```
    python main.py
    ```
    # Or use nohup to run it in the background:
    ```
    nohup python main.py &
    ```

