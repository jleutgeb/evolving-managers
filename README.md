new version of evolving managers using otree live

Tested with Python 3.9.16 and otree 5.10.3
Tested with postgresql database. 

CAVEATS

Nowadays, browsers by default limit the execution of javascript in windows that are not in focus. If you open ten tabs to test the code, the timeouts that are used for the periods will not work as they should. Instead of using whatever period length, they will default to a timeout of 1 second. Either disable the background timer throttling in Chrome or use the startup parameter --disable-background-timer-throttling in a shortcut when starting Chrome. 

Reset the database between sessions. If you accrue too many observations, oTree seems to struggle with downloading all the period data from the database. The data can still be accessed by dumping the database and using SQL queries, but it is very cumbersome to do so.
