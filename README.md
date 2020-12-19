![Python package](https://github.com/y-akahori-ramen/UnrealLogParser/workflows/Python%20package/badge.svg)

# UnrealLogParser
Parsse UnrealEngine Logs in Python

# Install

```
pip install git+https://github.com/y-akahori-ramen/UnrealLogParser
```

# Sample

```py
import uelogparser


with open('ue4.log', encoding='utf_8_sig') as log_file:
    parser = uelogparser.Parser(log_file)
    log = parser.read()

    while log:
        print('-loginfo')
        print(f'date:{log.date}')
        print(f'verbosity:{log.verbosity}')
        print(f'category:{log.category}')
        print(f'log:{log.log}')
        print(f'log_body:{log.log_body}')
        print('-end')
        log = parser.read()
```
