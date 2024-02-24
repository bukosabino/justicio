import sys
from datetime import datetime

from src.etls.bopgr.scrapper import BOPGRScrapper


def main():
    if len(sys.argv) != 2:
        print("Uso: python main.py dd/MM/yyyy")
        sys.exit(1)

    fecha = datetime.strptime(sys.argv[1], "%d/%m/%Y").date()

    scrapper = BOPGRScrapper()
    metadatos = scrapper.download_day(fecha)
    print(metadatos)

if __name__ == "__main__":
    main()
