from pathlib import Path
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parents[1]
URLS={
ROOT/"data/raw/census/sub-est2025.csv":"https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/cities/totals/sub-est2025.csv",
ROOT/"data/raw/bls/oesm24ma.zip":"https://www.bls.gov/oes/special-requests/oesm24ma.zip",}
def download(path,url):
 path.parent.mkdir(parents=True,exist_ok=True); req=Request(url,headers={"User-Agent":"ai-data-analyst-day1/1.0"})
 with urlopen(req,timeout=60) as r, path.open("wb") as out: out.write(r.read())
 print(f"downloaded {path}")
if __name__=="__main__":
 for path,url in URLS.items(): download(path,url)
