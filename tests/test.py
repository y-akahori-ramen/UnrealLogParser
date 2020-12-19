import unittest
import uelogparser
from datetime import datetime, timezone, timedelta


class ParserTest(unittest.TestCase):
    def test_sample(self):
        tz = timezone(offset=timedelta(hours=9))
        logs = []
        logs.append(
            uelogparser.Log(
                date=datetime(2020, 12, 14, 13, 46, 3, 809000, tz),
                verbosity=uelogparser.Verbosity.Log,
                category='LogTemp',
                log='LogTemp: MultilineTest line1\nMultilineTest line2',
                log_body='MultilineTest line1\nMultilineTest line2'
            )
        )
        logs.append(
            uelogparser.Log(
                date=datetime(2020, 12, 14, 13, 46, 4, 819000, tz),
                verbosity=uelogparser.Verbosity.Warning,
                category='SampleCategory',
                log='SampleCategory: Warning: WarningVerbosityTest',
                log_body='WarningVerbosityTest'
            )
        )
        logs.append(
            uelogparser.Log(
                date=datetime(2020, 12, 14, 13, 46, 5, 829000, tz),
                verbosity=uelogparser.Verbosity.Error,
                category='LogTemp',
                log='LogTemp: Error: ErrorVerbosityTest',
                log_body='ErrorVerbosityTest'
            )
        )
        logs.append(
            uelogparser.Log(
                date=datetime(2020, 12, 14, 13, 46, 6, 839000, tz),
                verbosity=uelogparser.Verbosity.Display,
                category='LogTemp',
                log='LogTemp: Display: DisplayVerbosityTest',
                log_body='DisplayVerbosityTest'
            )
        )
        logs.append(
            uelogparser.Log(
                date=datetime(2020, 12, 14, 13, 46, 7, 849000, tz),
                verbosity=uelogparser.Verbosity.Log,
                category='LogTemp',
                log='LogTemp: LogVerbosityTest',
                log_body='LogVerbosityTest'
            )
        )
        logs.append(
            uelogparser.Log(
                date=datetime(2020, 12, 14, 13, 46, 8, 859000, tz),
                verbosity=None,
                category=None,
                log='NoneCategory,VerbosityTest',
                log_body='NoneCategory,VerbosityTest'
            )
        )

        with open('tests/data/testlog.log', encoding='utf_8_sig') as log_file:
            parser = uelogparser.Parser(log_file)
            log = parser.read()
            log_idx = 0

            while log:
                self.assertTrue(self._is_equal(logs[log_idx], log))
                log = parser.read()
                log_idx += 1

    def test_invalid_log(self):
        with open('tests/data/invalidlog.log', encoding='utf_8_sig') as log_file:
            with self.assertRaises(Exception):
                uelogparser.Parser(log_file)

    @staticmethod
    def _is_equal(log1: uelogparser.Log, log2: uelogparser.Log) -> bool:
        return log1.log_body == log2.log_body\
            and log1.log == log2.log\
            and log1.verbosity == log2.verbosity\
            and log1.category == log2.category\
            and log1.date == log2.date
