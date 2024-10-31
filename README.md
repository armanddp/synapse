# GoPro Synapse

A GoPro livestreaming service for Raspberry Pi.

## Quick Install 

```
curl -sSL https://raw.githubusercontent.com/armanddp/synapse/main/install.sh | sudo bash
```

## Manual Installation

1. Clone the repository:

```
git clone https://github.com/armanddp/synapse.git
```


2. Run the installer:

```
bash
cd synapse
sudo ./install.sh
```

## Configuration

Edit the configuration file at `/etc/gopro-synapse/config.ini`

## Logs

View logs with:

```
bash
tail -f /var/log/gopro-livestream.log
```