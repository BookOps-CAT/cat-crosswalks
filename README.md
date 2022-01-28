# cat-crosswalks

Various crosswalks for NYPL & BPL data.

## Flourish score records


### Usage

1. Download Connexion database files (.bib.db) from designated folder in Flourish Google Drive
2. Serialize record in the database to MARC21 using MARCEdit
	1. Open MarcEdit (valid for version 7 & up)
	2. In the MarcEdit main menu go to Help>Restart MARCEdit in 32-bit Mode
	3. Install OCLC Connexion Bib File Reader plugin if not installed (Main Menu>Plug-ins>Plugin Manager> select OCLC Connexion Bib File Reader and click Download button)
	4. Open MarcEditor
	5. Select Plug-ins>OCLC Connexion Bib File Reader in the top bar menu
	6. Navigate to downloaded Connexion database file and load it.
	7. Select All and click to Edit Records
	8. Compile .mrk records into MARC21 (.mrc) format

3. Activate virtual environment

bash example:
```bash
$ source ./.venv/[script_virtual_env]/scripts/activate
```

4. Change the current directory to `cat-crosswalks`

bash example:
```bash
$ cd ~/[your_path_to_repos_directory]/cat-crosswalks
```

5. Manipulate provided by vendor files

bash example:
```bash
$ python src/flourish_bibs.py [path_to_src_marc_file]
```

6. Email processed file to database manager for import

