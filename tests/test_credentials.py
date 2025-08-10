from datetime import datetime, timezone

from utils import credentials


def test_set_get_clear(fake_keyring):
    credentials.set_consumer_credentials("ck", "cs")
    assert credentials.have_consumer_credentials()
    assert credentials.get_consumer_credentials() == ("ck", "cs")

    now = datetime.now(timezone.utc).isoformat()
    credentials.set_access_token("at", "ats", now)
    tok, sec, issued = credentials.get_access_token()
    assert tok == "at" and sec == "ats" and issued is not None

    credentials.clear_all_credentials()
    assert not credentials.have_consumer_credentials()
    assert credentials.get_access_token() == (None, None, None)

