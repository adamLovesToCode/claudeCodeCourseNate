import modal

app = modal.App("job-scraper-pipeline")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements("requirements.txt")
    .pip_install("fastapi[standard]")
    .add_local_dir("tools", remote_path="/root/tools")
)

vol = modal.Volume.from_name("job-scraper-vol", create_if_missing=True)
VOLUME_PATH = "/data"


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("job-scraper-secrets")],
    volumes={VOLUME_PATH: vol},
    timeout=300,
)
def run_scraper():
    import os, sys
    sys.path.insert(0, "/root")
    import tools.scrape_job_listings as scraper
    os.makedirs(VOLUME_PATH, exist_ok=True)
    scraper.OUTPUT_PATH = f"{VOLUME_PATH}/raw_jobs.json"
    scraper.main()
    vol.commit()


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("job-scraper-secrets")],
    volumes={VOLUME_PATH: vol},
    timeout=600,
)
def run_extractor():
    import sys
    sys.path.insert(0, "/root")
    import tools.extract_and_export_jobs as extractor
    vol.reload()
    extractor.INPUT_PATH = f"{VOLUME_PATH}/raw_jobs.json"
    extractor.OUTPUT_PATH = f"{VOLUME_PATH}/jobs.xlsx"
    extractor.main()
    vol.commit()


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("job-scraper-secrets")],
    volumes={VOLUME_PATH: vol},
    timeout=900,
)
@modal.fastapi_endpoint(method="POST")
def trigger_pipeline():
    run_scraper.local()
    run_extractor.local()
    return {"status": "ok", "message": "Pipeline completed. Fetch output with: modal volume get job-scraper-vol jobs.xlsx ./jobs.xlsx"}


@app.local_entrypoint()
def main():
    print("Step 1: Scraping job listings...")
    run_scraper.remote()
    print("Step 2: Extracting fields and exporting to Excel...")
    run_extractor.remote()
    print("\nDone. Download output with:")
    print("  modal volume get job-scraper-vol jobs.xlsx ./jobs.xlsx")
