# cat-crosswalks

Various crosswalks for NYPL & BPL data.

## Flourish score records

Use this process to prep records provided by [Flourish Music Metadata Solutions](http://www.flourishmusic.net/index.php) for LPA scores.
Records provided by the vendor are in form of a Connexion database files, and need to be first converted into a MARC21 file using [MARCEdit software](https://marcedit.reeset.net/). Such file can be finally manipulated using `src/flourish_bibs.py` script.

The script does following operations on each record:
* adds 003  OCoLC
* adds 035  $a(OCoLC)[oclc #]
* removes any 911 tags
* adds 910  $aRL
* adds 949 tag with appropriate commands for Sierra import (sets bib code2, bib code3, default location, load table to use)
* adds item record (949 tag) with call number specified in 852$h field

The script does not provide a barcode, instead it populates item barcode field with a place holder phrase to be replaced by LPA staff. 

### Usage

1. Download Connexion database files (`.bib.db`) from designated folder in Flourish Google Drive
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

4. Change the current directory to `cat-crosswalks/`

bash example:
```bash
$ cd ~/[your_path_to_repos_directory]/cat-crosswalks
```

5. Manipulate provided by vendor records

bash example:
```bash
$ python ~/[path_to_repo_directory]/cat-crosswalks/src/flourish_bibs.py [path_to_src_marc_file]
```

The script outputs manipulated records into a file in the same directory where the source file resides. A newly created file has the same base name as the source file and has "-PRC" suffix added.

6. Email processed file to database manager for import

