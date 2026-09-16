# Annual Report Markdown Extractor — Streamlit App

Upload an annual report PDF, inspect any page, pick page ranges by
clicking (not typing, except for "how many ranges"), and extract
clean Markdown per range using LlamaParse.



## Files

- `app.py` — the Streamlit UI
- `extractor.py` — the extraction engine (unchanged from the CLI version)
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — upload size limit + theme
- `.streamlit/secrets.toml.example` — template for the two secrets you need

## Run locally

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# then edit .streamlit/secrets.toml with your real values
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this folder to a GitHub repo (public or private).
2. Go to https://share.streamlit.io and create a new app pointing at
   this repo, with `app.py` as the main file.
3. In the app's **Settings → Secrets**, add:

   ```toml
   APP_PASSWORD = "choose-a-strong-shared-password"
   LLAMA_CLOUD_API_KEY = "llx-..."
   ```

4. Deploy. Anyone who opens the app link will be asked for
   `APP_PASSWORD` before they can use it.

## Notes

- The password gate is a single shared password for the whole app —
  fine for a small internal tool, not meant as real multi-user auth.
- PDF pages are rendered on demand (not all at once), so browsing a
  1,000+ page PDF stays fast; recently viewed pages are cached for
  the session.
- `maxUploadSize` in `.streamlit/config.toml` is set to 500 MB —
  adjust if your reports are smaller/larger.
- The original uploaded PDF is never modified; only temporary page
  slices are created and deleted during extraction, same as the
  CLI version.