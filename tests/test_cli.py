import argparse

import pytest

from radar.cli import build_parser, positive_int


def test_positive_int_rejects_zero_and_negative_values():
    assert positive_int("25") == 25
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int("0")
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int("-1")


def test_rescore_parser_defaults_to_batched_all_job_processing():
    args = build_parser().parse_args(["rescore-jobs", "--dry-run", "--only-outdated"])

    assert args.batch_size == 500
    assert args.limit is None
    assert args.dry_run is True
    assert args.only_outdated is True
    assert args.active_only is False
