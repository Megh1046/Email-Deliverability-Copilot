from domains.header_analysis.header_parser import HeaderParser


def test_header_parser_extracts_authentication_and_relaxed_alignment():
    headers = """From: Campaign <news@example.com>
Return-Path: <bounce@example.com>
DKIM-Signature: v=1; d=example.com; s=mailer;
Authentication-Results: mx.receiver.test; spf=pass smtp.mailfrom=bounce.example.com; dkim=pass header.d=example.com; dmarc=pass header.from=example.com

"""
    result = HeaderParser().parse(headers)
    assert result.spf.result == result.dkim.result == result.dmarc.result == "PASS"
    assert result.from_domain == "example.com"
    assert result.alignment.spf is True
    assert result.alignment.dkim is True
    assert result.alignment.overall is True


def test_header_parser_reports_dkim_alignment_failure_with_remediation():
    headers = """From: Campaign <news@example.com>
Authentication-Results: mx.receiver.test; spf=fail smtp.mailfrom=mailer.sendgrid.net; dkim=pass header.d=sendgrid.net; dmarc=fail header.from=example.com

"""
    result = HeaderParser().parse(headers)
    assert result.dkim.result == "PASS"
    assert result.alignment.dkim is False
    assert result.alignment.overall is False
    assert result.root_cause.title == "DKIM Alignment Failure"
    assert result.remediation
