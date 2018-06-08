# EVE Market History
Copyright (c) 2018 Po Huit

This is a silly little Python 3 script prototype that will
wake up every 24 hours, report the average price of market
indicators on the previous day to standard output, and then
go back to sleep.

For portability, this does not require any third-party
libraries: fetching is done with a custom request broker
that takes into account some of the CCP vagaries.

This program is licensed under the "MIT License".  Please
see the file LICENSE in the source distribution of this
software for license terms.
