#!/usr/bin/env python3
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import app as app_module


class _FakeEvents:
    def list(self, **_kwargs):
        return self

    def execute(self):
        return {'items': []}


class _FakeCalendarService:
    def events(self):
        return _FakeEvents()


def main() -> None:
    os.environ['GOOGLE_CREDENTIALS'] = json.dumps({
        'refresh_token': 'fake-refresh-token',
        'client_id': 'fake-client-id',
        'client_secret': 'fake-client-secret',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'token': 'fake-token'
    })

    app_module.get_calendar_service = lambda: _FakeCalendarService()
    app_module.generate_contextual_reply = lambda *_args, **_kwargs: 'Test reply'

    client = app_module.app.test_client()
    response = client.post('/generate', json={
        'email_text': '',
        'timezone': 'ET',
        'duration': 30,
        'date_range': 'two_weeks'
    })

    print('Status:', response.status_code)
    print('Response:', response.get_json())


if __name__ == '__main__':
    main()
