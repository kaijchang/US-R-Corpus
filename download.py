import requests

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import tqdm

PDFS_DIR = "pdfs"
TEXT_DIR = "text"

os.makedirs(PDFS_DIR, exist_ok=True)
os.makedirs(TEXT_DIR, exist_ok=True)

def process_result(result):
    if "resources" not in result or "pdf" not in result["resources"][0]:
        return

    pdf_url = result["resources"][0]["pdf"]

    for i in range(10):
        if i > 0:
            print(f"Retrying {pdf_url} ({i})")
        try:
            source_path = f"{PDFS_DIR}/{pdf_url.split('/')[-1]}".replace(".pdf", "")

            year = result["item"]["created_published"][0]

            source_text_path = f"{source_path}.txt"
            source_pdf_path = f"{source_path}.pdf"
            target_text_path = f"{TEXT_DIR}/{year}.txt"

            if not os.path.exists(source_text_path):
                with open(target_text_path, "w") as f:
                    pass

            subprocess.run(["wget", "-q", "-O", source_pdf_path, pdf_url])
            subprocess.run(["pdftotext", source_pdf_path], check=True)

            subprocess.run(f"cat {source_text_path} ff.txt >> {target_text_path}", shell=True)
            break
        except KeyError:
            break
        except subprocess.CalledProcessError:
            pass
        finally:
            subprocess.run(f"yes | rm -rf {source_path}*", shell=True)

page = 1

while True:
    r = requests.get(f"https://www.loc.gov/collections/united-states-reports?fo=json&c=150&at=results,pagination&sp={page}")
    data = r.json()
    pagination = data["pagination"]
    results = data["results"]

    print(f"Page {page} of {pagination['total']}")

    progress_bar = tqdm.tqdm(total=len(results))

    with ThreadPoolExecutor() as executor:
        for result in executor.map(process_result, results):
            progress_bar.update(1)

    progress_bar.close()

    if pagination["current"] == pagination["total"]:
        break

    page += 1
