# pyMemorise

No-frills tool to help memorise tables of data. Developed to aid
studying for exams where there is a need to recall lists of facts
presented in tables.

Tables of data can be configured into the application. Parts of these
tables will be presented back to the user for them to enter
corresponding data.

For example, consider the following list of facts:

| Vehicle  | Wheels | Passengers |
| -------- | ------:| ----------:|
| car      |      4 |          4 |
| van      |      4 |          2 |
| bike     |      2 |          1 |

The tool will enumerate through the possible values and prompt the
user to enter a corresponding value (or values). Thus, it could ask
simple questions such as:

* How many wheels a bike has? *2*
* What vehicle takes 4 passengers? *car*

Alternatively, in the case a value has multiple related values, it
could ask:

* What vehicle has 4 wheels? *car* and *van*
* How many passengers in a vehicle that has 4 wheels? *4* and *2*

The style of asking questions about related values aids building full
mental connections between values in the table. Whereas an alternative
of repeatedly writing out the table to memorise it does not result in
as useful mental map of the values (especially when trying to perform
reverse look ups in the head).

## Data storage

SQLite is used as the underlying database. All questions asked are
recorded into the database for further analysis/trends using external
tools.

## Installation

Requires `python3`, `pyuic5` available to compile the GUI and `PyQt5`
libraries: Core, GUI, Widgets, Sql.

```bash
make build
python3 setup.py install
```
