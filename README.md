This is the code I use to listen for UDP messages from WSJT-X and JS8Call then post QSO ADIF messages to my https://qrz.com logbook.

* This code is functional but not elegant.
* This code is *not supported* in any way.
* No PRs are accepted for this repo.
* This repo exists only for sharing and safekeeping of the code.

Notes:

1. Run the code in a virtual environment.
1. Don't forget to `pip install -r requirements.txt` after activating the venv.
1. Add your qrz.com logbook api key to `mycall_config.json`
1. The UDP listener is on the default port for WSJT-X (2337), to also listen for JS8Call messages configure JS8Call to emit messages on the same port number.
1. I typically just start the code in the venv with `python udp_to_qrz.py` in a terminal window, then just minimize the terminal and leave it running. If you want to run it detached or as a process, be my guest.