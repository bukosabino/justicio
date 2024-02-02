This is a template module to load gazettes (e.g.: BOE) and/or single documents (e.g.: sentencias judiciales) into the embedding database.

# Gazettes

A gazette in this project has some requirements:

* A gazette is divided into days.
* Each day has many documents.

To define an ETL for your gazette, you need to fill some files:

1. `metadata.py` Define the metadata to be stored in the embedding database.
2. `scrapper.py` Define a class with some methods to scrape the information. 
3. `load.py` You can define the different scripts to load the data.

### Batch/Historical Load

If you want to do a batch/historical load:

```sh
python -m src.etls.template.load dates <collection_name> <date_start_%Y/%m/%d> <date_end_%Y/%m/%d>
```

Note: You should update the end/start dates in the `config/config.py' file.

### Daily (today) load

Most likely, your Gazette will be updated every day, so you will need to run a daily ETL script. Take a look at src.etls.template.load.py for inspiration.

```sh
python -m src.etls.template.load today <collection_name>
```

You will probably also want to schedule a daily job to update your embedding database. Then take a look at `src/etls/template/schedule.py`.

**Note:** For a complete example of a gazette configuration, you can take a look at the BOE `src/etls/boe`.

# Documents

If you want to load a single document into the embedding database.

...In progress...


# Want to develop your own module?

You are welcome! Please contact us to discuss your requirements:

* [Darío López](https://www.linkedin.com/in/dar%C3%ADo-l%C3%B3pez-padial-45269150/) 
* [Alex Dantart](https://www.linkedin.com/in/dantart/)
* [Jorge Iliarte](https://www.linkedin.com/in/jorge-iliarte-llop/)
* [Jorge Barrachina](https://www.linkedin.com/in/jorgebarrachina/)
