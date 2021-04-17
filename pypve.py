#!/usr/bin/python3
from proxmoxer import ProxmoxAPI
from enum import Enum
from time import sleep, time
import json
import typer
import os

# Required for typer
app = typer.Typer()

# Getting the file's directory for configuration files
DIRECTORY = os.path.dirname(__file__)[:-1]

print(DIRECTORY)

# Parts of the spinny animation
ANIMATION = ['-', '\\', '|', '/']

# Loads the hosts json. Currently put only one host in there.
hosts = json.load(open(f"{DIRECTORY}hosts.json"))

# Loads the credentials and aliases proxmox
credentials = json.load(open(f"{DIRECTORY}token.json")) 
proxmox = ProxmoxAPI(
    hosts["host"],
    user=credentials["username"],
    token_name=credentials["name"],
    token_value=credentials["value"],
    verify_ssl=False,
)


def percent_used(maximum, used, accuracy=2):
    """Calculates percentage to a certain accuracy"""
    int_percent = round(used/maximum*100, accuracy)
    percentage = str(int_percent) + "%"
    return percentage

def is_same_id(vm_object, vmid):
    """Takes json object vm_object from cluster resources and a VM ID, and compares them."""
    vm = VirtualMachine(vm_object)
    if str(vm.vmid) == str(vmid):
        return True
    else:
        return False

def get_vm_type(vm_object):
    """Makes an object and gets the VM type, just a bit easier to call a function."""
    vm = VirtualMachine(vm_object)
    return vm.type

def wait_until_status_OK(upid, hostnode):
    """Takes Unique Process ID of a task, prints that the task is running until the task 
        completes. Currently not on a timer, could go to infinity."""
    node = proxmox.nodes(hostnode)
    current_time = time()
    counter = 0
    while True:
        current_task = node.tasks(upid).get("status")
        current_task = Task(current_task)
        tmp_time = time()
        if current_time + 0.15 < tmp_time and current_task.status == "running":
            print(f"Task running... {ANIMATION[counter]}", end="\r")
            counter += 1
            if counter == 4:
                counter = 0
            current_time = tmp_time
        if current_task.status == "stopped":
            return typer.echo("Task completed!      ")


class Task:
    """Defines the properties of tasks."""

    def __init__(self, iterable=(), **kwargs):
        """Takes task dictionary as argument, makes it into attributes with the 
            same key-value pairs."""
        self.__dict__.update(iterable, **kwargs)

    
class VirtualMachine:
    """Defines the properties of the PVE guests."""

    def __init__(self, iterable=(), **kwargs):
        """Takes VM dictionary as argument, makes it into attributes with the 
            same key-value pairs."""
        self.__dict__.update(iterable, **kwargs)
    
    def vm_status(self, verbose):
        """Outputs the status of the self VM, which it gets from cluster resources"""
        if self.status == "running":
            vm_status = typer.style(self.status, fg=typer.colors.GREEN, bold=True)
        else: 
            vm_status = typer.style(self.status, fg=typer.colors.RED, bold=True)
        message = str(self.vmid) + "-" + self.name + " on node " + self.node + ": " + vm_status 
        if verbose:
            maxmem = round(self.maxmem/1000000000, 2)
            mem = ", available RAM: " + str(maxmem) + "GiB"
            message += mem
        return message

    def start(self):
        if self.status == "stopped":
            node = proxmox.nodes(self.node)
            if self.type == "qemu":
                upid = node.qemu(self.vmid).status.post("start")
            elif self.type == "lxc":
                upid = node.lxc(self.vmid).status.post("start")
            else:
                return typer.echo("Unsupported VM type.")
            return typer.echo("Starting the VM."), wait_until_status_OK(upid, self.node)
        else:
            return typer.echo("The VM is already running!")

    def stop(self):
        if self.status == "running":
            node = proxmox.nodes(self.node)
            if self.type == "qemu":
                upid = node.qemu(self.vmid).status.post("shutdown")
            elif self.type == "lxc":
                upid = node.lxc(self.vmid).status.post("shutdown")
            else:
                return typer.echo("Unsupported VM type.")
            return typer.echo("Gracefully stopping the VM."), wait_until_status_OK(upid, self.node)
        else:
            return typer.echo("The VM is not running!")


class QEMU(VirtualMachine):
    """Defines the properties of the PVE QEMU-based guests. Inherits from VirtualMachine,
        will be used for QEMU-specific things, currently planned is live migration and cloning."""
    
    def __init__(self, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)


class LXC(VirtualMachine):
    """Defines the properties of the PVE QEMU-based guests. Inherits from VirtualMachine,
        will be used for LXC-specific things, currently planned is the very quick LXC create
        from template."""
    
    def __init__(self, iterable=(), **kwargs):
        self.__dict__.update(iterable, **kwargs)


class HostNode:
    """Defines the properties of PVE host nodes."""

    def __init__(self, iterable=(), **kwargs):
        """Takes node dictionary as argument, makes it into key-value attributes."""
        self.__dict__.update(iterable, **kwargs)

    def host_status(self, verbose):
        """Creates and formats message for node status."""
        if self.status == "online":
            vm_status = typer.style(self.status, fg=typer.colors.GREEN, bold=True)
        else: 
            vm_status = typer.style(self.status, fg=typer.colors.RED, bold=True)
        message = self.node + ": " + vm_status
        if verbose:
            maxmem = round(self.maxmem/1000000000, 2) # turns this into gigabytes
            usedmem = percent_used(self.maxmem, self.mem)
            mem = ", available RAM: " + str(maxmem) + "GiB used RAM: " + usedmem
            message += mem
        return message


class Resources(str, Enum):
    """Here just for fancy input checking."""
    vm = "vm"
    node = "node"


@app.command()
def status(type_of_resource: Resources, verbose: bool = typer.Option(False, "--verbose", "-v")):
    """Returns status of cluster resources."""
    message = ""
    for res in proxmox.cluster.resources.get(type=type_of_resource):
        if type_of_resource == "node":
            node = HostNode(res)
            message = node.host_status(verbose)
        if type_of_resource == "vm":
            vm = VirtualMachine(res)
            message = vm.vm_status(verbose)
        typer.echo(message)

@app.command()
def cluster():
    """Reserved for status of cluster."""
    typer.echo("This command is reserved but currently not in use.")

@app.command()
def raw(resource: Resources):
    """Returns raw API data, used for testing."""
    typer.echo(proxmox.cluster.resources.get(type=resource))

@app.command()
def start(vmid: int):
    """Starts selected VM."""
    for res in proxmox.cluster.resources.get(type="vm"):
        vm = VirtualMachine(res)
        if is_same_id(res, vmid):
            vm.start()
            raise typer.Exit()
    typer.echo(f"There is no VM with ID {vmid}!")

@app.command()
def shutdown(vmid: int):
    """Gracefully stops selected VM."""
    for res in proxmox.cluster.resources.get(type="vm"):
        vm = VirtualMachine(res)
        if is_same_id(res, vmid):
            vm.stop()
            raise typer.Exit()
    typer.echo(f"There is no VM with ID {vmid}!")
    
@app.command()
def lxc_create(
        vmid: int = typer.Argument(...),
        memory: int = typer.Option(512)):
    """Will create an LXC container."""

if __name__ == "__main__":
    app()
