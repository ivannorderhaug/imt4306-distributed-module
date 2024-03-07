# imt4306-distributed-module
This repository is a part of the portfolio for IMT4306 - Introduction to Research in Decentralised Systems. 

## Requirements

- [Python v20.12.2](https://www.python.org/)
- [netifaces](https://pypi.org/project/netifaces/) - a python library for network interface information
- [twisted](https://pypi.org/project/Twisted/) - a python library for asynchronous networking


## Installation
1. Clone the repository
```bash
git clone git@github.com:ivannorderhaug/imt4306-distributed-module.git
```
2. Navigate to the project folder
```bash
cd imt4306-distributed-module
```
3. Create a Python virtual environment
```bash
python -m venv env
```
4. Activate it (Linux & MacOS). Might be different for Windows.
```bash
source env/bin/activate
```
5. Install requirements
```bash
pip install -r requirements.txt
```
6. Run the application
```bash
python app.py
```
7. Enjoy!

## Usage
Once the application is started, you can either select to start a new game, in which you will be a "host"(peers will have to establish a connection with you to get the gamestate, or you can choose to join a game, where you will have to input the ip address and port of the peer you want to establish a connection to. From there, all that's left is to enjoy a good ol' game of Sudoku. 

![example.png](https://github.com/ivannorderhaug/imt4306-distributed-module/blob/dev/example.png)

Note: The game is very basic, and therefore lacking certain functionality such as marking candidates on an empty spot or clearing the whole board. Changing difficulty is also not possible.


## Limitations
- The protocol used is UDP, meaning there is a chance of packet loss. I have yet to experience that, but that might be because this has only ever been tested on the local network. If packets are lossed, I believe it will mess up the synchronization between the peers and there is no way to recover from that.
- Currently, only tested on local network.

