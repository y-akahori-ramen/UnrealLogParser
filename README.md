# UnrealLogParser
UnrealEngineが出力するログをPythonでパースする

# インストール方法

```
pip install git+https://github.com/y-akahori-ramen/UnrealLogParser
```

# 使用例

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
