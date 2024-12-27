LLM Core
===

This branch contains the core LLM implementation along with LLM guardrails for language learning.

Llama.cpp is used for inference.

Currently, this code can only be run on [Rosie](https://msoe.dev/).

## How to Run Repo Notebooks in the Browser

- Open a Git bash terminal (NOT a windows terminal)
- SSH into Rosie (run `ssh your_rosie_username@dh-mgmt2.hpc.msoe.edu`)
- Clone this repo or navigate to an existing version from the terminal.
  - Clone by running `git clone <HTTPS or SSH url>`.
    - Go into the repo after cloning by running `cd LLTM`.
  - Navigate by running `cd path/to/navigate/to`.
  - See the current directory contents with `ls` or `ls -la`.
  - Use tab to autocomplete paths.
- Once in the repo directory, run `./job.sh`.

- Open a second Git bash terminal
- Tunnel into the job node
  - run `ssh -J your_rosie_username@dh-mgmt2.hpc.msoe.edu -L 14321:localhost:14321 your_rosie_username@dh-nodeX.hpc.msoe.edu`, **BUT** replace `dh-nodeX` with the node name specified in the first output line of `job.sh`.
- Copy the URL from the `./job.sh` output starting with `http://localhost`, and paste it (including the token) in a browser

## How To Run Repo Notebooks in VSCode

- Open VSCode
- In VSCode, SSH into Rosie using the [remote SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh) extension which is available in the built-in VSCode extension browser.
    - Once the extension is installed, click the SSH icon (two arrows pointing at each other) at the bottom-left of VSCode, and press "Connect Current Window to Host..."
    - Connect to the host `your_rosie_username@dh-mgmt2.hpc.msoe.edu`
- From VSCode, clone this repo (or navigate to an existing version) and open a terminal in it.
- Run `./job.sh`.
- Open a Jupyter Notebook from VSCode (e.g., `llm.ipynb`)
- Click the kernel connection button in the top right of the notebook.
- Click "Select Another Kernel..."
- Click "Existing Jupyter Server..."
- Click "Enter the URL of the running Jupyter Server"
- Paste the URL
    - Copy the URL output from `job.sh` that begins with `http://localhost...`.
    - Paste it into the dialog box.
    - CHANGE the domain from `localhost` to the node that the job started on (e.g., `dh-node10`). You can find this node name seeing the first output of the `job.sh` command.
- Press enter or select the only option a few times. The notebook should now be working.