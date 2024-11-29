from happy_migrations._utils import mig_name_parser


def test_mig_incorrect_name():
    assert mig_name_parser("Mar^&*io") == "mar___io"
