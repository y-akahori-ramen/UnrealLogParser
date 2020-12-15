from dataclasses import dataclass
from enum import Enum, auto
from datetime import datetime, timezone, timedelta
from typing import Optional
import io
import re


class Verbosity(Enum):
    """ログのVerbosityLevel
    """
    Log = auto()
    Warning = auto()
    Error = auto()
    Display = auto()


@dataclass
class Log:
    """パースしたログ情報

    Attributes:
        date (datetime): ログが出力された時刻
        verbosity (Verbosity): ログのVerbosityLevel
        category (str): ログカテゴリ
        log (str): 時刻情報を取り除いたログ
        log_body (str): 時刻情報、VerbosityLevel,カテゴリを取り除いたログ本文
    """
    date: datetime
    verbosity: Verbosity
    category: str
    log: str
    log_body: str


class Parser:
    """UnrealEngineのログファイルを読み取り、ログに付随する時刻やカテゴリなどの情報を解析した結果を取得する
    """

    def __init__(self, file_object: io.TextIOBase):
        """初期化

        Args:
            file_object (io.TextIOBase): UnrealEngineのログファイルオブジェクト

        Raises:
            Exception: UnrealEngineのログとして認識できない場合例外を送出します
        """

        # タイムゾーン取得
        # ログ出力が始まるまでに以下のようにタイムゾーンが出力されている
        # LogICUInternationalization: ICU TimeZone Detection - Raw Offset: +9:00, Platform Override: ''
        self._log_timezone = None
        self._file_object = file_object
        line = self._file_object.readline()
        while line:
            if 'TimeZone Detection' in line:
                match = Parser._extract_time_zone_pattern.match(line)
                offset = timedelta(hours=int(match.group(1)), minutes=int(match.group(2)))
                self._log_timezone = timezone(offset)
                break
            else:
                line = self._file_object.readline()

        if self._log_timezone is None:
            raise Exception('ログからタイムゾーンを検出できませんでした。UnrealEngineのログファイルでは無い可能性があります。')

    def read(self) -> Optional[Log]:
        """ログを１つ読み込む

        Returns:
            Optional[Log]: 読み込んだログ情報。これ以上ログを読み込めない場合はNoneを返します。
        """
        line = self._file_object.readline()
        if line == '':
            return None

        while line:
            if Parser._is_logstart(line):
                log = Parser._parse_log_start_line(line, self._log_timezone)
                if not log:
                    line = self._file_object.readline()
                    continue

                # 複数行で出力されているログがあるため次のログ開始にマッチするまでのものをまとめる
                prev_pos = self._file_object.tell()
                line = self._file_object.readline()
                while line and not self._is_logstart(line):
                    prev_pos = self._file_object.tell()
                    log.log += '\n'
                    log.log += line.replace('\n', '')
                    log.log_body += '\n'
                    log.log_body += line.replace('\n', '')
                    line = self._file_object.readline()

                # 次のログの開始にマッチした場合に次のreadで検出できるように直前のreadlineを巻き戻す
                line = self._file_object.seek(prev_pos)
                return log
            else:
                line = self._file_object.readline()

        return None

    # タイムゾーン情報のログからオフセット時間と分を抽出する正規表現
    # LogICUInternationalization: ICU TimeZone Detection - Raw Offset: +9:00, Platform Override: ''
    # というようなログが出力されており、そのログから抽出する
    # group1: year
    # group2: minute
    _extract_time_zone_pattern = re.compile(r'.+Raw Offset:\s*([^:]+):(\d+)')

    # UEログ開始パターン
    # 時刻情報とログ自体をグループで分離することができる
    # [2020.12.13-02.11.01:195][404]LogTemp: Error: LogTemp Verbosity:Error
    # というログから
    # 前半の時刻情報 [2020.12.12-13.09.43:708]
    # 後半のログ LogTemp: Error: LogTemp Verbosity:Error
    # を分離する
    # group1: year
    # group2: month
    # group3: day
    # group4: hour
    # group5: minute
    # group6: second
    # group7: milliseconds
    # group8: log
    _log_start_pattern = re.compile(r'^\[(\d+)\.(\d+)\.(\d+)-(\d+)\.(\d+)\.(\d+):(\d+)\]\[[\s\d]+\](.+)$')

    # ログからカテゴリを抽出する
    # LogTemp: Error: LogTemp Verbosity:Error
    # とういうログから
    # カテゴリの LogTemp
    # それいこうのError: LogTemp Verbosity:Error
    # を分離する
    # group1: ログカテゴリ
    # group2: ログ文
    _split_log_category = re.compile(r'([^:]+):\s+(.+)')

    # ログのVerbosityを抽出する
    # Error: LogTemp Verbosity:Error
    # というログから
    # VerbosityのError
    # それ以降のLogTemp Verbosity:Error
    # を抽出する
    # UEのVerbosityは以下のものに限定される
    # Warning
    # Error
    # Display
    # Logの場合はログに情報がでないためこのパターンにマッチしない場合はVerbosityがLogとなる
    # group1: Verbosity
    # group2: ログ文
    _split_log_verbosity = re.compile(r'(Warning|Error|Display):\s+(.+)')

    @staticmethod
    def _is_logstart(line: str) -> bool:
        """UnrealEngineのログ出力開始フォーマットとなっているか

        UnrealEngineはログごとに時刻情報の出力から始まり、それを検出する。
        複数行ログの出力すると先頭に時刻情報がなくその場合は直前に開始されたログの内容とみなされる。
        読み込んだログファイルの行がログ開始なのかそうで無いのかを区別するのに使用する。

        Args:
            line (str): チェックしたい文字列

        Returns:
            bool: ログ出力開始フォーマットかどうか
        """
        match = Parser._log_start_pattern.match(line)
        return match is not None

    @staticmethod
    def _parse_log_start_line(line: str, log_timezone: timezone) -> Optional[Log]:
        """UnrealEngineのログ開始文字列をパースする

        ログ開始文字列であってもパースに失敗することがあります。
        UnrealEngineのログにはログファイルを閉じた時刻などのシステム的な情報が出力されていることがあり、
        その場合はUE_LOGマクロで出力されるログフォーマットとは異なり、パースに失敗します。        

        Args:
            line (str): 文字列
            log_timezone (timezone): タイムゾーン

        Returns:
            Optional[Log]: パースしたログ情報。パースに失敗するとNoneを返します。
        """
        match = Parser._log_start_pattern.match(line)
        time = datetime(
            year=int(match.group(1)),
            month=int(match.group(2)),
            day=int(match.group(3)),
            hour=int(match.group(4)),
            minute=int(match.group(5)),
            second=int(match.group(6)),
            microsecond=int(match.group(7))*1000,
            tzinfo=log_timezone
        )

        # ログカテゴリ検出
        log_without_time = match.group(8)
        category_match = Parser._split_log_category.match(log_without_time)
        if category_match is None:
            return None

        category = category_match.group(1)
        log_without_category = category_match.group(2)

        # Verbosity検出
        verbosity_math = Parser._split_log_verbosity.match(log_without_category)
        if verbosity_math is not None:
            verbosity = Verbosity[verbosity_math.group(1)]
            log_body = verbosity_math.group(2)
        else:
            verbosity = Verbosity.Log
            log_body = log_without_category

        return Log(time, verbosity, category, log_without_time, log_body)
