from pathlib import Path
import csv
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/raw/census/city_population_sample.csv"
DST=ROOT/"data/processed/city_population.csv"

def main():
    DST.parent.mkdir(parents=True, exist_ok=True)
    with SRC.open(newline="",encoding="utf-8") as src, DST.open("w",newline="",encoding="utf-8") as out:
        reader=csv.DictReader(src)
        writer=csv.DictWriter(out, fieldnames=["name","state","population","year","source"])
        writer.writeheader()
        for r in reader:
            writer.writerow({"name":r["city"].strip(),"state":r["state"].strip(),"population":int(r["population"]),"year":int(r["year"]),"source":r["source"].strip()})
    print(f"ETL transformed {SRC} -> {DST}")
if __name__ == "__main__": main()
