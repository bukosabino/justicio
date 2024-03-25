import sys
from datetime import datetime, timedelta

from src.etls.bopgr.scrapper import BOPGRScrapper


def main():
    if len(sys.argv) != 3:
        print("Uso: python main.py dd/MM/yyyy dd/MM/yyyy")
        sys.exit(1)

    comienzo = datetime.strptime(sys.argv[1], "%d/%m/%Y").date()
    fin = datetime.strptime(sys.argv[2], "%d/%m/%Y").date()

    scrapper = BOPGRScrapper()

    while comienzo <= fin:
        metadatos = scrapper.download_day(comienzo)

        print(f'--------------- Boletín con fecha {comienzo.strftime("%d/%m/%Y")} ---------------')
        comienzo += timedelta(days=1)
        for m in metadatos:
            print(f"Edicto #: {m.edicto} - Entidad: {m.entidad} - Asunto: {m.asunto}")
        print(f'Total edictos {len(metadatos)}')
        print(f'--------------- Fin boletín con fecha {comienzo.strftime("%d/%m/%Y")} ---------------')
        print(len(metadatos))

if __name__ == "__main__":
    main()
