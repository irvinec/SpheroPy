"""Setup a conda environment for working with spheropy."""
# Keep this file in sync with setup_spheropy_env.py

import os, sys
import subprocess

def main():
    print('Setting up SpheroPy conda environment.')
    if not is_conda_available():
        print('\"conda\" is not available in this context. Are you sure you have minconda or anaconda installed and are running this from a conda environment?')

    add_conda_forge()
    install_deps()
    install_spheropy()
    # Give python access to bluetooth
    if is_running_on_linux():
        subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'libcap2-bin'])
        subprocess.check_call("sudo setcap 'cap_net_raw,cap_net_admin+eip' `which python3.6`", shell=True)

    print('Done setting up environment.')

def is_conda_available():
    try:
        subprocess.check_call(
            ['conda', '--help'],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def install_deps():
    subprocess.check_call(['conda', 'install', '--yes',
        'python=3.6',
        'pylint',
        'git',
        'pexpect']
    )
    subprocess.check_call(['pip', 'install',
        # install pybluez. If running on windows we need to install irvinec's fork that has a patch for windows.
        'git+https://github.com/irvinec/pybluez' if is_running_on_windows() else 'git+https://github.com/pybluez/pybluez',
        # install pygatt
        'git+https://github.com/peplin/pygatt']
    )

def install_spheropy():
    subprocess.check_call(['pip', 'install', 'git+https://github.com/irvinec/SpheroPy'])

def add_conda_forge():
    subprocess.check_call(['conda', 'config', '--add', 'channels', 'conda-forge'])

def is_running_on_windows():
    return os.name == 'nt'

def is_running_on_linux():
    return os.name == 'posix'

def is_running_on_mac():
    return os.name == 'mac'

if __name__ == '__main__': main()