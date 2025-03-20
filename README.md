NAME TBD
===
*some language-learning project*

This repo has all code for the MAIC LLTM (large language-teaching model) research project.

Go to Lucas Gral on MS Teams for questions.

## How to Run Things

This project is intended to be run from a VSCode window sshed into Rosie with the [SSH extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh).

- [Install the extension and SSH into Rosie.](https://msoe-maic.com/library?nav=Articles&article=6-rosie-ssh)
  - Once the extension is installed, click the SSH icon (two arrows pointing at each other) at the bottom-left of VSCode, and press "Connect Current Window to Host..."
  - Connect to the host `your_rosie_username@dh-mgmt2.hpc.msoe.edu`
  - Select "Linux" if you're prompted to select an OS.
- Install any python-related extensions that VSCode notifies you to install while trying to run notebooks.
- From VSCode, clone this repo (or navigate to an existing version via `cd`). You will need to run terminals on Rosie from VSCode for commands.

For development, the intention is that subsystems will be developed/tested in notebooks while the whole UI will just be a python web server running from scripts.

### Running Notebooks (`job.sh`)

- Have a notebook open on Rosie in VSCode
- `cd` into this repo on Rosie
- Run `./job.sh`
- Copy the resulting link that contains `http://localhost...` and use it as a notebook kernel.
  - Click the kernel connection button in the top right of an open notebook.
  - Click "Select Another Kernel..."
  - Click "Existing Jupyter Server..."
  - Click "Enter the URL of the running Jupyter Server"
- Paste the link when prompted, but **replace `localhost` with the hostname at the top of the command output - something like `dh-nodeN`**
- The notebook should now be able to run code.

### Running the UI (`main.sh`)

- `cd` into this repo on Rosie
- Run `/.main.sh`
- Copy the ssh tunnel command in the output
- Open a Git bash terminal (NOT a windows terminal)
- Run the ssh tunnel command Git Bash on your local machine
- Go to `localhost:8001` in your browser. You can now go to pages like `localhost:8001/static/chat/index.html`.
