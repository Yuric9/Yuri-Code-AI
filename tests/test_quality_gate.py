from agent.quality_gate import validation_passed


def test_validation_passed_requires_zero_exit_codes():
    assert validation_passed("$ python -m pytest -q\nexit=0\n2 passed")
    assert not validation_passed("$ npm test\nexit=1\nfailed")
    assert not validation_passed("no commands executed")


def test_validation_passed_accepts_multiple_successful_checks():
    report = "$ python -m compileall -q .\nexit=0\n\n$ npm run build\nexit=0\nok"
    assert validation_passed(report)
