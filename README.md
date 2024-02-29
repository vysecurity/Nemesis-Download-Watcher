# Nemesis Download Watcher
Watches the Downloads folder for any new files and inserts it into (Nemesis)[https://github.com/SpecterOps/Nemesis] for analysis.

Compatible with BRC4.

## Usage

Run in a `screen -S 1` session:

```
python3 main.py -d brc4/downloads/ -u nemesis -p <PASSWORD> -n <http://nemesis:8080>
```

**It will loop every 60 seconds** and process and files.