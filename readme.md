# PyPVE

PyPVE is a CLI app for managing a Proxmox cluster. It is built with [Typer](https://typer.tiangolo.com/), and utilizes the Proxmox Virtualization Environment API. 

## Features
PyPVE currently supports:
- status

    Prints the status of all the nodes in the cluster or the status of all of the VMs in the cluster.
- start

    Starts the LXC or QEMU virtual machine with the specified VMID.

- shutdown

    Gracefully stops the LXC or QEMU virtual machine with the specified VMID.
## How to use?
The project is being developed on Python 3.9.1. Install the required packages with `pip install requirements` and create the required JSON files in  the same folder as `main.py`:

- `hosts.json`

    Defines the host on which the API will be accessed. Should be in the following format:
    ```
    {
    "host": "[host IP or FQDN]"
    }
    ```
- `token.json`

    Defines the API user's name, the name of the API key and the API key itself. Should be in the following format:
    ```
    {
    "username": "[user]@pam",
    "name": "[name of API key]",
    "value": "[API key]"
    }
    ```

### How to get a Proxmox API token?
You can generate your own Proxmox API token in the datacenter view, in `Permissions => API Tokens`, where you press the `add` button at the top of the page. The token itself must be saved to a file as it is only shown once upon generation.
## Planned features
I am currently adding support for creating LXC containers from the CLI.