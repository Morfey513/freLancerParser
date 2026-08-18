# Freelancer Parser

V2 parser for rendered Freelancer search-result pages. It uses a separate local
Opera profile so you can log in manually; credentials are never stored in code.

## Setup

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Save a login session

```powershell
python main.py --login
```

Log in in the browser window yourself, then return to the terminal and press
Enter. The local Opera profile is stored in `data/opera_profile/`, which is
ignored by Git because it contains session data.

Opera is detected at its standard per-user Windows location. If yours is
installed elsewhere, set `OPERA_EXECUTABLE` to the full path of `opera.exe`.

## Reuse an existing Opera session

Close Opera first, then add `--reuse-opera-session` to import a copy of its
profile into `data/opera_existing_session/`. Your normal Opera profile is not
changed.

```powershell
python main.py "https://www.freelancer.com/search/projects/?q=python" --reuse-opera-session
```

If Opera stores its profile elsewhere, set `OPERA_PROFILE_DIR` to that folder.

## Use the actual open Opera window

Playwright cannot attach to an ordinary running Opera instance. Close Opera, then
start it once with a local debugging port:

```powershell
& "C:\Users\And\AppData\Local\Programs\Opera\opera.exe" --remote-debugging-port=9222
```

Log in normally in that Opera window, then run the parser with:

```powershell
python main.py "https://www.freelancer.com/search/projects/?q=python" --connect-existing-opera
```

This attaches to the already-open Opera process, reuses its tabs/session, and
does not close Opera when parsing completes.

## Run

```powershell
python main.py "https://www.freelancer.com/search/projects/?q=python"
```

The response is saved to `data/raw_page.html`; parsed jobs are written to `data/jobs.json`.
Add `--headless` after you have saved a valid session to run without a browser window.

## Test

```powershell
pytest
```
